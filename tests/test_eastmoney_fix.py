"""东方财富期货 secid 修复测试（G33）。"""
from unittest.mock import patch, MagicMock
import httpx

from datacore.futures.providers.eastmoney import EastMoneyFuturesProvider


def _mock_response(klinedata=None):
    """构造 mock httpx 响应。"""
    resp = MagicMock()
    resp.json.return_value = {
        "data": {"klinedata": klinedata or []} if klinedata is not None else None
    }
    return resp


class TestSecidDetection:
    """期货 secid 探测：遍历候选直到返回数据。"""

    @patch("datacore.futures.providers.eastmoney.httpx.Client")
    def test_first_secid_works(self, mock_client_cls):
        """115.RB9999 返回数据时直接采用。"""
        klinedata = [
            {"f51": "2026-07-01", "f52": "3500", "f53": "3550", "f54": "3490",
             "f55": "3520", "f56": "100000", "f57": "350000000", "f58": "0", "f59": "0", "f60": "0", "f61": "0"}
        ]
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_inst.get.return_value = _mock_response(klinedata)
        mock_client_cls.return_value = mock_inst

        p = EastMoneyFuturesProvider()
        result = p.fetch_kline("RB", "daily", 5)
        assert result is not None
        assert len(result.bars) == 1
        assert result.bars[0].close == 3520.0
        # 验证调用参数
        call_args = mock_inst.get.call_args
        assert call_args[1]["params"]["secid"] == "115.RB9999"

    @patch("datacore.futures.providers.eastmoney.httpx.Client")
    def test_fallback_to_second_secid(self, mock_client_cls):
        """第一个 secid 返回空，降级到第二个。"""
        klinedata = [
            {"f51": "2026-07-01", "f52": "3500", "f53": "3550", "f54": "3490",
             "f55": "3520", "f56": "100000", "f57": "350000000", "f58": "0", "f59": "0", "f60": "0", "f61": "0"}
        ]

        # 第一次返回空，第二次返回数据
        responses = [_mock_response([]), _mock_response(klinedata)]
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_inst.get.side_effect = responses
        mock_client_cls.return_value = mock_inst

        p = EastMoneyFuturesProvider()
        result = p.fetch_kline("RB", "daily", 5)
        assert result is not None
        assert len(result.bars) == 1
        # 验证第一次调用 secid="115.RB9999"，第二次 secid="113.RB9999"
        assert mock_inst.get.call_count == 2
        first_secid = mock_inst.get.call_args_list[0][1]["params"]["secid"]
        second_secid = mock_inst.get.call_args_list[1][1]["params"]["secid"]
        assert first_secid == "115.RB9999"
        assert second_secid == "113.RB9999"

    @patch("datacore.futures.providers.eastmoney.httpx.Client")
    def test_all_secids_empty_returns_none(self, mock_client_cls):
        """所有候选 secid 都返回空，返回 None。"""
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        # 每次都返回空 klinedata
        mock_inst.get.return_value = _mock_response([])
        mock_client_cls.return_value = mock_inst

        p = EastMoneyFuturesProvider()
        result = p.fetch_kline("RB", "daily", 5)
        assert result is None

    @patch("datacore.futures.providers.eastmoney.httpx.Client")
    def test_network_exception_returns_none(self, mock_client_cls):
        """网络异常时返回 None。"""
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_inst.get.side_effect = httpx.RequestError("timeout")
        mock_client_cls.return_value = mock_inst

        p = EastMoneyFuturesProvider()
        result = p.fetch_kline("RB", "daily", 5)
        assert result is None

    @patch("datacore.futures.providers.eastmoney.httpx.Client")
    def test_check_available(self, mock_client_cls):
        """check_available 通过 head 请求检测。"""
        mock_inst = MagicMock()
        mock_inst.__enter__.return_value = mock_inst
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_inst.head.return_value = mock_resp
        mock_client_cls.return_value = mock_inst

        p = EastMoneyFuturesProvider()
        assert p.check_available() is True
