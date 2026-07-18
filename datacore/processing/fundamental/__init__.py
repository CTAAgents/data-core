"""基本面 LLM 加工模块 — Data-Core 数据加工层。

将研报/财报等基本面数据通过 LLM 加工为结构化摘要。

模块结构:
- FundamentalLLMStage — 研报结构化摘要
- EarningLLMStage — 财报关键信息抽取
- models.py — FundamentalSummary 数据模型
"""
from .models import FundamentalSummary, EarningSummary, ReportSummary

__all__ = [
    "FundamentalSummary",
    "EarningSummary",
    "ReportSummary",
]
