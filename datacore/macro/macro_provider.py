"""宏观数据提供者 — 多源降级链。

P0: 国家统计局/央行（官方）
P1: 东方财富（汇总）
P2: Cached（缓存数据）
"""

from __future__ import annotations
import time
from typing import Optional
from datacore.models.enums import DataType, MarketType, SourceGrade
from datacore.models.payload import DataPayload
from datacore.macro.models import MacroData


class MacroDataProvider:
    """宏观数据提供者 — 多源降级链。"""

    def __init__(self):
        self.sources = []
        self._init_sources()

    def _init_sources(self):
        """懒加载数据源（优先级: 统计局 → 央行 → 东方财富）。"""
        try:
            from datacore.macro.providers.national_bureau import NationalBureauProvider
            self.sources.append(NationalBureauProvider())
        except Exception:
            pass
        try:
            from datacore.macro.providers.pboc import PboCProvider
            self.sources.append(PboCProvider())
        except Exception:
            pass
        try:
            from datacore.macro.providers.eastmoney_macro import EastMoneyMacroProvider
            self.sources.append(EastMoneyMacroProvider())
        except Exception:
            pass

    def get(self, indicator: Optional[str] = None,
            params: dict | None = None) -> DataPayload:
        """获取宏观数据。

        Args:
            indicator: "pmi", "lpr", "cpi", "ppi", "gdp", "m2", None(全部)
            params: {"limit": 50}
        """
        params = params or {}
        limit = int(params.get("limit", 50))

        for src in self.sources:
            if not hasattr(src, "check_available") or not src.check_available():
                continue
            try:
                macro_data = src.fetch_macro(indicator=indicator, limit=limit)
                if macro_data and macro_data.data:
                    grade = SourceGrade.DAILY if src.priority == 0 else SourceGrade.CACHED
                    if src.priority == 0:
                        grade = SourceGrade.PRIMARY
                    return DataPayload(
                        symbol=indicator or "*",
                        data_type=DataType.MACRO,
                        market=MarketType.FUTURES,
                        data=macro_data,
                        source=src.name,
                        grade=grade,
                        collected_at=time.time(),
                    )
            except Exception:
                continue

        return DataPayload(
            symbol=indicator or "*",
            data_type=DataType.MACRO,
            market=MarketType.FUTURES,
            data=MacroData(indicator=indicator or ""),
            grade=SourceGrade.UNAVAILABLE,
            errors=["所有宏观数据源不可用"],
            collected_at=time.time(),
        )
