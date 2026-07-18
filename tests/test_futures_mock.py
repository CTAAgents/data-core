import pytest
from datacore.futures.providers.tdx_lc import TdxLcProvider
from datacore.models.enums import DataType


class TestTdxLcMock:
    def test_check_available_false(self):
        p = TdxLcProvider()
        p._post = lambda m, params: {}
        assert not p.check_available()
        
    def test_check_available_true(self):
        p = TdxLcProvider()
        p._post = lambda m, params: {'Value': [{'Code': 'RB2501'}]}
        assert p.check_available()
        
    def test_fetch_kline_no_contract(self):
        p = TdxLcProvider()
        p._post = lambda m, params: {}
        assert p.fetch_kline('ZZZ') is None
        
    def test_fetch_quote_no_contract(self):
        p = TdxLcProvider()
        p._post = lambda m, params: {}
        assert p.fetch_quote('ZZZ') is None

    def test_supported_types_includes_chain(self):
        p = TdxLcProvider()
        assert DataType.FUTURES_CONTRACT_CHAIN in p.supported_types

    def test_supported_types_includes_term_structure(self):
        p = TdxLcProvider()
        assert DataType.FUTURES_TERM_STRUCTURE in p.supported_types

    def test_supported_types_includes_spread(self):
        p = TdxLcProvider()
        assert DataType.FUTURES_SPREAD in p.supported_types

    def test_fetch_contract_chain_empty(self):
        p = TdxLcProvider()
        p._post = lambda m, params: {}
        assert p.fetch_contract_chain('RB') is None

    def test_fetch_term_structure_empty(self):
        p = TdxLcProvider()
        p._post = lambda m, params: {}
        assert p.fetch_term_structure('RB') is None

    def test_fetch_spread_no_kline(self):
        p = TdxLcProvider()
        p._post = lambda m, params: {}
        assert p.fetch_spread('RB', 'RB2510', 'RB2601') is None

    def test_list_symbol_contracts_empty(self):
        p = TdxLcProvider()
        p._post = lambda m, params: {}
        assert p._list_symbol_contracts('RB') == []
