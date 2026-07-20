"""Pydantic schemas for DataCore tools.

Pydantic is an optional dependency. If not installed, all schema classes
will be None and tools will fall back to natural-language descriptions.
"""

from __future__ import annotations

from typing import Any, Optional

try:
    from pydantic import BaseModel, Field

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = None  # type: ignore
    Field = None  # type: ignore


# ============================================================
#  Data retrieval tools
# ============================================================

if HAS_PYDANTIC:

    class OHLCVSchema(BaseModel):
        """Schema for DataCoreOHLCVTool."""

        symbol: str = Field(..., description="品种代码，如 'RB'、'000001'")
        period: str = Field("daily", description="K线周期，可选值: 1m, 5m, 15m, 30m, 60m, daily, weekly, monthly")
        limit: int = Field(100, description="返回数据条数")
        start_date: Optional[str] = Field(None, description="开始日期，格式 'YYYY-MM-DD'")
        end_date: Optional[str] = Field(None, description="结束日期，格式 'YYYY-MM-DD'")
        adjust: str = Field("none", description="复权方式，'none'/'forward'/'backward'")

    class QuoteSchema(BaseModel):
        """Schema for DataCoreQuoteTool."""

        symbol: str = Field(..., description="品种代码，如 'RB'、'000001'")
        fields: Optional[list[str]] = Field(None, description="指定返回字段，默认返回全部字段")

    class SentimentSchema(BaseModel):
        """Schema for DataCoreSentimentTool."""

        symbol: str = Field(..., description="品种代码")

    class HealthSchema(BaseModel):
        """Schema for DataCoreHealthTool."""

        pass

    class ListSymbolsSchema(BaseModel):
        """Schema for DataCoreListSymbolsTool."""

        market: Optional[str] = Field(None, description="市场类型，'futures'/'stock'/'etf'/'cb'/'reit'，默认返回全部")

    class MacroSchema(BaseModel):
        """Schema for DataCoreMacroTool."""

        indicator: Optional[str] = Field(None, description="指标名称，如 'GDP'、'CPI'、'PPI' 等")

    class FundamentalSchema(BaseModel):
        """Schema for DataCoreFundamentalTool."""

        symbol: str = Field(..., description="品种代码")

    class F10Schema(BaseModel):
        """Schema for DataCoreF10Tool."""

        symbol: str = Field(..., description="品种代码")

    class IndicatorsSchema(BaseModel):
        """Schema for DataCoreIndicatorsTool."""

        symbol: str = Field(..., description="品种代码")
        indicators: list[str] = Field(..., description="要计算的指标名称列表，如 ['MA', 'RSI', 'MACD']")
        period: str = Field("daily", description="K线周期，默认 'daily'")
        limit: int = Field(100, description="返回数据条数")

    class TermStructureSchema(BaseModel):
        """Schema for DataCoreTermStructureTool."""

        symbol: str = Field(..., description="品种代码，如 'RB'、'CU'")

    class BasisSchema(BaseModel):
        """Schema for DataCoreBasisTool."""

        symbol: str = Field(..., description="品种代码")

    class MarketRegimeSchema(BaseModel):
        """Schema for DataCoreMarketRegimeTool."""

        symbol: str = Field(..., description="品种代码")
        period: str = Field("daily", description="K线周期，默认 'daily'")
        lookback: int = Field(60, description="回顾周期数")

    class NewsSchema(BaseModel):
        """Schema for DataCoreNewsTool."""

        symbol: str = Field(..., description="品种代码")
        limit: int = Field(20, description="返回新闻条数")

    class AdjustmentSchema(BaseModel):
        """Schema for DataCoreAdjustmentTool."""

        symbol: str = Field(..., description="品种代码")
        adjustment: str = Field(..., description="调整类型，'forward'/'backward'/'rollover'")
        period: str = Field("daily", description="K线周期，默认 'daily'")
        limit: int = Field(100, description="返回数据条数")

    # ============================================================
    #  Data processing tools
    # ============================================================

    class PeriodSchema(BaseModel):
        """Schema for DataCorePeriodTool."""

        df: list[dict[str, Any]] = Field(..., description="OHLCV 数据列表，每条需包含 datetime, open, high, low, close")
        target_period: str = Field(..., description="目标周期，如 '5m', '15m', '30m', '60m', 'daily', 'weekly', 'monthly'")
        source_period: Optional[str] = Field(None, description="源周期，默认自动推断")

    class UnitUnifySchema(BaseModel):
        """Schema for UnitUnifyTool."""

        df: list[dict[str, Any]] = Field(..., description="数据列表")
        field: str = Field(..., description="要转换的字段名")
        target_unit: str = Field(..., description="目标单位")
        source_unit: Optional[str] = Field(None, description="源单位，不传则自动检测")

    class DateAlignSchema(BaseModel):
        """Schema for DateAlignTool."""

        dfs: list[list[dict[str, Any]]] = Field(..., description="多个数据序列列表")
        method: Optional[str] = Field(None, description="缺失值填充方法，'ffill'/'bfill'/'interpolate'/'drop'，默认 'ffill'")

    class DuplicateMergeSchema(BaseModel):
        """Schema for DuplicateMergeTool."""

        dfs: list[list[dict[str, Any]]] = Field(..., description="多个数据列表")
        key_field: str = Field("date", description="判断重复的键字段名")

    class OutlierFilterSchema(BaseModel):
        """Schema for OutlierFilterTool."""

        df: list[dict[str, Any]] = Field(..., description="数据列表")
        field: str = Field(..., description="要检测的字段名")
        method: str = Field("zscore", description="检测方法，'iqr'/'zscore'/'rolling'")
        threshold: float = Field(3.0, description="异常阈值")

    # ============================================================
    #  Validation tools
    # ============================================================

    class CrossSourceVerifySchema(BaseModel):
        """Schema for CrossSourceVerifyTool."""

        source_data: dict[str, list[dict[str, Any]]] = Field(..., description="各数据源的数据，key 为源名，value 为数据列表")
        field: str = Field(..., description="要对比的字段名")
        key_field: str = Field("date", description="对齐键字段")

    class DataMissingDetectSchema(BaseModel):
        """Schema for DataMissingDetectTool."""

        df: list[dict[str, Any]] = Field(..., description="数据列表")
        fields: Optional[list[str]] = Field(None, description="要检测的字段列表，默认所有数值字段")

    class CalMathComputeSchema(BaseModel):
        """Schema for CalMathComputeTool."""

        df: list[dict[str, Any]] = Field(..., description="数据列表")

    # ============================================================
    #  Operations tools
    # ============================================================

    class ConfigReadSchema(BaseModel):
        """Schema for ConfigReadTool."""

        config_path: str = Field(..., description="配置文件路径或配置键名")

else:
    OHLCVSchema: Any = None
    QuoteSchema: Any = None
    SentimentSchema: Any = None
    HealthSchema: Any = None
    ListSymbolsSchema: Any = None
    MacroSchema: Any = None
    FundamentalSchema: Any = None
    F10Schema: Any = None
    IndicatorsSchema: Any = None
    TermStructureSchema: Any = None
    BasisSchema: Any = None
    MarketRegimeSchema: Any = None
    NewsSchema: Any = None
    AdjustmentSchema: Any = None
    PeriodSchema: Any = None
    UnitUnifySchema: Any = None
    DateAlignSchema: Any = None
    DuplicateMergeSchema: Any = None
    OutlierFilterSchema: Any = None
    CrossSourceVerifySchema: Any = None
    DataMissingDetectSchema: Any = None
    CalMathComputeSchema: Any = None
    ConfigReadSchema: Any = None


__all__ = [
    "HAS_PYDANTIC",
    "OHLCVSchema",
    "QuoteSchema",
    "SentimentSchema",
    "HealthSchema",
    "ListSymbolsSchema",
    "MacroSchema",
    "FundamentalSchema",
    "F10Schema",
    "IndicatorsSchema",
    "TermStructureSchema",
    "BasisSchema",
    "MarketRegimeSchema",
    "NewsSchema",
    "AdjustmentSchema",
    "PeriodSchema",
    "UnitUnifySchema",
    "DateAlignSchema",
    "DuplicateMergeSchema",
    "OutlierFilterSchema",
    "CrossSourceVerifySchema",
    "DataMissingDetectSchema",
    "CalMathComputeSchema",
    "ConfigReadSchema",
]
