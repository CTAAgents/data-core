"""宏观数据源的 mock 测试。"""
from unittest.mock import patch, MagicMock
from datacore.macro.models import MacroData


class TestNationalBureauProvider:
    """datacore.macro.providers.national_bureau"""

    def test_name_and_priority(self):
        from datacore.macro.providers.national_bureau import NationalBureauProvider
        provider = NationalBureauProvider()
        assert provider.name == "national_bureau"
        assert provider.priority == 0

    def test_fetch_macro_cpi(self):
        from datacore.macro.providers.national_bureau import NationalBureauProvider
        provider = NationalBureauProvider()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "returndata": {
                "datanodes": [
                    {"code": "2026Q1", "data": {"data": 101.5}},
                    {"code": "2025Q4", "data": {"data": 101.2}},
                ]
            }
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.post.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro("cpi", limit=5)

        assert result is not None
        assert result.indicator == "cpi"
        assert len(result.data) == 2
        assert result.data[0].value == 101.5
        assert result.data[1].value == 101.2
        assert result.data[0].period == "2026Q1"

    def test_fetch_macro_default_indicator(self):
        """不传 indicator 时默认使用 cpi。"""
        from datacore.macro.providers.national_bureau import NationalBureauProvider
        provider = NationalBureauProvider()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "returndata": {
                "datanodes": [
                    {"code": "2026Q1", "data": {"data": 101.5}},
                ]
            }
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.post.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()

        assert result is not None
        assert result.indicator == "cpi"

    def test_fetch_macro_invalid_indicator_falls_back_to_cpi(self):
        """无效 indicator 回退到 cpi。"""
        from datacore.macro.providers.national_bureau import NationalBureauProvider
        provider = NationalBureauProvider()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "returndata": {
                "datanodes": [
                    {"code": "2026Q1", "data": {"data": 101.5}},
                ]
            }
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.post.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro(indicator="unknown")

        assert result is not None
        assert result.indicator == "cpi"

    def test_fetch_macro_api_error_returns_none(self):
        """HTTP 请求异常返回 None。"""
        from datacore.macro.providers.national_bureau import NationalBureauProvider
        provider = NationalBureauProvider()

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.post.side_effect = Exception("Connection error")
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()

        assert result is None

    def test_fetch_macro_empty_data_returns_none(self):
        """返回空数据列表时返回 None。"""
        from datacore.macro.providers.national_bureau import NationalBureauProvider
        provider = NationalBureauProvider()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"returndata": {"datanodes": []}}

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.post.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()

        assert result is None

    def test_fetch_macro_missing_returndata_returns_none(self):
        """response 不含 returndata 字段时返回 None。"""
        from datacore.macro.providers.national_bureau import NationalBureauProvider
        provider = NationalBureauProvider()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {}

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.post.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()

        assert result is None

    def test_fetch_macro_item_parse_error_skips_bad_item(self):
        """单条数据解析失败时跳过，不中断整体。"""
        from datacore.macro.providers.national_bureau import NationalBureauProvider
        provider = NationalBureauProvider()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "returndata": {
                "datanodes": [
                    {"code": "2026Q1", "data": {"data": 101.5}},
                    {"code": "bad", "data": {"data": "NOT_A_NUMBER"}},
                ]
            }
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.post.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro(limit=5)

        assert result is not None
        assert len(result.data) == 1

    def test_fetch_macro_all_items_bad_returns_none(self):
        """所有数据条都解析失败时返回 None。"""
        from datacore.macro.providers.national_bureau import NationalBureauProvider
        provider = NationalBureauProvider()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "returndata": {
                "datanodes": [
                    {"code": "bad", "data": {"data": "NOT_A_NUMBER"}},
                ]
            }
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.post.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()

        assert result is None

    def test_check_available_success(self):
        from datacore.macro.providers.national_bureau import NationalBureauProvider
        provider = NationalBureauProvider()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.head.return_value = mock_resp
            mock_client.return_value = mock_instance

            assert provider.check_available() is True

    def test_check_available_server_error(self):
        from datacore.macro.providers.national_bureau import NationalBureauProvider
        provider = NationalBureauProvider()

        mock_resp = MagicMock()
        mock_resp.status_code = 503

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.head.return_value = mock_resp
            mock_client.return_value = mock_instance

            assert provider.check_available() is False

    def test_check_available_connection_error(self):
        from datacore.macro.providers.national_bureau import NationalBureauProvider
        provider = NationalBureauProvider()

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.head.side_effect = Exception("Timeout")
            mock_client.return_value = mock_instance

            assert provider.check_available() is False


class TestPboCProvider:
    """datacore.macro.providers.pboc"""

    def test_name_and_priority(self):
        from datacore.macro.providers.pboc import PboCProvider
        provider = PboCProvider()
        assert provider.name == "pboc"
        assert provider.priority == 1

    def test_fetch_macro_lpr(self):
        from datacore.macro.providers.pboc import PboCProvider
        provider = PboCProvider()

        mock_resp = MagicMock()
        mock_resp.text = "2026年7月 LPR 3.45% 2026年6月 LPR 3.55%"

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro("lpr", limit=5)

        assert result is not None
        assert result.indicator == "lpr"
        assert len(result.data) == 2
        assert result.data[0].value == 3.45
        assert result.data[0].unit == "%"
        assert result.data[0].source == "pboc"

    def test_fetch_macro_m2(self):
        from datacore.macro.providers.pboc import PboCProvider
        provider = PboCProvider()

        mock_resp = MagicMock()
        mock_resp.text = "2026年6月 M2同比增长7.5%"

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro("m2", limit=5)

        assert result is not None
        assert result.indicator == "m2"
        assert len(result.data) == 1
        assert result.data[0].value == 7.5
        # 日期正则中 day 组可选，无 day 时只返回年份
        assert result.data[0].period == "2026"

    def test_fetch_macro_default_indicator(self):
        """不传 indicator 时默认使用 lpr。"""
        from datacore.macro.providers.pboc import PboCProvider
        provider = PboCProvider()

        mock_resp = MagicMock()
        mock_resp.text = "2026年7月 LPR 3.45%"

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()

        assert result is not None
        assert result.indicator == "lpr"

    def test_fetch_macro_invalid_indicator_falls_back_to_lpr(self):
        """无效 indicator 回退到 lpr。"""
        from datacore.macro.providers.pboc import PboCProvider
        provider = PboCProvider()

        mock_resp = MagicMock()
        mock_resp.text = "2026年7月 LPR 3.45%"

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro(indicator="unknown")

        assert result is not None
        assert result.indicator == "lpr"

    def test_fetch_macro_http_error_returns_none(self):
        """HTTP 请求异常返回 None。"""
        from datacore.macro.providers.pboc import PboCProvider
        provider = PboCProvider()

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.side_effect = Exception("Connection error")
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()

        assert result is None

    def test_fetch_macro_empty_text_returns_none(self):
        """返回空文本时返回 None。"""
        from datacore.macro.providers.pboc import PboCProvider
        provider = PboCProvider()

        mock_resp = MagicMock()
        mock_resp.text = ""

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()

        assert result is None

    def test_fetch_macro_no_dates_or_values_returns_none(self):
        """HTML 中无日期或数值时返回 None。"""
        from datacore.macro.providers.pboc import PboCProvider
        provider = PboCProvider()

        mock_resp = MagicMock()
        mock_resp.text = "<html>no data here</html>"

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.get.return_value = mock_resp
            mock_client.return_value = mock_instance

            result = provider.fetch_macro()

        assert result is None

    def test_check_available_success(self):
        from datacore.macro.providers.pboc import PboCProvider
        provider = PboCProvider()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.head.return_value = mock_resp
            mock_client.return_value = mock_instance

            assert provider.check_available() is True

    def test_check_available_server_error(self):
        from datacore.macro.providers.pboc import PboCProvider
        provider = PboCProvider()

        mock_resp = MagicMock()
        mock_resp.status_code = 503

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.head.return_value = mock_resp
            mock_client.return_value = mock_instance

            assert provider.check_available() is False

    def test_check_available_connection_error(self):
        from datacore.macro.providers.pboc import PboCProvider
        provider = PboCProvider()

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.head.side_effect = Exception("Timeout")
            mock_client.return_value = mock_instance

            assert provider.check_available() is False
