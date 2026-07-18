"""国信证券数据源 — A 股 P2 回退源。

配置方式:
  - 环境变量: DATACORE_SOURCES_GUOSEN_API_KEY
  - YAML: sources.guosen.api_key

数据范围: A 股 K 线/行情/财务数据
"""
from __future__ import annotations
from typing import Optional
import httpx
from datacore.equity.providers.base import EquityDataSource
from datacore.models.enums import DataType
from datacore.models.payload import DataPayload
from datacore.config import get_config


class GuosenProvider(EquityDataSource):
    """国信证券数据源。"""
    name = "guosen"
    priority = 2  # P2: 腾讯(P0) → 东方财富(P1) → 国信(P2)
    supported_types = {
        DataType.OHLCV,
        DataType.QUOTE,
        DataType.FINANCIAL,
    }

    def __init__(self):
        config = get_config()
        self.api_key = config.guosen_api_key
        self.base_url = config.guosen_url
        self.timeout = config.guosen_timeout

    def check_available(self) -> bool:
        """检查 API Key 是否已配置以及 API 是否可达。"""
        if not self.api_key:
            return False
        try:
            with httpx.Client(timeout=5) as c:
                r = c.get(
                    f"{self.base_url}/api/v1/ping",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return r.status_code < 500
        except Exception:
            return False

    def fetch(self, symbol: str, data_type: DataType,
              params: dict | None = None) -> Optional[DataPayload]:
        """获取 A 股数据。"""
        if data_type == DataType.OHLCV:
            return self._fetch_kline(symbol, params)
        if data_type == DataType.QUOTE:
            return self._fetch_quote(symbol, params)
        if data_type == DataType.FINANCIAL:
            return self._fetch_financial(symbol)
        return None

    def _fetch_kline(self, symbol: str, params: dict | None = None) -> Optional[DataPayload]:
        """获取 K 线数据。"""
        if not self.api_key:
            return None
        period = (params or {}).get("period", "daily")
        days = int((params or {}).get("days", 120))
        try:
            with httpx.Client(timeout=self.timeout) as c:
                resp = c.get(
                    f"{self.base_url}/api/v1/stock/kline",
                    params={
                        "symbol": symbol,
                        "period": period,
                        "days": days,
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                data = resp.json()
            if not data or not data.get("success"):
                return None
            from datacore.models.ohlcv import KlineData, KBar
            bars = []
            for item in data.get("data", []):
                bars.append(KBar(
                    date=item.get("date", ""),
                    open=float(item.get("open", 0)),
                    high=float(item.get("high", 0)),
                    low=float(item.get("low", 0)),
                    close=float(item.get("close", 0)),
                    volume=float(item.get("volume", 0)),
                    amount=float(item.get("amount", 0)),
                ))
            if not bars:
                return None
            from datacore.models.enums import SourceGrade
            kline = KlineData(symbol=symbol, period=period, bars=bars, source=self.name)
            return DataPayload(
                symbol=symbol, data_type=DataType.OHLCV,
                market=None, data=kline,
                source=self.name, grade=SourceGrade.DAILY,
            )
        except Exception:
            return None

    def _fetch_quote(self, symbol: str, params: dict | None = None) -> Optional[DataPayload]:
        """获取实时行情。"""
        if not self.api_key:
            return None
        try:
            with httpx.Client(timeout=self.timeout) as c:
                resp = c.get(
                    f"{self.base_url}/api/v1/stock/quote",
                    params={"symbol": symbol},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                data = resp.json()
            if not data or not data.get("success"):
                return None
            from datacore.models.ohlcv import QuoteData
            from datacore.models.enums import SourceGrade
            item = data.get("data", {})
            quote = QuoteData(
                symbol=symbol,
                source=self.name,
                last_price=float(item.get("last_price", 0) or 0),
                open=float(item.get("open", 0) or 0),
                high=float(item.get("high", 0) or 0),
                low=float(item.get("low", 0) or 0),
                volume=float(item.get("volume", 0) or 0),
                amount=float(item.get("amount", 0) or 0),
            )
            return DataPayload(
                symbol=symbol, data_type=DataType.QUOTE,
                market=None, data=quote,
                source=self.name, grade=SourceGrade.DAILY,
            )
        except Exception:
            return None

    def _fetch_financial(self, symbol: str) -> Optional[DataPayload]:
        """获取财务数据。"""
        if not self.api_key:
            return None
        try:
            with httpx.Client(timeout=self.timeout) as c:
                resp = c.get(
                    f"{self.base_url}/api/v1/stock/financial",
                    params={"symbol": symbol},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                data = resp.json()
            if not data or not data.get("success"):
                return None
            from datacore.models.enums import SourceGrade
            return DataPayload(
                symbol=symbol, data_type=DataType.FINANCIAL,
                market=None, data=data.get("data", {}),
                source=self.name, grade=SourceGrade.DAILY,
            )
        except Exception:
            return None
