"""市场制度检测 — 识别当前市场处于 bull/bear/sideways。

基于 OHLCV 数据，通过趋势强度、波动率、成交量等综合判断。
FTS 直接消费 MARKET_STATE 数据用于 regime-aware 因子计算。

检测逻辑:
1. 趋势强度: 基于 MA 斜率和价格相对 MA 的位置
2. 波动率: 基于 ATR 或标准差
3. 成交量趋势: 基于成交量 MA 斜率
4. 综合判断: 多维度加权打分
"""

from __future__ import annotations
import time
import math
from typing import Any, Optional

from datacore.processing.base import ProcessingStage
from datacore.processing.models import MarketStateData, MarketRegime


class MarketRegimeDetector(ProcessingStage):
    """市场制度检测 — 识别 bull/bear/sideways。

    输入: OHLCV 数据（list[dict] 或 DataFrame）
    输出: MarketStateData（含 regime, confidence, features）

    检测维度:
    - 趋势强度 (trend_strength): MA 斜率 + 价格/MA 偏离度
    - 波动率 (volatility): 收益率标准差
    - 成交量趋势 (volume_trend): 成交量 MA 斜率
    """

    input_type = "OHLCV"
    output_type = "MARKET_STATE"
    name = "market_regime"
    priority = 0

    def __init__(self, ma_period: int = 20, atr_period: int = 14,
                 bull_threshold: float = 0.6, bear_threshold: float = -0.6):
        """
        Args:
            ma_period: 均线周期
            atr_period: ATR 计算周期
            bull_threshold: 牛市判断阈值（综合分数 > 此值）
            bear_threshold: 熊市判断阈值（综合分数 < 此值）
        """
        self.ma_period = ma_period
        self.atr_period = atr_period
        self.bull_threshold = bull_threshold
        self.bear_threshold = bear_threshold

    def check_available(self) -> bool:
        """市场制度检测始终可用（纯计算，无外部依赖）。"""
        return True

    def process(self, input_data: Any, symbol: Optional[str] = None,
                params: Optional[dict] = None) -> MarketStateData:
        """检测市场制度。

        Args:
            input_data: OHLCV 数据，list[dict] 格式
                       [{"date": ..., "open": ..., "high": ..., "low": ...,
                         "close": ..., "volume": ...}, ...]
            symbol: 品种代码
            params: 可选参数

        Returns:
            MarketStateData: 市场制度状态
        """
        params = params or {}

        # 提取 OHLCV 数据
        candles = self._extract_candles(input_data)
        if len(candles) < self.ma_period:
            return MarketStateData(
                symbol=symbol or "",
                regime=MarketRegime.UNKNOWN,
                confidence=0.0,
                features={"reason": "insufficient_data", "count": len(candles)},
                collected_at=time.time(),
            )

        # 计算特征
        trend_strength = self._calc_trend_strength(candles)
        volatility = self._calc_volatility(candles)
        volume_trend = self._calc_volume_trend(candles)

        # 综合判断
        composite_score = self._composite_score(
            trend_strength, volatility, volume_trend
        )

        # 判断 regime
        if composite_score > self.bull_threshold:
            regime = MarketRegime.BULL
        elif composite_score < self.bear_threshold:
            regime = MarketRegime.BEAR
        else:
            regime = MarketRegime.SIDEWAYS

        # 置信度：基于综合分数的绝对值
        confidence = min(1.0, abs(composite_score) * 1.2)

        return MarketStateData(
            symbol=symbol or "",
            regime=regime,
            confidence=round(confidence, 4),
            trend_strength=round(trend_strength, 4),
            volatility=round(volatility, 4),
            volume_trend=round(volume_trend, 4),
            features={
                "composite_score": round(composite_score, 4),
                "ma_period": self.ma_period,
                "candle_count": len(candles),
            },
            collected_at=time.time(),
        )

    def _extract_candles(self, input_data: Any) -> list[dict]:
        """从输入数据提取 OHLCV 列表。"""
        if isinstance(input_data, list):
            return input_data
        if hasattr(input_data, "to_dict"):
            # DataFrame
            return input_data.to_dict("records")
        if hasattr(input_data, "items"):
            # list[dict] 或 dict
            return list(input_data)
        return []

    def _calc_trend_strength(self, candles: list[dict]) -> float:
        """计算趋势强度。

        基于:
        - MA 斜率（正=上升趋势）
        - 价格相对 MA 的位置

        Returns:
            趋势强度 (-1.0 ~ +1.0)
        """
        closes = [float(c.get("close", 0)) for c in candles]
        if len(closes) < self.ma_period:
            return 0.0

        # 计算 MA
        ma_values = self._calc_ma(closes, self.ma_period)
        if len(ma_values) < 3:
            return 0.0

        # MA 斜率（归一化）
        current_ma = ma_values[-1]
        prev_ma = ma_values[-3]
        if current_ma == 0:
            return 0.0
        ma_slope = (current_ma - prev_ma) / (prev_ma * 3) if prev_ma != 0 else 0.0

        # 价格相对 MA 的位置
        current_price = closes[-1]
        price_deviation = (current_price - current_ma) / current_ma if current_ma != 0 else 0.0

        # 综合趋势强度
        trend = ma_slope * 50 + price_deviation * 20
        return max(-1.0, min(1.0, trend))

    def _calc_volatility(self, candles: list[dict]) -> float:
        """计算波动率（收益率标准差，年化）。

        Returns:
            波动率 (0.0 ~ 1.0+)
        """
        closes = [float(c.get("close", 0)) for c in candles]
        if len(closes) < 2:
            return 0.0

        # 计算日收益率
        returns = []
        for i in range(1, len(closes)):
            if closes[i - 1] != 0:
                returns.append((closes[i] - closes[i - 1]) / closes[i - 1])

        if len(returns) < 2:
            return 0.0

        # 标准差
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        std = math.sqrt(variance)

        # 年化波动率
        annualized = std * math.sqrt(252)
        return min(1.0, annualized)

    def _calc_volume_trend(self, candles: list[dict]) -> float:
        """计算成交量趋势。

        Returns:
            成交量趋势 (-1.0 ~ +1.0)，正=放量，负=缩量
        """
        volumes = [float(c.get("volume", 0)) for c in candles]
        if len(volumes) < self.ma_period:
            return 0.0

        # 计算成交量 MA
        vol_ma = self._calc_ma(volumes, self.ma_period)
        if len(vol_ma) < 2 or vol_ma[-2] == 0:
            return 0.0

        # 成交量 MA 斜率
        vol_slope = (vol_ma[-1] - vol_ma[-2]) / vol_ma[-2]
        return max(-1.0, min(1.0, vol_slope * 10))

    def _composite_score(self, trend_strength: float, volatility: float,
                         volume_trend: float) -> float:
        """综合打分，判断 regime。

        Returns:
            综合分数 (-1.0 ~ +1.0)
        """
        # 趋势权重最高
        score = (
            trend_strength * 0.6
            + volume_trend * 0.2
            # 高波动率在无趋势时倾向于 sideways
            - (1.0 - abs(trend_strength)) * volatility * 0.2
        )
        return max(-1.0, min(1.0, score))

    def _calc_ma(self, values: list[float], period: int) -> list[float]:
        """计算移动平均。"""
        if len(values) < period:
            return []
        ma = []
        for i in range(period - 1, len(values)):
            window = values[i - period + 1: i + 1]
            ma.append(sum(window) / period)
        return ma
