"""宏观数据源。"""
from .base import MacroDataSource
from .eastmoney_macro import EastMoneyMacroProvider

__all__ = ["MacroDataSource", "EastMoneyMacroProvider"]
