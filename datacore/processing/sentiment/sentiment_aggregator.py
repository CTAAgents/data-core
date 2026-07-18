"""情绪聚合器 — 按品种/时间维度聚合情绪分数。

输入: list[SentimentItem]
输出: SentimentData（含按日聚合结果和整体摘要）

聚合策略:
- 时间衰减加权（近期新闻权重更高）
- 置信度加权（高置信度新闻权重更高）
- 按日期分组聚合
"""

from __future__ import annotations
import time
import math
from datetime import datetime
from typing import Optional

from datacore.processing.models import SentimentItem, SentimentData


class SentimentAggregator:
    """情绪聚合器 — 按品种/时间维度聚合情绪分数。

    输入: list[SentimentItem]
    输出: SentimentData（symbol → {date → {score, volume, topics}}）
    """

    def __init__(self, decay_half_life_days: float = 7.0,
                 min_confidence: float = 0.1):
        """
        Args:
            decay_half_life_days: 时间衰减半衰期（天），7天表示7天前的新闻权重减半
            min_confidence: 低于此置信度的新闻将被过滤
        """
        self.decay_half_life_days = decay_half_life_days
        self.min_confidence = min_confidence

    def aggregate(self, items: list[SentimentItem],
                  symbol: Optional[str] = None,
                  params: Optional[dict] = None) -> SentimentData:
        """聚合情绪数据。

        Args:
            items: 情绪打分结果列表
            symbol: 品种代码
            params: {"days": 30} 等参数

        Returns:
            SentimentData: 聚合后的情绪数据
        """
        params = params or {}
        days = params.get("days", 30)
        now = time.time()
        cutoff = now - days * 86400

        # 过滤低置信度和过期数据
        filtered = [
            item for item in items
            if item.confidence >= self.min_confidence
            and (item.published_at == 0.0 or item.published_at >= cutoff)
        ]

        result = SentimentData(symbol=symbol or "")

        # 按日期分组
        daily_items: dict[str, list[SentimentItem]] = {}
        all_topics: set[str] = set()

        for item in filtered:
            result.add_item(item)
            # 提取日期
            date_str = self._get_date_str(item.published_at)
            if date_str not in daily_items:
                daily_items[date_str] = []
            daily_items[date_str].append(item)
            # 收集主题
            if item.tags:
                all_topics.update(item.tags)

        # 按日聚合
        for date_str, day_items in daily_items.items():
            weighted_score = 0.0
            total_weight = 0.0
            day_topics: set[str] = set()

            for item in day_items:
                # 时间衰减权重
                time_weight = self._time_decay_weight(item.published_at, now)
                # 置信度权重
                conf_weight = item.confidence
                # 综合权重
                weight = time_weight * conf_weight

                weighted_score += item.score * weight
                total_weight += weight
                if item.tags:
                    day_topics.update(item.tags)

            avg_score = weighted_score / total_weight if total_weight > 0 else 0.0
            result.daily[date_str] = {
                "score": round(avg_score, 4),
                "volume": len(day_items),
                "topics": list(day_topics),
            }

        # 整体情绪摘要
        if filtered:
            total_weight = 0.0
            weighted_score = 0.0
            for item in filtered:
                time_weight = self._time_decay_weight(item.published_at, now)
                conf_weight = item.confidence
                weight = time_weight * conf_weight
                weighted_score += item.score * weight
                total_weight += weight
            result.overall_score = round(
                weighted_score / total_weight if total_weight > 0 else 0.0, 4
            )

        result.topics = list(all_topics)
        return result

    def _time_decay_weight(self, timestamp: float, now: float) -> float:
        """计算时间衰减权重。

        使用指数衰减: w = 0.5^(age / half_life)
        """
        if timestamp == 0.0:
            return 0.5  # 未知时间的新闻给中等权重
        age_days = (now - timestamp) / 86400.0
        age_days = max(age_days, 0)
        return math.pow(0.5, age_days / self.decay_half_life_days)

    def _get_date_str(self, timestamp: float) -> str:
        """从时间戳提取日期字符串。"""
        if timestamp == 0.0:
            return "unknown"
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, OSError):
            return "unknown"
