"""情绪加工管线 — Data-Core 数据加工层。

包含三个阶段：
1. SentimentRuleStage — 规则情绪基线（词典法，零成本模式）
2. SentimentLLMStage — LLM 情绪打分（高质量，需 LLM 依赖）
3. SentimentAggregator — 情绪聚合器（按品种/时间聚合）

降级链: LLM 打分 (P0) -> 规则基线 (P1) -> Cached (P2)
"""

from datacore.processing.sentiment.sentiment_rule import SentimentRuleStage
from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
from datacore.processing.sentiment.sentiment_aggregator import SentimentAggregator

__all__ = [
    "SentimentRuleStage",
    "SentimentLLMStage",
    "SentimentAggregator",
]
