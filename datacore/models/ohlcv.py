"""OHLCV K 线数据结构。

与 FDT futures_data_core.core.types 严格对齐字段名与默认值。
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KBar:
    """单根 K 线 — 对齐 FDT KlineBar。"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    amount: float = 0.0
    open_interest: float = 0.0
    settlement: float = 0.0


@dataclass
class KlineData:
    """K 线数据集"""
    symbol: str
    period: str
    bars: list[KBar] = field(default_factory=list)
    source: str = ""
    contract: str = ""


@dataclass
class QuoteData:
    """实时行情快照 — 对齐 FDT QuoteData（含 to_dict / collected_at）。"""
    symbol: str
    source: str = ""
    last_price: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    pre_close: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None
    bid_price: list[float] = field(default_factory=list)
    ask_price: list[float] = field(default_factory=list)
    change_pct: Optional[float] = None
    update_time: Optional[str] = None
    collected_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """序列化为 JSON 友好的 dict — 与 FDT QuoteData.to_dict() 格式一致。"""
        return {
            "symbol": self.symbol,
            "source": self.source,
            "last_price": self.last_price,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "pre_close": self.pre_close,
            "volume": self.volume,
            "collected_at": self.collected_at,
        }
