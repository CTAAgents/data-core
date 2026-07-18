"""数据加工层数据模型。

定义情绪数据和市场制度数据的标准结构，
供 FTS 直接消费。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MarketRegime(str, Enum):
    """市场制度类型。"""
    BULL = "bull"           # 牛市：上升趋势
    BEAR = "bear"           # 熊市：下降趋势
    SIDEWAYS = "sideways"   # 震荡：无明显趋势
    UNKNOWN = "unknown"     # 未知/数据不足


@dataclass
class SentimentItem:
    """单条新闻/公告的情绪打分结果。

    由 SentimentLLMStage 或 SentimentRuleStage 产出。
    """

    text: str = ""                              # 原始文本（标题+摘要）
    score: float = 0.0                          # 情绪分数 (-1.0 ~ +1.0)
    confidence: float = 0.0                     # 置信度 (0.0 ~ 1.0)
    source: str = ""                            # 打分来源 ("llm" / "rule")
    symbol: str = ""                            # 关联品种
    tags: list[str] = field(default_factory=list)  # 新闻分类标签
    published_at: float = 0.0                   # 发布时间戳
    collected_at: float = 0.0                   # 打分时间戳


@dataclass
class SentimentData:
    """品种情绪聚合数据。

    由 SentimentAggregator 产出，按品种+时间维度聚合。
    FTS 直接消费此结构。
    """

    symbol: str = ""
    items: list[SentimentItem] = field(default_factory=list)
    # 按日期聚合的结果: {date_str: {score, volume, topics}}
    daily: dict[str, dict] = field(default_factory=dict)
    # 整体情绪摘要
    overall_score: float = 0.0                  # 加权平均情绪分数
    total_volume: int = 0                       # 新闻总条数
    topics: list[str] = field(default_factory=list)  # 涉及的主题

    def add_item(self, item: SentimentItem) -> None:
        """添加单条情绪数据。"""
        self.items.append(item)
        self.total_volume += 1


@dataclass
class MarketStateData:
    """市场制度状态数据。

    由 MarketRegimeDetector 产出。
    FTS 直接消费此结构用于 regime-aware 因子计算。
    """

    symbol: str = ""
    regime: MarketRegime = MarketRegime.UNKNOWN
    confidence: float = 0.0                      # 置信度 (0.0 ~ 1.0)
    # 特征数据
    trend_strength: float = 0.0                  # 趋势强度
    volatility: float = 0.0                      # 波动率
    volume_trend: float = 0.0                    # 成交量趋势
    # 原始特征字典（用于扩展）
    features: dict = field(default_factory=dict)
    collected_at: float = 0.0

    @property
    def is_bull(self) -> bool:
        return self.regime == MarketRegime.BULL

    @property
    def is_bear(self) -> bool:
        return self.regime == MarketRegime.BEAR

    @property
    def is_sideways(self) -> bool:
        return self.regime == MarketRegime.SIDEWAYS
