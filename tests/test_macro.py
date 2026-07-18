"""macro 模块测试。"""

import pytest
from unittest.mock import patch, MagicMock
from datacore.macro.models import MacroIndicator, MacroData
from datacore.macro.macro_provider import MacroDataProvider
from datacore.macro.providers.base import MacroDataSource
from datacore.macro.providers.eastmoney_macro import (
    EastMoneyMacroProvider,
    MACRO_INDICATOR_MAP,
)
from datacore.models.enums import DataType, MarketType, SourceGrade


# ── 基类测试 ──

class TestMacroDataSourceBase:
    """datacore.macro.providers.base"""

    def test_abstract_method_raises(self):
        """fetch_macro 是抽象方法，直接调用应抛 TypeError。"""
        with pytest.raises(TypeError):
            MacroDataSource()

    def test_concrete_subclass_must_implement_fetch_macro(self):
        """未实现 fetch_macro 的子类无法实例化。"""
        class Incomplete(MacroDataSource):
            pass
        with pytest.raises(TypeError):
            Incomplete()

    def test_check_available_default(self):
        """默认 check_available 返回 True。"""
        class Concrete(MacroDataSource):
            def fetch_macro(self, indicator=None, limit=50):
                return None
        inst = Concrete()
        assert inst.check_available() is True

    def test_name_and_priority_defaults(self):
        """name 和 priority 有默认值。"""
        class Concrete(MacroDataSource):
            def fetch_macro(self, indicator=None, limit=50):
                return None
        inst = Concrete()
        assert inst.name == ""
        assert inst.priority == 99


# ── EastMoneyMacroProvider 测试 ──

class TestEastMoneyMacroProvider:
    """datacore.macro.providers.eastmoney_macro"""

    MOCK_SUCCESS_DATA = {
        "result": {
            "data": [
                {
                    "REPORT_DATE": "2026-06-30",
                    "VALUE": 50.5,
                    "PREV_VALUE": 49.8,
                    "YOY": 1.4,
                    "MOM": 0.7,
                    "UNIT": "%",
                },
                {
                    "REPORT_DATE": "2026-05-31",
                    "VALUE": 49.8,
                    "PREV_VALUE": 50.2,
                    "YOY": -0.4,
                    "MOM": -0.2,
                    "UNIT": "%",
                },
            ]
        }
    }

    @pytest.fixture
    def provider(self):
        return EastMoneyMacroProvider()

    def test_name_and_priority(self, provider):
        assert provider.name == "eastmoney_macro"
        assert provider.priority == 1

    # ── fetch_macro 成功路径 ──

    def test_fetch_macro_pmi(self, provider):
        """成功获取 PMI 数据。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = self.MOCK_SUCCESS_DATA
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro(indicator="pmi")

        assert result is not None
        assert result.indicator == "pmi"
        assert result.total == 2
        assert len(result.data) == 2
        assert result.data[0].value == 50.5
        assert result.data[0].period == "2026-06-30"
        assert result.data[0].source == "eastmoney"
        assert result.data[0].unit == "%"
        assert result.data[1].value == 49.8

    def test_fetch_macro_lpr(self, provider):
        """成功获取 LPR 数据。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = self.MOCK_SUCCESS_DATA
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro(indicator="lpr")

        assert result is not None
        assert result.indicator == "lpr"

    def test_fetch_macro_cpi(self, provider):
        """成功获取 CPI 数据。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = self.MOCK_SUCCESS_DATA
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro(indicator="cpi")
        assert result is not None
        assert result.indicator == "cpi"

    def test_fetch_macro_default_indicator(self, provider):
        """不传 indicator 时默认使用 pmi。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = self.MOCK_SUCCESS_DATA
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()
        assert result is not None
        assert result.indicator == "pmi"

    def test_fetch_macro_invalid_indicator_falls_back_to_pmi(self, provider):
        """无效 indicator 回退到 pmi。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = self.MOCK_SUCCESS_DATA
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro(indicator="unknown_indicator")
        assert result is not None
        assert result.indicator == "pmi"

    def test_fetch_macro_limit_passed(self, provider):
        """limit 参数正确传递给请求。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = self.MOCK_SUCCESS_DATA
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value = mock_instance
            mock_instance.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            provider.fetch_macro(limit=10)

            call_kwargs = mock_instance.get.call_args[1]
            assert call_kwargs["params"]["pageSize"] == 10

    # ── fetch_macro 异常路径 ──

    def test_fetch_macro_http_error_returns_none(self, provider):
        """HTTP 请求异常返回 None。"""
        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.side_effect = Exception("Connection error")
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()
        assert result is None

    def test_fetch_macro_json_error_returns_none(self, provider):
        """JSON 解析异常返回 None。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.side_effect = ValueError("Invalid JSON")
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()
        assert result is None

    def test_fetch_macro_empty_data_returns_none(self, provider):
        """返回空数据列表时返回 None。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"result": {"data": []}}
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()
        assert result is None

    def test_fetch_macro_missing_result_returns_none(self, provider):
        """response 不含 result 字段时返回 None。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {}
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()
        assert result is None

    def test_fetch_macro_item_parse_error_skips_bad_item(self, provider):
        """单条数据解析失败时跳过，不中断整体。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "result": {
                    "data": [
                        {"REPORT_DATE": "2026-06", "VALUE": 50.5},
                        {"REPORT_DATE": "bad", "VALUE": "NOT_A_NUMBER"},
                    ]
                }
            }
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()
        assert result is not None
        assert result.total == 1
        assert len(result.data) == 1

    def test_fetch_macro_all_items_bad_returns_none(self, provider):
        """所有数据条都解析失败时返回 None。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "result": {
                    "data": [
                        {"REPORT_DATE": "bad", "VALUE": "NOT_A_NUMBER"},
                    ]
                }
            }
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()
        assert result is None

    # ── check_available ──

    def test_check_available_success(self, provider):
        """站点可达时返回 True。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.head.return_value = mock_resp
            mock_client.return_value = mock_instance

            assert provider.check_available() is True

    def test_check_available_server_error(self, provider):
        """站点返回 5xx 时返回 False。"""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 503
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.head.return_value = mock_resp
            mock_client.return_value = mock_instance

            assert provider.check_available() is False

    def test_check_available_connection_error(self, provider):
        """网络异常时返回 False。"""
        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.head.side_effect = Exception("Timeout")
            mock_client.return_value = mock_instance

            assert provider.check_available() is False


# ── MacroDataProvider 测试 ──

class TestMacroDataProvider:
    """datacore.macro.macro_provider"""

    @pytest.fixture
    def mock_macro_data(self):
        return MacroData(
            indicator="pmi",
            total=2,
            data=[
                MacroIndicator(indicator="pmi", period="2026-06", value=50.5),
                MacroIndicator(indicator="pmi", period="2026-05", value=49.8),
            ],
        )

    # ── _init_sources ──

    def test_init_sources_loads_providers(self):
        """_init_sources 按优先级加载三个数据源。"""
        provider = MacroDataProvider()
        assert len(provider.sources) == 3
        assert provider.sources[0].name == "national_bureau"
        assert provider.sources[1].name == "pboc"
        assert provider.sources[2].name == "eastmoney_macro"

    def test_init_sources_handles_import_error(self):
        """EastMoneyMacroProvider 导入失败时 sources 为空。"""
        with patch("datacore.macro.macro_provider.MacroDataProvider._init_sources",
                   side_effect=Exception("Import failed")):
            with pytest.raises(Exception):
                MacroDataProvider()

    def test_init_sources_handles_constructor_failure(self):
        """source 构造异常被吞掉，sources 不包含该 source。"""
        with patch("datacore.macro.providers.eastmoney_macro.EastMoneyMacroProvider",
                   side_effect=Exception("Constructor failed")):
            provider = MacroDataProvider()
        # 前两个 source（national_bureau, pboc）正常加载
        assert len(provider.sources) == 2
        assert provider.sources[0].name == "national_bureau"
        assert provider.sources[1].name == "pboc"

    # ── get ──

    def test_get_success(self, provider_with_mock, mock_macro_data):
        """get 成功路径：返回 DataPayload 包含正确字段。"""
        provider, mock_src = provider_with_mock
        mock_src.fetch_macro.return_value = mock_macro_data

        result = provider.get(indicator="pmi")

        assert result is not None
        assert result.symbol == "pmi"
        assert result.data_type == DataType.MACRO
        assert result.market == MarketType.FUTURES
        assert result.source == "eastmoney_macro"
        assert result.grade == SourceGrade.CACHED
        assert result.data is mock_macro_data
        assert len(result.errors) == 0

    def test_get_without_indicator(self, provider_with_mock, mock_macro_data):
        """不带 indicator 时 symbol 为 *。"""
        provider, mock_src = provider_with_mock
        mock_src.fetch_macro.return_value = mock_macro_data

        result = provider.get()

        assert result.symbol == "*"

    def test_get_with_params(self, provider_with_mock, mock_macro_data):
        """params 中的 limit 传递给 fetch_macro。"""
        provider, mock_src = provider_with_mock
        mock_src.fetch_macro.return_value = mock_macro_data

        provider.get(indicator="pmi", params={"limit": 20})

        mock_src.fetch_macro.assert_called_once_with(indicator="pmi", limit=20)

    def test_get_default_params(self, provider_with_mock, mock_macro_data):
        """未传 params 时使用默认 limit=50。"""
        provider, mock_src = provider_with_mock
        mock_src.fetch_macro.return_value = mock_macro_data

        provider.get(indicator="pmi")

        mock_src.fetch_macro.assert_called_once_with(indicator="pmi", limit=50)

    def test_get_source_not_available_skips(self, provider_with_mock):
        """source check_available 返回 False 时跳过。"""
        provider, mock_src = provider_with_mock
        mock_src.check_available.return_value = False

        result = provider.get()

        mock_src.fetch_macro.assert_not_called()
        assert result.grade == SourceGrade.UNAVAILABLE

    def test_get_source_exception_continues(self, provider_with_mock):
        """source 抛出异常时继续下一个。"""
        provider, mock_src = provider_with_mock
        mock_src.fetch_macro.side_effect = Exception("Fetch error")

        result = provider.get()

        assert result.grade == SourceGrade.UNAVAILABLE

    def test_get_source_returns_none_continues(self, provider_with_mock):
        """source 返回 None 时继续下一个。"""
        provider, mock_src = provider_with_mock
        mock_src.fetch_macro.return_value = None

        result = provider.get()

        assert result.grade == SourceGrade.UNAVAILABLE

    def test_get_all_unavailable(self, provider_with_mock):
        """所有 source 不可用时返回 UNAVAILABLE。"""
        provider, mock_src = provider_with_mock
        mock_src.check_available.return_value = False

        result = provider.get(indicator="pmi")

        assert result.grade == SourceGrade.UNAVAILABLE
        assert result.data.indicator == "pmi"
        assert "所有宏观数据源不可用" in result.errors

    def test_get_returns_data_payload_available(self, provider_with_mock, mock_macro_data):
        """成功获取时 available 为 True。"""
        provider, mock_src = provider_with_mock
        mock_src.fetch_macro.return_value = mock_macro_data

        result = provider.get()

        assert result.available is True

    def test_get_data_empty_continues(self, provider_with_mock):
        """source 返回 data 为空列表时继续下一个。"""
        provider, mock_src = provider_with_mock
        empty_data = MacroData(indicator="pmi", total=0, data=[])
        mock_src.fetch_macro.return_value = empty_data

        result = provider.get()

        assert result.grade == SourceGrade.UNAVAILABLE

    @pytest.fixture
    def provider_with_mock(self):
        """创建一个 MacroDataProvider，其 sources 被替换为一个 mock source。"""
        provider = MacroDataProvider()
        mock_src = MagicMock()
        mock_src.name = "eastmoney_macro"
        mock_src.priority = 1
        mock_src.check_available.return_value = True
        provider.sources = [mock_src]
        return provider, mock_src
