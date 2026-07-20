"""新增期货数据源 mock 补充测试 — 目标 100% 覆盖率。"""
import importlib
import sys
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest


# -----------------------------------------------------------------------------
# Module-level import branches
# -----------------------------------------------------------------------------
def test_qmt_module_imports_xtquant_when_available():
    """覆盖 qmt.py 中 _XTV_AVAILABLE = True 分支。"""
    from datacore.futures.providers import qmt as qmt_mod

    original = qmt_mod._XTV_AVAILABLE
    try:
        sys.modules["xtquant"] = MagicMock()
        importlib.reload(qmt_mod)
        assert qmt_mod._XTV_AVAILABLE is True
    finally:
        sys.modules.pop("xtquant", None)
        qmt_mod._XTV_AVAILABLE = original


def test_tqsdk_module_imports_tqsdk_when_available():
    """覆盖 tqsdk.py 中 _TQ_AVAILABLE = True 分支。"""
    from datacore.futures.providers import tqsdk as tq_mod

    original = tq_mod._TQ_AVAILABLE
    try:
        sys.modules["tqsdk"] = MagicMock()
        importlib.reload(tq_mod)
        assert tq_mod._TQ_AVAILABLE is True
    finally:
        sys.modules.pop("tqsdk", None)
        tq_mod._TQ_AVAILABLE = original


# -----------------------------------------------------------------------------
# QMT Provider
# -----------------------------------------------------------------------------
@pytest.fixture
def qmt_available():
    """模拟 xtquant 已安装且可用。"""
    from datacore.futures.providers import qmt as qmt_mod

    original = qmt_mod._XTV_AVAILABLE
    qmt_mod._XTV_AVAILABLE = True
    xtquant_pkg = MagicMock()
    xtdata_mod = MagicMock()
    xtquant_pkg.xtdata = xtdata_mod
    sys.modules["xtquant"] = xtquant_pkg
    sys.modules["xtquant.xtdata"] = xtdata_mod
    yield qmt_mod
    qmt_mod._XTV_AVAILABLE = original
    sys.modules.pop("xtquant", None)
    sys.modules.pop("xtquant.xtdata", None)


class TestQMTProviderExtra:
    def test_check_available_true(self, qmt_available):
        from datacore.futures.providers.qmt import QMTProvider

        p = QMTProvider()
        assert p.check_available() is True

    def test_fetch_kline_success(self, qmt_available):
        from datacore.futures.providers.qmt import QMTProvider

        p = QMTProvider()
        xtdata = sys.modules["xtquant.xtdata"]
        df = pd.DataFrame({
            "time": ["20240101", "20240102"],
            "open": [100.0, 101.0],
            "high": [105.0, 106.0],
            "low": [99.0, 100.0],
            "close": [104.0, 105.0],
            "volume": [1000.0, 2000.0],
            "amount": [100000.0, 200000.0],
        })
        xtdata.get_market_data_ex.return_value = {"RB2501": df}
        result = p.fetch_kline("rb2501", period="daily", days=120)
        assert result is not None
        assert result.symbol == "rb2501"
        assert result.period == "daily"
        assert len(result.bars) == 2
        assert result.bars[0].open == 100.0
        xtdata.get_market_data_ex.assert_called_once()

    def test_fetch_kline_alternate_period(self, qmt_available):
        from datacore.futures.providers.qmt import QMTProvider

        p = QMTProvider()
        xtdata = sys.modules["xtquant.xtdata"]
        df = pd.DataFrame({
            "time": ["20240101"],
            "open": [100.0],
            "high": [105.0],
            "low": [99.0],
            "close": [104.0],
            "volume": [1000.0],
            "amount": [100000.0],
        })
        xtdata.get_market_data_ex.return_value = {"RB2505": df}
        result = p.fetch_kline("RB2505", period="60min", days=60)
        assert result is not None
        call_kwargs = xtdata.get_market_data_ex.call_args.kwargs
        assert call_kwargs["period"] == "1h"

    def test_fetch_kline_no_data_key(self, qmt_available):
        from datacore.futures.providers.qmt import QMTProvider

        p = QMTProvider()
        xtdata = sys.modules["xtquant.xtdata"]
        xtdata.get_market_data_ex.return_value = {}
        assert p.fetch_kline("RB2501") is None

    def test_fetch_kline_empty_dataframe(self, qmt_available):
        from datacore.futures.providers.qmt import QMTProvider

        p = QMTProvider()
        xtdata = sys.modules["xtquant.xtdata"]
        xtdata.get_market_data_ex.return_value = {"RB2501": pd.DataFrame()}
        assert p.fetch_kline("RB2501") is None

    def test_fetch_kline_row_parse_error(self, qmt_available):
        from datacore.futures.providers.qmt import QMTProvider

        p = QMTProvider()
        xtdata = sys.modules["xtquant.xtdata"]
        df = pd.DataFrame({
            "time": ["20240101"],
            "open": ["bad"],
            "high": ["bad"],
            "low": ["bad"],
            "close": ["bad"],
            "volume": ["bad"],
            "amount": ["bad"],
        })
        xtdata.get_market_data_ex.return_value = {"RB2501": df}
        result = p.fetch_kline("RB2501")
        assert result is not None
        assert result.bars == []

    def test_fetch_kline_exception(self, qmt_available):
        from datacore.futures.providers.qmt import QMTProvider

        p = QMTProvider()
        xtdata = sys.modules["xtquant.xtdata"]
        xtdata.get_market_data_ex.side_effect = Exception("market data error")
        assert p.fetch_kline("RB2501") is None

    def test_fetch_quote_success(self, qmt_available):
        from datacore.futures.providers.qmt import QMTProvider

        p = QMTProvider()
        xtdata = sys.modules["xtquant.xtdata"]
        xtdata.get_full_tick.return_value = {
            "RB2501": {
                "lastPrice": 3500.0,
                "open": 3480.0,
                "high": 3520.0,
                "low": 3470.0,
                "lastClose": 3490.0,
                "volume": 10000.0,
                "amount": 35000000.0,
            }
        }
        result = p.fetch_quote("RB2501")
        assert result is not None
        assert result.symbol == "RB2501"
        assert result.last_price == 3500.0
        assert result.source == "qmt"

    def test_fetch_quote_no_symbol_key(self, qmt_available):
        from datacore.futures.providers.qmt import QMTProvider

        p = QMTProvider()
        xtdata = sys.modules["xtquant.xtdata"]
        xtdata.get_full_tick.return_value = {"M2501": {"lastPrice": 3000.0}}
        assert p.fetch_quote("RB2501") is None

    def test_fetch_quote_empty_response(self, qmt_available):
        from datacore.futures.providers.qmt import QMTProvider

        p = QMTProvider()
        xtdata = sys.modules["xtquant.xtdata"]
        xtdata.get_full_tick.return_value = {}
        assert p.fetch_quote("RB2501") is None

    def test_fetch_quote_exception(self, qmt_available):
        from datacore.futures.providers.qmt import QMTProvider

        p = QMTProvider()
        xtdata = sys.modules["xtquant.xtdata"]
        xtdata.get_full_tick.side_effect = Exception("tick error")
        assert p.fetch_quote("RB2501") is None

    def test_fetch_contract_chain_available(self, qmt_available):
        from datacore.futures.providers.qmt import QMTProvider

        p = QMTProvider()
        assert p.fetch_contract_chain("RB") is None


# -----------------------------------------------------------------------------
# TqSdk Provider
# -----------------------------------------------------------------------------
@pytest.fixture
def tqsdk_available():
    """模拟 tqsdk 已安装且可用。"""
    from datacore.futures.providers import tqsdk as tq_mod

    original = tq_mod._TQ_AVAILABLE
    tq_mod._TQ_AVAILABLE = True
    tqsdk_pkg = MagicMock()
    sys.modules["tqsdk"] = tqsdk_pkg
    yield tq_mod
    tq_mod._TQ_AVAILABLE = original
    sys.modules.pop("tqsdk", None)


class TestTqSdkProviderExtra:
    def test_check_available_true(self, tqsdk_available):
        from datacore.futures.providers.tqsdk import TqSdkProvider

        p = TqSdkProvider()
        assert p.check_available() is True

    def _make_api_mock(self, tqsdk_pkg):
        api = MagicMock()
        auth = MagicMock()
        tqsdk_pkg.TqApi.return_value = api
        tqsdk_pkg.TqAuth.return_value = auth
        return api, auth

    def test_fetch_kline_success(self, tqsdk_available):
        from datacore.futures.providers.tqsdk import TqSdkProvider

        p = TqSdkProvider()
        tqsdk_pkg = sys.modules["tqsdk"]
        api, _ = self._make_api_mock(tqsdk_pkg)
        df = pd.DataFrame({
            "datetime": ["20240101000000000", "20240102000000000"],
            "open": [100.0, 101.0],
            "high": [105.0, 106.0],
            "low": [99.0, 100.0],
            "close": [104.0, 105.0],
            "volume": [1000.0, 2000.0],
        })
        api.get_kline_serial.return_value = df
        result = p.fetch_kline("rb2501", period="daily", days=120)
        assert result is not None
        assert result.symbol == "rb2501"
        assert len(result.bars) == 2
        assert result.bars[0].amount == 104.0 * 1000.0
        api.close.assert_called_once()

    def test_fetch_kline_empty(self, tqsdk_available):
        from datacore.futures.providers.tqsdk import TqSdkProvider

        p = TqSdkProvider()
        tqsdk_pkg = sys.modules["tqsdk"]
        api, _ = self._make_api_mock(tqsdk_pkg)
        api.get_kline_serial.return_value = pd.DataFrame()
        assert p.fetch_kline("RB2501") is None
        api.close.assert_called_once()

    def test_fetch_kline_none(self, tqsdk_available):
        from datacore.futures.providers.tqsdk import TqSdkProvider

        p = TqSdkProvider()
        tqsdk_pkg = sys.modules["tqsdk"]
        api, _ = self._make_api_mock(tqsdk_pkg)
        api.get_kline_serial.return_value = None
        assert p.fetch_kline("RB2501") is None
        api.close.assert_called_once()

    def test_fetch_kline_row_parse_error(self, tqsdk_available):
        from datacore.futures.providers.tqsdk import TqSdkProvider

        p = TqSdkProvider()
        tqsdk_pkg = sys.modules["tqsdk"]
        api, _ = self._make_api_mock(tqsdk_pkg)
        df = pd.DataFrame({
            "datetime": ["20240101"],
            "open": ["bad"],
            "high": ["bad"],
            "low": ["bad"],
            "close": ["bad"],
            "volume": ["bad"],
        })
        api.get_kline_serial.return_value = df
        result = p.fetch_kline("RB2501")
        assert result is not None
        assert result.bars == []
        api.close.assert_called_once()

    def test_fetch_kline_exception(self, tqsdk_available):
        from datacore.futures.providers.tqsdk import TqSdkProvider

        p = TqSdkProvider()
        tqsdk_pkg = sys.modules["tqsdk"]
        tqsdk_pkg.TqApi.side_effect = Exception("login fail")
        assert p.fetch_kline("RB2501") is None

    def test_fetch_quote_success(self, tqsdk_available):
        from datacore.futures.providers.tqsdk import TqSdkProvider

        p = TqSdkProvider()
        tqsdk_pkg = sys.modules["tqsdk"]
        api, _ = self._make_api_mock(tqsdk_pkg)
        quote = MagicMock()
        quote.last_price = 3500.0
        quote.open = 3480.0
        quote.highest = 3520.0
        quote.lowest = 3470.0
        quote.pre_close = 3490.0
        quote.volume = 10000.0
        quote.amount = 35000000.0
        api.get_quote.return_value = quote
        result = p.fetch_quote("RB2501")
        assert result is not None
        assert result.symbol == "RB2501"
        assert result.last_price == 3500.0
        assert result.high == 3520.0
        api.close.assert_called_once()

    def test_fetch_quote_none(self, tqsdk_available):
        from datacore.futures.providers.tqsdk import TqSdkProvider

        p = TqSdkProvider()
        tqsdk_pkg = sys.modules["tqsdk"]
        api, _ = self._make_api_mock(tqsdk_pkg)
        api.get_quote.return_value = None
        assert p.fetch_quote("RB2501") is None
        api.close.assert_called_once()

    def test_fetch_quote_exception(self, tqsdk_available):
        from datacore.futures.providers.tqsdk import TqSdkProvider

        p = TqSdkProvider()
        tqsdk_pkg = sys.modules["tqsdk"]
        tqsdk_pkg.TqApi.side_effect = Exception("api error")
        assert p.fetch_quote("RB2501") is None


# -----------------------------------------------------------------------------
# Exchange API Provider
# -----------------------------------------------------------------------------
class TestExchangeApiProviderExtra:
    def test_fetch_kline_returns_none(self):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider

        p = ExchangeApiProvider()
        assert p.fetch_kline("RB2501") is None

    def test_fetch_quote_returns_none(self):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider

        p = ExchangeApiProvider()
        assert p.fetch_quote("RB2501") is None

    def _mock_client(self, status_code=200):
        mock_inst = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_inst.__enter__.return_value = mock_inst
        mock_inst.get.return_value = mock_resp
        return mock_inst, mock_resp

    @pytest.mark.parametrize("symbol,exch", [
        ("RB2501", "SHFE"),
        ("TA2501", "CZCE"),
        ("M2501", "DCE"),
    ])
    def test_fetch_warehouse_receipts_success(self, symbol, exch):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider

        with patch("datacore.futures.providers.exchange_api.httpx.Client") as mock_client:
            mock_inst, _ = self._mock_client(200)
            mock_client.return_value = mock_inst
            p = ExchangeApiProvider()
            result = p.fetch_warehouse_receipts(symbol)
            assert result is not None
            assert result.symbol == symbol.upper()

    def test_fetch_warehouse_receipts_unknown_exchange(self):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider

        p = ExchangeApiProvider()
        assert p.fetch_warehouse_receipts("ZZZ999") is None

    def test_fetch_warehouse_receipts_http_error(self):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider

        with patch("datacore.futures.providers.exchange_api.httpx.Client") as mock_client:
            mock_inst, _ = self._mock_client(500)
            mock_client.return_value = mock_inst
            p = ExchangeApiProvider()
            assert p.fetch_warehouse_receipts("RB2501") is None

    def test_fetch_warehouse_receipts_exception(self):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider

        with patch("datacore.futures.providers.exchange_api.httpx.Client") as mock_client:
            mock_inst, _ = self._mock_client(200)
            mock_inst.get.side_effect = Exception("network down")
            mock_client.return_value = mock_inst
            p = ExchangeApiProvider()
            assert p.fetch_warehouse_receipts("RB2501") is None

    @pytest.mark.parametrize("symbol,exch", [
        ("RB2501", "SHFE"),
        ("TA2501", "CZCE"),
        ("M2501", "DCE"),
    ])
    def test_fetch_position_rank_success(self, symbol, exch):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider

        with patch("datacore.futures.providers.exchange_api.httpx.Client") as mock_client:
            mock_inst, _ = self._mock_client(200)
            mock_client.return_value = mock_inst
            p = ExchangeApiProvider()
            result = p.fetch_position_rank(symbol)
            assert result is not None
            assert result.symbol == symbol.upper()
            assert result.contract == symbol.upper()

    def test_fetch_position_rank_unknown_exchange(self):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider

        p = ExchangeApiProvider()
        assert p.fetch_position_rank("ZZZ999") is None

    def test_fetch_position_rank_http_error(self):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider

        with patch("datacore.futures.providers.exchange_api.httpx.Client") as mock_client:
            mock_inst, _ = self._mock_client(404)
            mock_client.return_value = mock_inst
            p = ExchangeApiProvider()
            assert p.fetch_position_rank("RB2501") is None

    def test_fetch_position_rank_exception(self):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider

        with patch("datacore.futures.providers.exchange_api.httpx.Client") as mock_client:
            mock_inst, _ = self._mock_client(200)
            mock_inst.get.side_effect = Exception("network down")
            mock_client.return_value = mock_inst
            p = ExchangeApiProvider()
            assert p.fetch_position_rank("RB2501") is None


# -----------------------------------------------------------------------------
# ShengYiShe Provider
# -----------------------------------------------------------------------------
class TestShengYiSheProviderExtra:
    def test_fetch_kline_returns_none(self):
        from datacore.futures.providers.shengyishe import ShengYiSheProvider

        p = ShengYiSheProvider()
        assert p.fetch_kline("RB2501") is None

    def test_fetch_quote_returns_none(self):
        from datacore.futures.providers.shengyishe import ShengYiSheProvider

        p = ShengYiSheProvider()
        assert p.fetch_quote("RB2501") is None

    @patch("datacore.futures.providers.shengyishe.httpx.Client")
    def test_fetch_basis_empty_text(self, mock_client):
        from datacore.futures.providers.shengyishe import ShengYiSheProvider

        p = ShengYiSheProvider()
        mock_inst = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = ""
        mock_inst.__enter__.return_value = mock_inst
        mock_inst.get.return_value = mock_resp
        mock_client.return_value = mock_inst
        assert p.fetch_basis("RB") is None

    @patch("datacore.futures.providers.shengyishe.httpx.Client")
    def test_fetch_basis_price_zero(self, mock_client):
        from datacore.futures.providers.shengyishe import ShengYiSheProvider

        p = ShengYiSheProvider()
        mock_inst = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "<html>0 元/吨</html>"
        mock_inst.__enter__.return_value = mock_inst
        mock_inst.get.return_value = mock_resp
        mock_client.return_value = mock_inst
        assert p.fetch_basis("RB") is None

    @patch("datacore.futures.providers.shengyishe.httpx.Client")
    def test_check_available_ok(self, mock_client):
        from datacore.futures.providers.shengyishe import ShengYiSheProvider

        p = ShengYiSheProvider()
        mock_inst = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_inst.__enter__.return_value = mock_inst
        mock_inst.head.return_value = mock_resp
        mock_client.return_value = mock_inst
        assert p.check_available() is True

    @patch("datacore.futures.providers.shengyishe.httpx.Client")
    def test_check_available_fail(self, mock_client):
        from datacore.futures.providers.shengyishe import ShengYiSheProvider

        p = ShengYiSheProvider()
        mock_client.side_effect = Exception("timeout")
        assert p.check_available() is False


# -----------------------------------------------------------------------------
# Web Fallback Provider
# -----------------------------------------------------------------------------
class TestWebFallbackProviderExtra:
    def test_fetch_kline_success_returns_none(self):
        from datacore.futures.providers.web_fallback import WebFallbackProvider

        p = WebFallbackProvider()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        p._client = MagicMock()
        p._client.get.return_value = mock_resp
        assert p.fetch_kline("RB2501") is None

    def test_fetch_kline_http_error(self):
        from datacore.futures.providers.web_fallback import WebFallbackProvider

        p = WebFallbackProvider()
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        p._client = MagicMock()
        p._client.get.return_value = mock_resp
        assert p.fetch_kline("RB2501") is None

    def test_fetch_kline_exception(self):
        from datacore.futures.providers.web_fallback import WebFallbackProvider

        p = WebFallbackProvider()
        p._client = MagicMock()
        p._client.get.side_effect = Exception("network error")
        assert p.fetch_kline("RB2501") is None

    def test_fetch_quote_success_returns_none(self):
        from datacore.futures.providers.web_fallback import WebFallbackProvider

        p = WebFallbackProvider()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "var hq_str_nf_rb2501=..."
        p._client = MagicMock()
        p._client.get.return_value = mock_resp
        assert p.fetch_quote("RB2501") is None

    def test_fetch_quote_empty_text(self):
        from datacore.futures.providers.web_fallback import WebFallbackProvider

        p = WebFallbackProvider()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = ""
        p._client = MagicMock()
        p._client.get.return_value = mock_resp
        assert p.fetch_quote("RB2501") is None

    def test_fetch_quote_no_data_marker(self):
        from datacore.futures.providers.web_fallback import WebFallbackProvider

        p = WebFallbackProvider()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = 'hq_str_nf_rb2501=""'
        p._client = MagicMock()
        p._client.get.return_value = mock_resp
        assert p.fetch_quote("RB2501") is None

    def test_fetch_quote_http_error(self):
        from datacore.futures.providers.web_fallback import WebFallbackProvider

        p = WebFallbackProvider()
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        p._client = MagicMock()
        p._client.get.return_value = mock_resp
        assert p.fetch_quote("RB2501") is None

    def test_fetch_quote_exception(self):
        from datacore.futures.providers.web_fallback import WebFallbackProvider

        p = WebFallbackProvider()
        p._client = MagicMock()
        p._client.get.side_effect = Exception("network error")
        assert p.fetch_quote("RB2501") is None

    def test_fetch_term_structure_returns_none(self):
        from datacore.futures.providers.web_fallback import WebFallbackProvider

        p = WebFallbackProvider()
        assert p.fetch_term_structure("RB") is None

    def test_fetch_spread_returns_none(self):
        from datacore.futures.providers.web_fallback import WebFallbackProvider

        p = WebFallbackProvider()
        assert p.fetch_spread("RB", "RB2501", "RB2505") is None
