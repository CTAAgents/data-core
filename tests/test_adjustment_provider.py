"""Provider 层 adjustment 参数测试（G34）。"""
from unittest.mock import MagicMock, patch

from datacore.models.enums import DataType


class TestTencentAdjustment:
    """腾讯 Provider adjustment 参数映射。"""

    @patch("datacore.equity.providers.tencent.httpx.Client")
    def test_qfq_calls_api_with_qfq(self, mock_client_cls):
        """adjustment="qfq" → API 参数带 qfq。"""
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_client_cls.return_value = mock_inst

        # Mock 返回数据
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "sh600519": {
                    "qfqday": [["2024-01-01", "10.0", "10.5", "11.0", "9.5", "100000", "1000000"]]
                }
            }
        }
        mock_inst.get.return_value = mock_resp

        from datacore.equity.providers.tencent import TencentProvider
        tp = TencentProvider()
        tp.fetch("600519", DataType.OHLCV, {"adjustment": "qfq", "period": "daily", "days": 10})

        # 验证 API 调用参数
        call_args = mock_inst.get.call_args
        assert call_args is not None
        params = call_args[1]["params"]["param"]
        assert "qfq" in params, f"Expected qfq in params, got {params}"

    @patch("datacore.equity.providers.tencent.httpx.Client")
    def test_hfq_calls_api_with_hfq(self, mock_client_cls):
        """adjustment="hfq" → API 参数带 hfq。"""
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_client_cls.return_value = mock_inst

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "sh600519": {
                    "hfqday": [["2024-01-01", "10.0", "10.5", "11.0", "9.5", "100000", "1000000"]]
                }
            }
        }
        mock_inst.get.return_value = mock_resp

        from datacore.equity.providers.tencent import TencentProvider
        tp = TencentProvider()
        tp.fetch("600519", DataType.OHLCV, {"adjustment": "hfq", "period": "daily", "days": 10})

        call_args = mock_inst.get.call_args
        params = call_args[1]["params"]["param"]
        assert "hfq" in params, f"Expected hfq in params, got {params}"

    @patch("datacore.equity.providers.tencent.httpx.Client")
    def test_none_calls_api_without_adjust(self, mock_client_cls):
        """adjustment="none" → API 参数不带复权标记。"""
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_client_cls.return_value = mock_inst

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "sh600519": {
                    "day": [["2024-01-01", "10.0", "10.5", "11.0", "9.5", "100000", "1000000"]]
                }
            }
        }
        mock_inst.get.return_value = mock_resp

        from datacore.equity.providers.tencent import TencentProvider
        tp = TencentProvider()
        tp.fetch("600519", DataType.OHLCV, {"adjustment": "none", "period": "daily", "days": 10})

        call_args = mock_inst.get.call_args
        params = call_args[1]["params"]["param"]
        assert "qfq" not in params and "hfq" not in params, f"Expected no adjust in params, got {params}"

    @patch("datacore.equity.providers.tencent.httpx.Client")
    def test_default_is_qfq(self, mock_client_cls):
        """不传 adjustment → 默认 "qfq"。"""
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_client_cls.return_value = mock_inst

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "sh600519": {
                    "qfqday": [["2024-01-01", "10.0", "10.5", "11.0", "9.5", "100000", "1000000"]]
                }
            }
        }
        mock_inst.get.return_value = mock_resp

        from datacore.equity.providers.tencent import TencentProvider
        tp = TencentProvider()
        tp.fetch("600519", DataType.OHLCV, {"period": "daily", "days": 10})

        call_args = mock_inst.get.call_args
        params = call_args[1]["params"]["param"]
        assert "qfq" in params, f"Expected default qfq, got {params}"


class TestEastMoneyAdjustment:
    """东方财富 Provider adjustment 参数映射。"""

    @patch("datacore.equity.providers.eastmoney.httpx.Client")
    def test_qfq_calls_api_with_fqt_1(self, mock_client_cls):
        """adjustment="qfq" → fqt=1。"""
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_client_cls.return_value = mock_inst

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "klines": ["2024-01-01,10.0,10.5,11.0,9.5,100000,1000000"]
            }
        }
        mock_inst.get.return_value = mock_resp

        from datacore.equity.providers.eastmoney import EastMoneyEquityProvider
        ep = EastMoneyEquityProvider()
        ep.fetch("600519", DataType.OHLCV, {"adjustment": "qfq", "period": "daily", "days": 10})

        call_args = mock_inst.get.call_args
        fqt = call_args[1]["params"]["fqt"]
        assert fqt == 1, f"Expected fqt=1 for qfq, got {fqt}"

    @patch("datacore.equity.providers.eastmoney.httpx.Client")
    def test_hfq_calls_api_with_fqt_2(self, mock_client_cls):
        """adjustment="hfq" → fqt=2。"""
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_client_cls.return_value = mock_inst

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "klines": ["2024-01-01,10.0,10.5,11.0,9.5,100000,1000000"]
            }
        }
        mock_inst.get.return_value = mock_resp

        from datacore.equity.providers.eastmoney import EastMoneyEquityProvider
        ep = EastMoneyEquityProvider()
        ep.fetch("600519", DataType.OHLCV, {"adjustment": "hfq", "period": "daily", "days": 10})

        call_args = mock_inst.get.call_args
        fqt = call_args[1]["params"]["fqt"]
        assert fqt == 2, f"Expected fqt=2 for hfq, got {fqt}"

    @patch("datacore.equity.providers.eastmoney.httpx.Client")
    def test_none_calls_api_with_fqt_0(self, mock_client_cls):
        """adjustment="none" → fqt=0（不复权）。"""
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_client_cls.return_value = mock_inst

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "klines": ["2024-01-01,10.0,10.5,11.0,9.5,100000,1000000"]
            }
        }
        mock_inst.get.return_value = mock_resp

        from datacore.equity.providers.eastmoney import EastMoneyEquityProvider
        ep = EastMoneyEquityProvider()
        ep.fetch("600519", DataType.OHLCV, {"adjustment": "none", "period": "daily", "days": 10})

        call_args = mock_inst.get.call_args
        fqt = call_args[1]["params"]["fqt"]
        assert fqt == 0, f"Expected fqt=0 for none, got {fqt}"

    @patch("datacore.equity.providers.eastmoney.httpx.Client")
    def test_default_is_qfq(self, mock_client_cls):
        """不传 adjustment → 默认 "qfq"（fqt=1）。"""
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_client_cls.return_value = mock_inst

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "klines": ["2024-01-01,10.0,10.5,11.0,9.5,100000,1000000"]
            }
        }
        mock_inst.get.return_value = mock_resp

        from datacore.equity.providers.eastmoney import EastMoneyEquityProvider
        ep = EastMoneyEquityProvider()
        ep.fetch("600519", DataType.OHLCV, {"period": "daily", "days": 10})

        call_args = mock_inst.get.call_args
        fqt = call_args[1]["params"]["fqt"]
        assert fqt == 1, f"Expected default fqt=1, got {fqt}"


class TestApiPassthrough:
    """api.py params 透传到 Provider。"""

    @patch("datacore.equity.providers.tencent.httpx.Client")
    def test_params_adjustment_passed_to_provider(self, mock_client_cls):
        """dc.get(params={"adjustment": "none"}) → Provider 接收到 adjustment。"""
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_client_cls.return_value = mock_inst

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "sh600519": {
                    "day": [["2024-01-01", "10.0", "10.5", "11.0", "9.5", "100000", "1000000"]]
                }
            }
        }
        mock_inst.get.return_value = mock_resp

        from datacore import UnifiedDataProvider
        dc = UnifiedDataProvider()
        dc.get("600519", DataType.OHLCV, {"adjustment": "none", "period": "daily", "days": 10})

        call_args = mock_inst.get.call_args
        # 腾讯 API 用 params 关键字参数传递 param 字符串
        param_value = call_args.kwargs.get("params", {})
        # params 可能是 dict 或 call 对象
        if hasattr(param_value, "get"):
            param_str = param_value.get("param", "")
        else:
            # args[1] 是关键字参数字典
            param_str = call_args[1].get("params", {}).get("param", "") if len(call_args) > 1 else ""

        assert "qfq" not in param_str and "hfq" not in param_str, f"Expected none adjust, got {param_str}"


class TestAdjustmentNormalization:
    """adjustment 参数规范化。"""

    def test_uppercase_accepted(self):
        """大小写不敏感。"""
        from datacore.adjustment.registry import parse_adjustment_config

        config = parse_adjustment_config("QFQ")
        assert config["equity_method"] == "qfq"

        config = parse_adjustment_config("NONE")
        assert config.get("equity_method") is None