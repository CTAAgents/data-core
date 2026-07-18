"""宏观数据模型。"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MacroIndicator:
    """宏观指标数据点。"""
    indicator: str
    period: str
    value: float
    prev_value: float = 0.0
    yoy: float = 0.0
    mom: float = 0.0
    source: str = ""
    unit: str = ""


@dataclass
class MacroData:
    """宏观数据集。"""
    indicator: str = ""
    total: int = 0
    data: list[MacroIndicator] = field(default_factory=list)

    def latest(self) -> Optional[MacroIndicator]:
        """获取最新一期数据。"""
        return self.data[0] if self.data else None
