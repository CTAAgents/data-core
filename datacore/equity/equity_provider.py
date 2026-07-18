"""A 股数据统一入口。"""
from __future__ import annotations
import time
from typing import Optional
from datacore.models.enums import DataType, MarketType, SourceGrade
from datacore.models.payload import DataPayload
from datacore.equity.providers import TencentProvider, EastMoneyEquityProvider, GuosenProvider


class EquityDataProvider:
    """A 股数据提供者 — 多源降级链: 腾讯 → 东方财富 → 国信。"""

    def __init__(self):
        self.sources = [TencentProvider(), EastMoneyEquityProvider(), GuosenProvider()]

    def get(self, symbol: str, data_type: DataType,
            params: dict | None = None,
            market: MarketType = MarketType.STOCK) -> Optional[DataPayload]:
        for src in self.sources:
            if not src.check_available():
                continue
            if data_type not in src.supported_types:
                continue
            try:
                payload = src.fetch(symbol, data_type, params)
                if payload and payload.available:
                    payload.market = market
                    return payload
            except Exception:
                continue
        return DataPayload(
            symbol=symbol, data_type=data_type,
            market=market,
            grade=SourceGrade.UNAVAILABLE,
            errors=["所有 A 股源不可用"], collected_at=time.time(),
        )

    def _get_etf(self, symbol: str, data_type: DataType,
                 params: dict | None = None) -> Optional[DataPayload]:
        """获取 ETF 数据。"""
        for src in self.sources:
            if not src.check_available() or data_type not in src.supported_types:
                continue
            try:
                payload = src.fetch(symbol, data_type, params)
                if payload and payload.available:
                    return payload
            except Exception:
                continue
        return None
