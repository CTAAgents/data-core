"""基本面加工数据模型。"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReportSummary:
    """研报结构化摘要。"""
    title: str = ""
    symbol: str = ""
    direction: str = ""           # "看多" / "看空" / "中性"
    strength: str = ""            # "强烈" / "一般" / "谨慎"
    time_horizon: str = ""        # "短期" / "中期" / "长期"
    key_points: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    source: str = ""
    published_at: str = ""


@dataclass
class EarningSummary:
    """财报关键信息摘要。"""
    symbol: str = ""
    period: str = ""
    revenue: Optional[float] = None
    revenue_yoy: Optional[float] = None
    revenue_qoq: Optional[float] = None
    profit: Optional[float] = None
    profit_yoy: Optional[float] = None
    profit_qoq: Optional[float] = None
    roe: Optional[float] = None
    cash_flow: Optional[float] = None
    source: str = ""
    summary: str = ""


@dataclass
class FundamentalSummary:
    """综合基本面摘要。

    由研报摘要和财报摘要整合而成。
    """
    symbol: str = ""
    reports: list[ReportSummary] = field(default_factory=list)
    earnings: list[EarningSummary] = field(default_factory=list)
    composite_score: float = 0.0         # -1.0 ~ +1.0
    confidence: float = 0.0               # 0.0 ~ 1.0
    source: str = "llm"
    collected_at: float = 0.0
