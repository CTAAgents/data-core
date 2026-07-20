"""Equity 模块综合测试。

覆盖:
  - equity_provider.py  EquityDataProvider
  - financial.py        calc_financial_score
  - providers/base.py   EquityDataSource.check_available
  - providers/eastmoney.py  EastMoneyEquityProvider
  - providers/tencent.py    TencentProvider / _parse_tencent_quote / _detect_market_code
"""
from __future__ import annotations
from unittest.mock import patch, MagicMock
import pytest
import time

from datacore.models.enums import DataType, MarketType, SourceGrade
from datacore.models.payload import DataPayload
from datacore.equity.equity_provider import EquityDataProvider
from datacore.equity.financial import calc_financial_score
from datacore.equity.providers.base import EquityDataSource
from datacore.equity.providers.eastmoney import EastMoneyEquityProvider
from datacore.equity.providers.tencent import TencentProvider, _parse_tencent_quote


# ── helpers ──

class _ConcreteSource(EquityDataSource):
    """用于测试抽象基类的具体子类。"""
    name = "test"
    priority = 0

    def fetch(self, symbol, data_type, params=None):
        return None


def _make_payload(symbol="600000", data_type=DataType.OHLCV, grade=SourceGrade.PRIMARY):
    """构建一个可用的 DataPayload。"""
    return DataPayload(
        symbol=symbol, data_type=data_type,
        market=MarketType.STOCK, grade=grade,
        collected_at=time.time(),
    )


# ════════════════════════════════════════════════
# providers / base.py
# ════════════════════════════════════════════════

class TestEquityDataSourceBase:
    """EquityDataSource 基类 — 覆盖 line 21 默认 check_available。"""

    def test_default_check_available(self):
        ds = _ConcreteSource()
        assert ds.check_available() is True

    def test_default_attributes(self):
        ds = _ConcreteSource()
        assert ds.supported_markets == {MarketType.STOCK, MarketType.ETF, MarketType.CB, MarketType.REIT}


# ════════════════════════════════════════════════
# equity_provider.py
# ════════════════════════════════════════════════

class TestEquityDataProvider:
    """EquityDataProvider — 多源降级链。"""

    def test_init_creates_three_sources(self):
        provider = EquityDataProvider()
        assert len(provider.sources) == 3
        from datacore.equity.providers.tencent import TencentProvider
        from datacore.equity.providers.eastmoney import EastMoneyEquityProvider
        from datacore.equity.providers.guosen import GuosenProvider
        assert isinstance(provider.sources[0], TencentProvider)
        assert isinstance(provider.sources[1], EastMoneyEquityProvider)
        assert isinstance(provider.sources[2], GuosenProvider)

    def test_get_first_source_available_returns_result(self):
        provider = EquityDataProvider()
        payload = _make_payload()
        provider.sources[0].check_available = MagicMock(return_value=True)
        provider.sources[0].fetch = MagicMock(return_value=payload)
        provider.sources[1].check_available = MagicMock(return_value=True)

        result = provider.get("600000", DataType.OHLCV)
        assert result is payload
        provider.sources[0].fetch.assert_called_once_with("600000", DataType.OHLCV, None)

    def test_get_fallback_to_second_source(self):
        provider = EquityDataProvider()
        payload = _make_payload()
        provider.sources[0].check_available = MagicMock(return_value=False)
        provider.sources[1].check_available = MagicMock(return_value=True)
        provider.sources[1].fetch = MagicMock(return_value=payload)

        result = provider.get("600000", DataType.OHLCV)
        assert result is payload
        provider.sources[1].fetch.assert_called_once_with("600000", DataType.OHLCV, None)

    def test_get_all_sources_unavailable(self):
        provider = EquityDataProvider()
        provider.sources[0].check_available = MagicMock(return_value=False)
        provider.sources[1].check_available = MagicMock(return_value=False)

        result = provider.get("600000", DataType.OHLCV)
        assert result.grade == SourceGrade.UNAVAILABLE
        assert "不可用" in result.errors[0]

    def test_get_fetch_returns_none_falls_through(self):
        """fetch 返回 None → 继续下一源。"""
        provider = EquityDataProvider()
        provider.sources[0].check_available = MagicMock(return_value=True)
        provider.sources[0].fetch = MagicMock(return_value=None)
        provider.sources[1].check_available = MagicMock(return_value=True)
        provider.sources[1].fetch = MagicMock(return_value=None)

        result = provider.get("600000", DataType.OHLCV)
        assert result.grade == SourceGrade.UNAVAILABLE

    def test_get_fetch_raises_exception_falls_through(self):
        """fetch 抛异常 → 继续下一源。"""
        provider = EquityDataProvider()
        payload = _make_payload()
        provider.sources[0].check_available = MagicMock(return_value=True)
        provider.sources[0].fetch = MagicMock(side_effect=RuntimeError("network error"))
        provider.sources[1].check_available = MagicMock(return_value=True)
        provider.sources[1].fetch = MagicMock(return_value=payload)

        result = provider.get("600000", DataType.OHLCV)
        assert result is payload

    def test_get_data_type_not_supported_skips_source(self):
        """data_type 不在 supported_types 中 → 跳过。"""
        provider = EquityDataProvider()
        # Tencent 不支持 MACRO
        provider.sources[0].check_available = MagicMock(return_value=True)
        provider.sources[0].fetch = MagicMock()
        provider.sources[1].check_available = MagicMock(return_value=True)
        provider.sources[1].fetch = MagicMock(return_value=_make_payload(data_type=DataType.MACRO))

        result = provider.get("600000", DataType.MACRO)
        assert result.grade != SourceGrade.UNAVAILABLE
        # 第一源应被跳过（Tencent 不支持 MACRO）
        provider.sources[0].fetch.assert_not_called()

    def test_get_payload_not_available_falls_through(self):
        """payload.available 为 False → 继续下一源。"""
        provider = EquityDataProvider()
        unavailable = _make_payload(grade=SourceGrade.UNAVAILABLE)
        payload = _make_payload()
        provider.sources[0].check_available = MagicMock(return_value=True)
        provider.sources[0].fetch = MagicMock(return_value=unavailable)
        provider.sources[1].check_available = MagicMock(return_value=True)
        provider.sources[1].fetch = MagicMock(return_value=payload)

        result = provider.get("600000", DataType.OHLCV)
        assert result is payload

    def test_get_params_passed_through(self):
        provider = EquityDataProvider()
        payload = _make_payload()
        provider.sources[0].check_available = MagicMock(return_value=True)
        provider.sources[0].fetch = MagicMock(return_value=payload)
        params = {"period": "weekly", "days": 100}

        provider.get("600000", DataType.OHLCV, params)
        provider.sources[0].fetch.assert_called_once_with("600000", DataType.OHLCV, params)

    # ── _get_etf 多源降级链 ──

    def test_get_etf_first_source_returns_result(self):
        provider = EquityDataProvider()
        payload = _make_payload(data_type=DataType.OHLCV)
        provider.sources[0].check_available = MagicMock(return_value=True)
        provider.sources[0].fetch = MagicMock(return_value=payload)

        result = provider._get_etf("510300", DataType.OHLCV)
        assert result is payload
        provider.sources[0].fetch.assert_called_once_with("510300", DataType.OHLCV, None)

    def test_get_etf_skips_unavailable_source(self):
        provider = EquityDataProvider()
        payload = _make_payload(data_type=DataType.OHLCV)
        provider.sources[0].check_available = MagicMock(return_value=False)
        provider.sources[1].check_available = MagicMock(return_value=True)
        provider.sources[1].fetch = MagicMock(return_value=payload)

        result = provider._get_etf("510300", DataType.OHLCV)
        assert result is payload
        provider.sources[1].fetch.assert_called_once_with("510300", DataType.OHLCV, None)

    def test_get_etf_skips_unsupported_type(self):
        provider = EquityDataProvider()
        payload = _make_payload(data_type=DataType.MACRO)
        provider.sources[0].check_available = MagicMock(return_value=True)
        provider.sources[0].fetch = MagicMock()
        provider.sources[1].check_available = MagicMock(return_value=True)
        provider.sources[1].fetch = MagicMock(return_value=payload)

        result = provider._get_etf("510300", DataType.MACRO)
        assert result is payload
        provider.sources[0].fetch.assert_not_called()

    def test_get_etf_exception_falls_through(self):
        provider = EquityDataProvider()
        payload = _make_payload(data_type=DataType.OHLCV)
        provider.sources[0].check_available = MagicMock(return_value=True)
        provider.sources[0].fetch = MagicMock(side_effect=RuntimeError("boom"))
        provider.sources[1].check_available = MagicMock(return_value=True)
        provider.sources[1].fetch = MagicMock(return_value=payload)

        result = provider._get_etf("510300", DataType.OHLCV)
        assert result is payload

    def test_get_etf_all_sources_fail_returns_none(self):
        provider = EquityDataProvider()
        provider.sources[0].check_available = MagicMock(return_value=False)
        provider.sources[1].check_available = MagicMock(return_value=True)
        provider.sources[1].fetch = MagicMock(return_value=None)
        provider.sources[2].check_available = MagicMock(return_value=False)

        result = provider._get_etf("510300", DataType.OHLCV)
        assert result is None


# ════════════════════════════════════════════════
# providers / eastmoney.py
# ════════════════════════════════════════════════

class TestEastMoneyProvider:
    """EastMoneyEquityProvider — HTTP 数据源。"""

    # ── _fetch_kline ──

    def test_fetch_kline_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "klines": [
                    "2024-01-02,10.0,10.5,11.0,9.5,100000,1000000",
                    "2024-01-03,10.5,11.0,11.5,10.0,200000,2000000",
                ]
            }
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_kline("600000")

        assert result is not None
        assert result.data_type == DataType.OHLCV
        assert result.data.symbol == "600000"
        assert result.data.period == "daily"
        assert len(result.data.bars) == 2
        assert result.data.bars[0].date == "2024-01-02"
        assert result.data.bars[0].open == 10.0
        assert result.data.bars[0].close == 10.5
        assert result.data.bars[0].high == 11.0
        assert result.data.bars[0].low == 9.5
        assert result.data.bars[0].volume == 100000
        assert result.data.bars[0].amount == 1000000

    def test_fetch_kline_shenzhen_code(self):
        """深圳市场代码（0 开头）→ secid 用 0. 前缀。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "klines": [
                    "2024-01-02,10.0,10.5,11.0,9.5,100000,1000000",
                ]
            }
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_kline("000001")

        assert result is not None
        # 验证请求参数中的 secid
        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["secid"] == "0.000001"

    def test_fetch_kline_no_data_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": None}
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_kline("600000")

        assert result is None

    def test_fetch_kline_empty_klines_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"klines": []}}
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_kline("600000")

        assert result is None

    def test_fetch_kline_exception_returns_none(self):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.side_effect = RuntimeError("timeout")

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_kline("600000")

        assert result is None

    def test_fetch_kline_bad_row_skipped(self):
        """某行解析失败应跳过, 不影响其他行。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "klines": [
                    "2024-01-02,10.0,10.5,11.0,9.5,100000,1000000",
                    "bad_row",  # 缺少字段
                ]
            }
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_kline("600000")

        assert result is not None
        assert len(result.data.bars) == 1

    # ── _fetch_financial ──

    def test_fetch_financial_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "f162": 15.0, "f167": 14.5, "f168": 1.5,
                "f45": 100_000_000_000, "f46": 10_000_000_000,
            }
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_financial("600000")

        assert result is not None
        assert result.data_type == DataType.FINANCIAL
        assert result.data["pe"] == 15.0
        assert result.data["pe_ttm"] == 14.5
        assert result.data["pb"] == 1.5
        assert result.data["market_cap"] == 100_000_000_000
        assert result.data["total_share"] == 10_000_000_000

    def test_fetch_financial_no_data_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": None}
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_financial("600000")

        assert result is None

    def test_fetch_financial_exception_returns_none(self):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.side_effect = RuntimeError("timeout")

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_financial("600000")

        assert result is None

    def test_fetch_financial_none_values(self):
        """财务字段为 None 应映射为 None。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"f162": "--", "f167": None, "f168": ""}}
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_financial("600000")

        assert result is not None
        assert result.data["pe"] is None
        assert result.data["pe_ttm"] is None
        assert result.data["pb"] is None

    def test_fetch_financial_invalid_values(self):
        """无法转为 float 的值 → 覆盖 _f 的 except 分支。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"f162": "invalid_number", "f167": "NaN_text"}}
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_financial("600000")

        assert result is not None
        assert result.data["pe"] is None
        assert result.data["pe_ttm"] is None

    # ── _fetch_macro ──

    def test_fetch_macro_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "result": {
                "data": [
                    {"REPORT_DATE": "2024-01-01", "INDICATOR_ID": "PMI", "CLOSE": 50.5},
                ]
            }
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_macro()

        assert result is not None
        assert result.data_type == DataType.MACRO
        assert result.data["pmi"] == 50.5
        assert result.data["pmi_date"] == "2024-01-01"

    def test_fetch_macro_no_data_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": {"data": []}}
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_macro()

        assert result is None

    def test_fetch_macro_exception_returns_none(self):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.side_effect = RuntimeError("timeout")

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            result = provider._fetch_macro()

        assert result is None

    # ── check_available ──

    def test_check_available_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.head.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            assert provider.check_available() is True

    def test_check_available_server_error(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.head.return_value = mock_resp

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            assert provider.check_available() is False

    def test_check_available_exception(self):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.head.side_effect = RuntimeError("timeout")

        with patch("datacore.equity.providers.eastmoney.httpx.Client", return_value=mock_client):
            provider = EastMoneyEquityProvider()
            assert provider.check_available() is False

    # ── fetch ──

    def test_fetch_unsupported_type(self):
        provider = EastMoneyEquityProvider()
        result = provider.fetch("600000", DataType.QUOTE)
        assert result is None

    def test_fetch_ohlcv_delegates(self):
        provider = EastMoneyEquityProvider()
        with patch.object(provider, "_fetch_kline", return_value="ok"):
            assert provider.fetch("600000", DataType.OHLCV) == "ok"

    def test_fetch_financial_delegates(self):
        provider = EastMoneyEquityProvider()
        with patch.object(provider, "_fetch_financial", return_value="ok"):
            assert provider.fetch("600000", DataType.FINANCIAL) == "ok"

    def test_fetch_macro_delegates(self):
        provider = EastMoneyEquityProvider()
        with patch.object(provider, "_fetch_macro", return_value="ok"):
            assert provider.fetch("600000", DataType.MACRO) == "ok"


# ════════════════════════════════════════════════
# providers / tencent.py
# ════════════════════════════════════════════════

class TestTencentProvider:
    """TencentProvider — HTTP 数据源。"""

    # ── _detect_market_code ──

    @pytest.mark.parametrize("symbol,expected", [
        ("600000", "sh"),
        ("500000", "sh"),
        ("110000", "sh"),
        ("000001", "sz"),
        ("300001", "sz"),
        ("123456", "sz"),
        ("002001", "sz"),
        ("399001", "sz"),
        ("888888", "sh"),   # 默认值
    ])
    def test_detect_market_code(self, symbol, expected):
        from datacore.equity.providers.tencent import _detect_market_code
        assert _detect_market_code(symbol) == expected

    # ── _parse_tencent_quote ──

    def _build_quote_text(self, **overrides) -> str:
        """构建腾讯行情文本（以 ~ 分隔）。"""
        parts = [""] * 35
        parts[0] = "浦发银行"
        parts[1] = "600000"
        parts[3] = "10.50"
        parts[4] = "10.00"
        parts[5] = "10.20"
        parts[6] = "100000"
        parts[7] = "1000"       # 万元
        parts[9] = "10.40"
        parts[10] = "10.60"
        parts[11] = "10.30"
        parts[12] = "10.70"
        parts[13] = "10.20"
        parts[14] = "10.80"
        parts[15] = "10.10"
        parts[16] = "10.90"
        parts[17] = "10.00"
        parts[18] = "11.00"
        parts[31] = "2024-01-01 15:00:00"
        parts[32] = "5.00"
        parts[33] = "11.00"
        parts[34] = "9.50"
        for k, v in overrides.items():
            parts[int(k)] = str(v)
        return "~".join(parts)

    def test_parse_tencent_quote_normal(self):
        text = self._build_quote_text()
        qd = _parse_tencent_quote(text, "600000")
        assert qd is not None
        assert qd.symbol == "600000"
        assert qd.last_price == 10.50
        assert qd.pre_close == 10.00
        assert qd.open == 10.20
        assert qd.volume == 100000
        assert qd.amount == 1000 * 10000  # 万元 → 元
        assert qd.high == 11.00
        assert qd.low == 9.50
        assert qd.change_pct == 5.00
        assert qd.update_time == "2024-01-01 15:00:00"
        assert qd.bid_price == [10.40, 10.30, 10.20, 10.10, 10.00]
        assert qd.ask_price == [10.60, 10.70, 10.80, 10.90, 11.00]

    def test_parse_tencent_quote_short_text(self):
        """太短的文本 → IndexError → None。"""
        qd = _parse_tencent_quote("a~b~c", "600000")
        assert qd is None

    def test_parse_tencent_quote_missing_high_low(self):
        """缺少高开低收字段 → 对应字段为 None。"""
        parts = [""] * 20
        parts[3] = "10.50"
        parts[4] = "10.00"
        parts[5] = "10.20"
        parts[6] = "100000"
        parts[7] = "1000"
        text = "~".join(parts)
        qd = _parse_tencent_quote(text, "600000")
        assert qd is not None
        assert qd.high is None
        assert qd.low is None
        assert qd.change_pct is None
        assert qd.update_time is None

    def test_parse_tencent_quote_none_fields(self):
        """字段为 None/--/N/A → None。"""
        text = self._build_quote_text(**{"3": "--", "4": "N/A", "5": ""})
        qd = _parse_tencent_quote(text, "600000")
        assert qd is not None
        assert qd.last_price is None
        assert qd.pre_close is None
        assert qd.open is None

    def test_parse_tencent_quote_invalid_float(self):
        """无法转为 float 的值 → 覆盖 _f 的 except 分支。"""
        text = self._build_quote_text(**{"3": "bad_float"})
        qd = _parse_tencent_quote(text, "600000")
        assert qd is not None
        assert qd.last_price is None

    # ── _fetch_kline ──

    def test_fetch_kline_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "sh600000": {
                    "day": [
                        # format: [date, open, close, high, low, volume, amount]
                        ["2024-01-02", 10.0, 10.2, 10.5, 9.5, 100000, 1000000],
                        ["2024-01-03", 10.2, 10.8, 11.0, 10.0, 200000, 2000000],
                    ]
                }
            }
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            result = provider._fetch_kline("600000")

        assert result is not None
        assert result.data_type == DataType.OHLCV
        assert result.data.symbol == "600000"
        assert result.data.period == "daily"
        assert len(result.data.bars) == 2
        assert result.data.bars[0].date == "2024-01-02"
        assert result.data.bars[0].open == 10.0
        assert result.data.bars[0].close == 10.2
        assert result.data.bars[0].high == 10.5
        assert result.data.bars[0].low == 9.5
        assert result.data.bars[0].volume == 100000
        assert result.data.bars[0].amount == 1000000

    def test_fetch_kline_no_data(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            result = provider._fetch_kline("600000")

        assert result is None

    def test_fetch_kline_empty_series(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"sh600000": {"day": []}}}
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            result = provider._fetch_kline("600000")

        assert result is None

    def test_fetch_kline_all_bad_rows(self):
        """所有行都解析失败 → bars 为空 → 返回 None（覆盖 line 129）。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "sh600000": {
                    "day": [
                        ["bad_row", "x", "y"],  # float() 失败
                        ["another_bad"],         # IndexError / ValueError
                    ]
                }
            }
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            result = provider._fetch_kline("600000")

        assert result is None

    def test_fetch_kline_exception(self):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.side_effect = RuntimeError("timeout")

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            result = provider._fetch_kline("600000")

        assert result is None

    def test_fetch_kline_bad_row_skipped(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "sh600000": {
                    "day": [
                        ["2024-01-02", 10.0, 10.2, 10.5, 9.5, 100000, 1000000],
                        ["2024-01-03"],  # 缺少字段
                    ]
                }
            }
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            result = provider._fetch_kline("600000")

        assert result is not None
        assert len(result.data.bars) == 1

    def test_fetch_kline_fallback_keys(self):
        """检查 ks.get(symbol) 和 .get('day') 回退路径。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "600000": {
                    "day": [
                        ["2024-01-02", 10.0, 10.2, 10.5, 9.5, 100000, 1000000],
                    ]
                }
            }
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            result = provider._fetch_kline("600000")

        assert result is not None
        assert len(result.data.bars) == 1

    # ── _fetch_quote ──

    def _make_quote_response_text(self) -> str:
        text = self._build_quote_text()
        return f'v_sh600000="{text}";'

    def test_fetch_quote_success(self):
        mock_resp = MagicMock()
        mock_resp.text = self._make_quote_response_text()
        mock_resp.encoding = None
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            result = provider._fetch_quote("600000")

        assert result is not None
        assert result.data_type == DataType.QUOTE
        assert result.data.symbol == "600000"
        assert result.data.last_price == 10.50

    def test_fetch_quote_no_equals(self):
        """响应中没有 = → None。"""
        mock_resp = MagicMock()
        mock_resp.text = "invalid_response_without_equals"
        mock_resp.encoding = None
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            result = provider._fetch_quote("600000")

        assert result is None

    def test_fetch_quote_empty_text(self):
        mock_resp = MagicMock()
        mock_resp.text = ";"
        mock_resp.encoding = None
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            result = provider._fetch_quote("600000")

        assert result is None

    def test_fetch_quote_exception(self):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.side_effect = RuntimeError("timeout")

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            result = provider._fetch_quote("600000")

        assert result is None

    def test_fetch_quote_parse_failure(self):
        """解析返回 None → 最终返回 None。"""
        mock_resp = MagicMock()
        mock_resp.text = 'v="abc";'  # 太短，解析失败
        mock_resp.encoding = None
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            result = provider._fetch_quote("600000")

        assert result is None

    # ── check_available ──

    def test_check_available_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            assert provider.check_available() is True

    def test_check_available_failure(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            assert provider.check_available() is False

    def test_check_available_exception(self):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.side_effect = RuntimeError("timeout")

        with patch("datacore.equity.providers.tencent.httpx.Client", return_value=mock_client):
            provider = TencentProvider()
            assert provider.check_available() is False

    # ── fetch ──

    def test_fetch_unsupported_type(self):
        provider = TencentProvider()
        result = provider.fetch("600000", DataType.MACRO)
        assert result is None

    def test_fetch_quote_delegates(self):
        provider = TencentProvider()
        with patch.object(provider, "_fetch_quote", return_value="ok"):
            assert provider.fetch("600000", DataType.QUOTE) == "ok"

    def test_fetch_ohlcv_delegates(self):
        provider = TencentProvider()
        with patch.object(provider, "_fetch_kline", return_value="ok"):
            assert provider.fetch("600000", DataType.OHLCV) == "ok"


# ════════════════════════════════════════════════
# financial.py
# ════════════════════════════════════════════════

class TestCalcFinancialScore:
    """calc_financial_score — 财务指标评分。"""

    def test_empty_fin(self):
        score = calc_financial_score({})
        assert score["value_score"] == 0.0
        assert score["growth_score"] == 0.0
        assert score["quality_score"] == 0.0
        assert score["composite"] == 0.0

    def test_pe_and_pb(self):
        score = calc_financial_score({"pe_ttm": 15, "pb": 2})
        # pe: (30-15)/30 = 0.5 → clamp(-1,1,0.5) = 0.5
        # pb: (5-2)/5 = 0.6 → clamp(-1,1,0.6) = 0.6
        # value_score = (0.5 + 0.6) / 2 = 0.55
        assert score["value_score"] == pytest.approx(0.55)
        assert score["composite"] == pytest.approx(0.55)

    def test_pe_only(self):
        score = calc_financial_score({"pe_ttm": 20})
        # pe: (30-20)/30 = 0.333...
        # value_score = 0.333... / 2 = 0.1666...
        assert score["value_score"] == pytest.approx(0.1666666, rel=1e-3)
        assert score["composite"] == pytest.approx(0.1666666, rel=1e-3)

    def test_pb_only(self):
        score = calc_financial_score({"pb": 3})
        # pe is None/0 → skip
        # pb: (5-3)/5 = 0.4
        # value_score = 0.4 / 2 = 0.2
        assert score["value_score"] == pytest.approx(0.2)

    def test_negative_pe_skipped(self):
        score = calc_financial_score({"pe_ttm": -10, "pb": 2})
        # pe = -10, pe > 0 is False → skip pe
        # pb: (5-2)/5 = 0.6 → value_score = 0.6/2 = 0.3
        assert score["value_score"] == pytest.approx(0.3)

    def test_zero_pe_skipped(self):
        """pe 为 0（falsy）→ 跳过。"""
        score = calc_financial_score({"pe_ttm": 0, "pb": 2})
        assert score["value_score"] == pytest.approx(0.3)

    def test_pe_clamp_upper(self):
        """pe 太低 → 上限 clamp to 1。"""
        score = calc_financial_score({"pe_ttm": 1})
        # (30-1)/30 = 29/30 ≈ 0.9667 → no clamp needed
        assert score["value_score"] == pytest.approx(29 / 30 / 2)

        score = calc_financial_score({"pe_ttm": 60})
        # (30-60)/30 = -1.0 → clamp(-1,1,-1) = -1
        assert score["value_score"] == pytest.approx(-0.5)

    def test_pe_clamp_lower(self):
        score = calc_financial_score({"pe_ttm": 100})
        # (30-100)/30 = -2.33 → clamp to -1
        assert score["value_score"] == pytest.approx(-0.5)

    def test_pe_fallback(self):
        """pe_ttm 为 None 但 pe 存在 → 用 pe。"""
        score = calc_financial_score({"pe": 15, "pb": 2})
        assert score["value_score"] == pytest.approx(0.55)
