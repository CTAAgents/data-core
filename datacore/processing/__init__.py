"""Data-Core 数据加工层 — 从原始数据到可消费结构化数据的转换。

v0.3.0 新增模块，包含：
- 情绪加工管线（LLM 打分 + 规则基线 + 聚合）
- 市场制度检测（market_regime）
- 基本面 LLM 加工（远期规划）

核心原则: LLM 是数据加工的工具之一，与规则引擎、统计方法地位相同。
FTS 的职责是因子演化与策略生成，直接消费已加工好的 SENTIMENT/MARKET_STATE 数据。
"""

from datacore.processing.base import ProcessingStage
from datacore.processing.models import (
    SentimentItem,
    SentimentData,
    MarketStateData,
    MarketRegime,
)

__all__ = [
    "ProcessingStage",
    "SentimentItem",
    "SentimentData",
    "MarketStateData",
    "MarketRegime",
]
