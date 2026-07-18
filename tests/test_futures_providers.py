"""期货基本面数据源 mock 测试。"""
from unittest.mock import patch, MagicMock


class TestExchangeApiProvider:
    def test_get_exchange(self):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider
        p = ExchangeApiProvider()
        assert p._get_exchange("RB") == "SHFE"
        assert p._get_exchange("TA") == "CZCE"
        assert p._get_exchange("M") == "DCE"
        assert p._get_exchange("ZZZ") is None

    @patch("datacore.futures.providers.exchange_api.httpx.Client")
    def test_check_available(self, mock_client):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider
        p = ExchangeApiProvider()
        mock_inst = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_inst.__enter__.return_value = mock_inst
        mock_inst.head.return_value = mock_resp
        mock_client.return_value = mock_inst
        assert p.check_available() is True

    @patch("datacore.futures.providers.exchange_api.httpx.Client")
    def test_check_available_fail(self, mock_client):
        from datacore.futures.providers.exchange_api import ExchangeApiProvider
        p = ExchangeApiProvider()
        mock_client.side_effect = Exception("fail")
        assert p.check_available() is False


class TestShengYiSheProvider:
    @patch("datacore.futures.providers.shengyishe.httpx.Client")
    def test_fetch_basis_known_symbol(self, mock_client):
        from datacore.futures.providers.shengyishe import ShengYiSheProvider
        p = ShengYiSheProvider()
        mock_inst = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "<html>现货价格 3500 元/吨</html>"
        mock_inst.__enter__.return_value = mock_inst
        mock_inst.get.return_value = mock_resp
        mock_client.return_value = mock_inst
        result = p.fetch_basis("RB")
        assert result is not None
        assert result.spot_price == 3500
        assert result.spot_source == "shengyishe"

    def test_fetch_basis_unknown_symbol(self):
        from datacore.futures.providers.shengyishe import ShengYiSheProvider
        p = ShengYiSheProvider()
        result = p.fetch_basis("ZZZ")
        assert result is None

    @patch("datacore.futures.providers.shengyishe.httpx.Client")
    def test_fetch_basis_http_fail(self, mock_client):
        from datacore.futures.providers.shengyishe import ShengYiSheProvider
        p = ShengYiSheProvider()
        mock_client.side_effect = Exception("timeout")
        result = p.fetch_basis("RB")
        assert result is None
