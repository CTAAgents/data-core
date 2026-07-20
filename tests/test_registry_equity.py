"""SymbolRegistry A 股/ETF/可转债自动识别测试（G32）。"""
from datacore.registry.symbol_registry import SymbolRegistry
from datacore.models.enums import MarketType


class TestEquitySymbolRecognition:
    """A 股代码自动识别 — 无需显式注册。"""

    def test_sh_main_board(self):
        """沪市主板 60 开头 → STOCK。"""
        sr = SymbolRegistry()
        assert sr.resolve_market("600519") == MarketType.STOCK
        assert sr.resolve_market("601318") == MarketType.STOCK

    def test_sz_main_board(self):
        """深市主板 00 开头 → STOCK。"""
        sr = SymbolRegistry()
        assert sr.resolve_market("000001") == MarketType.STOCK
        assert sr.resolve_market("000858") == MarketType.STOCK

    def test_chinext(self):
        """创业板 30 开头 → STOCK。"""
        sr = SymbolRegistry()
        assert sr.resolve_market("300750") == MarketType.STOCK
        assert sr.resolve_market("301236") == MarketType.STOCK

    def test_star(self):
        """科创板 68 开头 → STOCK。"""
        sr = SymbolRegistry()
        assert sr.resolve_market("688981") == MarketType.STOCK

    def test_bj_stock(self):
        """北交所 8/4 开头 → STOCK。"""
        sr = SymbolRegistry()
        assert sr.resolve_market("830799") == MarketType.STOCK
        assert sr.resolve_market("430139") == MarketType.STOCK

    def test_sh_etf(self):
        """沪市 ETF 510/511/512/513/515/588/516 前缀 → ETF。"""
        sr = SymbolRegistry()
        assert sr.resolve_market("510050") == MarketType.ETF
        assert sr.resolve_market("511260") == MarketType.ETF
        assert sr.resolve_market("512100") == MarketType.ETF
        assert sr.resolve_market("513050") == MarketType.ETF
        assert sr.resolve_market("515880") == MarketType.ETF
        assert sr.resolve_market("588000") == MarketType.ETF
        assert sr.resolve_market("516160") == MarketType.ETF

    def test_sz_etf(self):
        """深市 ETF 159 前缀 → ETF。"""
        sr = SymbolRegistry()
        assert sr.resolve_market("159915") == MarketType.ETF
        assert sr.resolve_market("159901") == MarketType.ETF

    def test_convertible_bond(self):
        """可转债 110/113/118/127/128/132/133 前缀 → CB。"""
        sr = SymbolRegistry()
        assert sr.resolve_market("113001") == MarketType.CB
        assert sr.resolve_market("118001") == MarketType.CB
        assert sr.resolve_market("127006") == MarketType.CB
        assert sr.resolve_market("128048") == MarketType.CB

    def test_futures_still_works(self):
        """期货品种识别保持不变。"""
        sr = SymbolRegistry()
        assert sr.resolve_market("RB") == MarketType.FUTURES
        assert sr.resolve_market("AU") == MarketType.FUTURES
        assert sr.resolve_market("CU") == MarketType.FUTURES

    def test_unknown_returns_none(self):
        """无规则识别的代码返回 None。"""
        sr = SymbolRegistry()
        # 3 位字母但非期货
        assert sr.resolve_market("ZZZ") is None
        # 5 位数字（非 A 股标准）
        assert sr.resolve_market("12345") is None
