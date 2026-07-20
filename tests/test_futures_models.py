import pytest
from datacore.models.enums import DataType
from datacore.models.futures import (
    ContractChain,
    TermStructurePoint, TermStructure,
    SpreadData, BasisData,
    PositionRankData,
    WarehouseReceiptData,
)
from datacore.models.ohlcv import KlineData


class TestFuturesDataTypes:
    def test_contract_chain_datatype_exists(self):
        assert hasattr(DataType, 'FUTURES_CONTRACT_CHAIN')
        assert DataType.FUTURES_CONTRACT_CHAIN.value == 'futures_contract_chain'

    def test_term_structure_datatype_exists(self):
        assert hasattr(DataType, 'FUTURES_TERM_STRUCTURE')
        assert DataType.FUTURES_TERM_STRUCTURE.value == 'futures_term_structure'

    def test_spread_datatype_exists(self):
        assert hasattr(DataType, 'FUTURES_SPREAD')
        assert DataType.FUTURES_SPREAD.value == 'futures_spread'

    def test_basis_datatype_exists(self):
        assert hasattr(DataType, 'FUTURES_BASIS')
        assert DataType.FUTURES_BASIS.value == 'futures_basis'

    def test_position_datatype_exists(self):
        assert hasattr(DataType, 'FUTURES_POSITION')
        assert DataType.FUTURES_POSITION.value == 'futures_position'

    def test_warehouse_receipt_datatype_exists(self):
        assert hasattr(DataType, 'FUTURES_WAREHOUSE_RECEIPT')
        assert DataType.FUTURES_WAREHOUSE_RECEIPT.value == 'futures_warehouse_receipt'

    def test_etf_datatypes_exist(self):
        assert hasattr(DataType, 'ETF_NAV')
        assert hasattr(DataType, 'ETF_PREMIUM')
        assert hasattr(DataType, 'ETF_FUND_FLOW')

    def test_cb_datatypes_exist(self):
        assert hasattr(DataType, 'CB_CONVERSION')
        assert hasattr(DataType, 'CB_TERMS')
        assert hasattr(DataType, 'CB_PURE_BOND')


class TestContractChain:
    def test_empty_chain(self):
        cc = ContractChain(symbol='RB')
        assert cc.symbol == 'RB'
        assert cc.contracts == []
        assert cc.main_contract is None

    def test_chain_with_contracts(self):
        kd = KlineData(symbol='RB2510', period='daily')
        cc = ContractChain(symbol='RB', contracts=['RB2510', 'RB2601'],
                           klines={'RB2510': kd})
        assert cc.main_contract == 'RB2510'
        assert len(cc.klines) == 1


class TestTermStructure:
    def test_empty_structure(self):
        ts = TermStructure(symbol='RB')
        assert ts.symbol == 'RB'
        assert ts.points == []
        assert not ts.is_contango
        assert ts.slope == 0.0

    def test_contango_structure(self):
        ts = TermStructure(symbol='RB', points=[
            TermStructurePoint(contract='RB2510', month='RB2510', price=3000),
            TermStructurePoint(contract='RB2601', month='RB2601', price=3100, yield_from_front=0.033),
        ])
        assert ts.is_contango
        assert ts.slope == pytest.approx(100 / 3000)

    def test_backwardation_structure(self):
        ts = TermStructure(symbol='RB', points=[
            TermStructurePoint(contract='RB2510', month='RB2510', price=3100),
            TermStructurePoint(contract='RB2601', month='RB2601', price=3000),
        ])
        assert not ts.is_contango
        assert ts.slope == pytest.approx(-100 / 3100)


class TestSpreadData:
    def test_empty_spread(self):
        sd = SpreadData(symbol='RB', near_contract='RB2510', far_contract='RB2601')
        assert sd.latest_spread == 0.0

    def test_spread_with_series(self):
        sd = SpreadData(symbol='RB', near_contract='RB2510', far_contract='RB2601',
                        spread_series=[
                            {'date': '20260717', 'spread': 50.0},
                            {'date': '20260718', 'spread': 60.0},
                        ])
        assert sd.latest_spread == 60.0


class TestBasisData:
    def test_basic_basis(self):
        bd = BasisData(symbol='RB', spot_price=3050, futures_price=3000,
                       basis=50, basis_rate=0.0167)
        assert bd.basis == 50
        assert bd.basis_rate == pytest.approx(0.0167)


class TestPositionRankData:
    def test_empty_rank(self):
        pr = PositionRankData(symbol='RB', contract='RB2510', date='20260718')
        assert pr.long_ranks == []
        assert pr.short_ranks == []


class TestWarehouseReceiptData:
    def test_empty_receipt(self):
        wr = WarehouseReceiptData(symbol='RB', date='20260718')
        assert wr.total_receipts == 0.0
        assert wr.change == 0.0
