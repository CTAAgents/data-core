"""国信证券数据源 mock 测试。"""


class TestGuosenProvider:
    def test_check_available_no_key(self, mocker):
        from datacore.equity.providers.guosen import GuosenProvider
        mocker.patch("datacore.equity.providers.guosen.get_config")
        config = mocker.Mock()
        config.guosen_api_key = None
        config.guosen_url = "https://api.guosen.com.cn/"
        config.guosen_timeout = 5
        from datacore.equity.providers import guosen as mod
        mod.get_config = mocker.Mock(return_value=config)
        p = GuosenProvider()
        assert p.check_available() is False

    def test_check_available_with_key(self, mocker):
        from datacore.equity.providers.guosen import GuosenProvider
        config = mocker.Mock()
        config.guosen_api_key = "test_key"
        config.guosen_url = "https://api.guosen.com.cn/"
        config.guosen_timeout = 5
        from datacore.equity.providers import guosen as mod
        mod.get_config = mocker.Mock(return_value=config)
        mock_resp = mocker.Mock()
        mock_resp.status_code = 200
        mc = mocker.patch("httpx.Client")
        mc.return_value.__enter__.return_value.get.return_value = mock_resp
        p = GuosenProvider()
        assert p.check_available() is True

    def test_fetch_kline_no_key(self, mocker):
        from datacore.equity.providers.guosen import GuosenProvider
        config = mocker.Mock()
        config.guosen_api_key = None
        config.guosen_url = "https://api.guosen.com.cn/"
        config.guosen_timeout = 5
        p = GuosenProvider()
        p.api_key = None
        from datacore.models.enums import DataType
        result = p.fetch("600519", DataType.OHLCV)
        assert result is None

    def test_fetch_kline_with_key(self, mocker):
        from datacore.equity.providers.guosen import GuosenProvider
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {
            "success": True,
            "data": [
                {"date": "2026-01-01", "open": 3500, "high": 3600, "low": 3400, "close": 3550, "volume": 1000, "amount": 3500000},
            ],
        }
        mc = mocker.patch("httpx.Client")
        mc.return_value.__enter__.return_value.get.return_value = mock_resp
        p = GuosenProvider()
        p.api_key = "test_key"
        p.base_url = "https://api.guosen.com.cn/"
        p.timeout = 5
        from datacore.models.enums import DataType
        result = p.fetch("600519", DataType.OHLCV)
        assert result is not None
        assert result.source == "guosen"

    def test_fetch_unknown_type(self, mocker):
        from datacore.equity.providers.guosen import GuosenProvider
        p = GuosenProvider()
        p.api_key = "test_key"
        p.base_url = "https://api.guosen.com.cn/"
        p.timeout = 5
        result = p.fetch("600519", "unknown_type")
        assert result is None

    def test_fetch_financial(self, mocker):
        from datacore.equity.providers.guosen import GuosenProvider
        p = GuosenProvider()
        p.api_key = "test_key"
        p.base_url = "https://api.guosen.com.cn/"
        p.timeout = 5
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {
            "success": True,
            "data": {"pe": 15.0, "pb": 2.0},
        }
        mc = mocker.patch("httpx.Client")
        mc.return_value.__enter__.return_value.get.return_value = mock_resp
        from datacore.models.enums import DataType
        result = p.fetch("600519", DataType.FINANCIAL)
        assert result is not None
        assert result.data_type == DataType.FINANCIAL

    def test_fetch_quote(self, mocker):
        from datacore.equity.providers.guosen import GuosenProvider
        p = GuosenProvider()
        p.api_key = "test_key"
        p.base_url = "https://api.guosen.com.cn/"
        p.timeout = 5
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {
            "success": True,
            "data": {"last_price": 1500, "open": 1480, "high": 1510, "low": 1470, "volume": 10000, "amount": 1500000},
        }
        mc = mocker.patch("httpx.Client")
        mc.return_value.__enter__.return_value.get.return_value = mock_resp
        from datacore.models.enums import DataType
        result = p.fetch("600519", DataType.QUOTE)
        assert result is not None
        assert result.data_type == DataType.QUOTE
