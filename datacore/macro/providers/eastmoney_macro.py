"""东方财富宏观数据源 — 宏观数据 P1。"""

from __future__ import annotations
from typing import Optional
import httpx
from datacore.macro.providers.base import MacroDataSource
from datacore.macro.models import MacroData, MacroIndicator


MACRO_INDICATOR_MAP = {
    "pmi": "PMI",
    "cpi": "CPI",
    "ppi": "PPI",
    "gdp": "GDP",
    "m2": "M2",
    "lpr": "LPR",
}


class EastMoneyMacroProvider(MacroDataSource):
    """东方财富宏观数据。"""
    name = "eastmoney_macro"
    priority = 1

    def fetch_macro(self, indicator: Optional[str] = None,
                    limit: int = 50) -> Optional[MacroData]:
        """从东方财富获取宏观数据。"""
        try:
            ind_key = (indicator or "pmi").lower()
            if ind_key not in MACRO_INDICATOR_MAP:
                ind_key = "pmi"
            with httpx.Client(timeout=10) as c:
                resp = c.get(
                    "https://datacenter-web.eastmoney.com/api/data/v1/get",
                    params={
                        "sortColumns": "REPORT_DATE",
                        "sortTypes": "-1",
                        "pageSize": limit,
                        "pageNumber": 1,
                        "reportName": "RPT_ECONOMIC_INDEX",
                        "columns": "ALL",
                        "filter": f'(INDICATOR_NAME="{MACRO_INDICATOR_MAP[ind_key]}")',
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": "https://data.eastmoney.com/",
                    },
                )
                result = resp.json().get("result", {})
                data_list = result.get("data", []) if result else []
        except Exception:
            return None
        if not data_list:
            return None
        indicators = []
        for item in data_list:
            try:
                indicators.append(MacroIndicator(
                    indicator=ind_key,
                    period=str(item.get("REPORT_DATE", "") or ""),
                    value=float(item.get("VALUE", 0) or 0),
                    prev_value=float(item.get("PREV_VALUE", 0) or 0),
                    yoy=float(item.get("YOY", 0) or 0),
                    mom=float(item.get("MOM", 0) or 0),
                    source="eastmoney",
                    unit=str(item.get("UNIT", "") or ""),
                ))
            except (TypeError, ValueError):
                continue
        if not indicators:
            return None
        return MacroData(indicator=ind_key, total=len(indicators), data=indicators)

    def check_available(self) -> bool:
        try:
            with httpx.Client(timeout=5) as c:
                r = c.head("https://datacenter-web.eastmoney.com")
                return r.status_code < 500
        except Exception:
            return False
