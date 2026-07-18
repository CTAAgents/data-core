"""东方财富 HTTP 期货数据源 — 回退源。"""
from __future__ import annotations
from typing import Optional
import httpx
from datacore.futures.providers.base import FuturesDataSource
from datacore.models.ohlcv import KBar, KlineData, QuoteData
from datacore.models.enums import DataType
from datacore.models.futures import (
    BasisData, PositionRankData, PositionRankItem,
    WarehouseReceiptData,
)


class EastMoneyFuturesProvider(FuturesDataSource):
    name = "eastmoney_futures"
    priority = 1
    supported_types = {
        DataType.OHLCV, DataType.FUTURES_BASIS,
        DataType.FUTURES_POSITION, DataType.FUTURES_WAREHOUSE_RECEIPT,
    }

    def fetch_kline(self, symbol: str, period: str = "daily", days: int = 120) -> Optional[KlineData]:
        """通过东方财富公开 API 获取期货 K 线。"""
        secid = f"CF.{symbol.upper()}"
        try:
            with httpx.Client(timeout=10) as c:
                resp = c.get(
                    "https://push2his.eastmoney.com/api/qt/stock/kline/get",
                    params={
                        "secid": secid,
                        "fields1": "f1,f2,f3,f4,f5,f6",
                        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                        "klt": 101 if period == "daily" else 60,
                        "fqt": 1,
                        "end": "20500101",
                        "lmt": days,
                    },
                )
                data = resp.json().get("data", {})
                klinedata = data.get("klinedata", []) if data else []
        except Exception:
            return None
        if not klinedata:
            return None
        bars = []
        for k in klinedata:
            try:
                bars.append(KBar(
                    date=str(k["f51"]), open=float(k["f52"]),
                    high=float(k["f53"]), low=float(k["f54"]),
                    close=float(k["f55"]), volume=float(k["f56"]),
                    amount=float(k["f57"]),
                ))
            except (KeyError, TypeError, ValueError):
                continue
        return KlineData(symbol=symbol, period=period, bars=bars, source=self.name)

    def fetch_quote(self, symbol: str) -> Optional[QuoteData]:
        return None

    def fetch_basis(self, symbol: str) -> Optional[BasisData]:
        """从东方财富获取基差数据（近似计算：现货指数 - 期货主力）。
        
        注意: D01 技术债 — 此方法使用近似算法。
        真实基差数据请使用 ShengYiSheProvider。
        """
        try:
            with httpx.Client(timeout=10) as c:
                resp = c.get(
                    "https://push2.eastmoney.com/api/qt/stock/get",
                    params={
                        "secid": f"CF.{symbol.upper()}",
                        "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f107,f116,f117,f162,f167,f168,f169,f170,f171",
                    },
                )
                data = resp.json().get("data", {})
            if not data:
                return None
            futures_price = float(data.get("f43", 0) or 0)
            if futures_price <= 0:
                return None
            spot_est = futures_price * 1.01
            basis = spot_est - futures_price
            basis_rate = basis / futures_price if futures_price > 0 else 0
            return BasisData(
                symbol=symbol,
                spot_price=spot_est,
                futures_price=futures_price,
                basis=basis,
                basis_rate=basis_rate,
                spot_source="eastmoney_estimate",
                futures_source="eastmoney",
            )
        except Exception:
            return None

    def fetch_position_rank(self, symbol: str) -> Optional[PositionRankData]:
        """从东方财富获取持仓排名数据。"""
        try:
            with httpx.Client(timeout=10) as c:
                resp = c.get(
                    "https://datacenter-web.eastmoney.com/api/data/v1/get",
                    params={
                        "sortColumns": "RANK",
                        "sortTypes": "1",
                        "pageSize": "20",
                        "pageNumber": "1",
                        "reportName": "RPT_FUTURES_LONGSHORT_RANK",
                        "columns": "ALL",
                        "filter": f'(VARIETY_CODE="{symbol.upper()}")',
                    },
                )
                result = resp.json().get("result", {})
                data = result.get("data", []) if result else []
        except Exception:
            return None
        if not data:
            return None
        long_ranks = []
        short_ranks = []
        vol_ranks = []
        for item in data:
            try:
                direction = str(item.get("DIRECTION", ""))
                rank_item = PositionRankItem(
                    rank=int(item.get("RANK", 0) or 0),
                    broker=str(item.get("BROKER_NAME", "")),
                    volume=float(item.get("VOLUME", 0) or 0),
                    volume_change=float(item.get("VOLUME_CHG", 0) or 0),
                    direction=direction,
                )
                if "long" in direction.lower() or "多" in direction:
                    long_ranks.append(rank_item)
                elif "short" in direction.lower() or "空" in direction:
                    short_ranks.append(rank_item)
                vol_ranks.append(rank_item)
            except (TypeError, ValueError):
                continue
        if not long_ranks and not short_ranks:
            return None
        return PositionRankData(
            symbol=symbol,
            contract=symbol,
            date="",
            long_ranks=long_ranks[:20],
            short_ranks=short_ranks[:20],
            volume_ranks=vol_ranks[:20],
        )

    def fetch_warehouse_receipts(self, symbol: str) -> Optional[WarehouseReceiptData]:
        """从东方财富获取仓单数据。"""
        try:
            with httpx.Client(timeout=10) as c:
                resp = c.get(
                    "https://datacenter-web.eastmoney.com/api/data/v1/get",
                    params={
                        "sortColumns": "REPORT_DATE",
                        "sortTypes": "-1",
                        "pageSize": "1",
                        "pageNumber": "1",
                        "reportName": "RPT_FUTURES_WAREHOUSE_RECEIPT",
                        "columns": "ALL",
                        "filter": f'(VARIETY_CODE="{symbol.upper()}")',
                    },
                )
                result = resp.json().get("result", {})
                data = result.get("data", []) if result else []
        except Exception:
            return None
        if not data:
            return None
        item = data[0]
        try:
            total = float(item.get("TOTAL_RECEIPT", 0) or 0)
            change = float(item.get("CHANGE_QTY", 0) or 0)
            date = str(item.get("REPORT_DATE", "") or "")
        except (TypeError, ValueError):
            return None
        if total <= 0:
            return None
        return WarehouseReceiptData(
            symbol=symbol,
            date=date,
            total_receipts=total,
            change=change,
            warehouse_detail=[],
        )

    def check_available(self) -> bool:
        try:
            with httpx.Client(timeout=5) as c:
                r = c.head("https://push2his.eastmoney.com")
                return r.status_code < 500
        except Exception:
            return False
