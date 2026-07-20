"""外部依赖模块的 mock 测试。

通过 mock 外部库（akshare / httpx / pdfplumber / PyPDF2 / pandas 等），
为 datacore.collectors 下的可选依赖模块补齐异常分支与正常分支覆盖。
"""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import MagicMock, patch

from datacore.collectors.local_doc import PdfExcelReader
from datacore.collectors.open_source import AKShareClient
from datacore.collectors.search import TavilyClient
from datacore.collectors.web_crawl import WebCollectorClient


# ============================================================
#  Helpers
# ============================================================

def _make_module(**attrs: Any) -> Any:
    """构造一个可作为 sys.modules 项使用的伪模块。"""
    mod = type(sys)("fake_module")
    for name, value in attrs.items():
        setattr(mod, name, value)
    return mod


def _fake_dataframe(records: list[dict[str, Any]]) -> Any:
    """构造具有 pandas DataFrame 最小 API 的伪对象。"""
    df = MagicMock()
    df.to_dict.return_value = records
    df.columns = list(records[0].keys()) if records else []
    df.__len__ = MagicMock(return_value=len(records))
    return df


# ============================================================
#  AKShareClient
# ============================================================

class TestAKShareClientMock:
    """AKShareClient 外部依赖 mock 测试。"""

    def test_check_available_true(self):
        """akshare 可导入时返回 True。"""
        fake_ak = _make_module()
        client = AKShareClient()
        with patch.dict(sys.modules, {"akshare": fake_ak}):
            assert client.check_available() is True

    def test_check_available_false(self):
        """akshare 不可导入时返回 False。"""
        client = AKShareClient()
        with patch.dict(sys.modules, {"akshare": None}):
            assert client.check_available() is False

    def test_get_akshare_caches_module(self):
        """_get_akshare 会缓存模块实例。"""
        fake_ak = _make_module()
        client = AKShareClient()
        with patch.dict(sys.modules, {"akshare": fake_ak}):
            first = client._get_akshare()
            second = client._get_akshare()
            assert first is fake_ak
            assert second is first

    def test_fetch_when_dependency_missing(self):
        """未安装 akshare 时 fetch 返回空结果。"""
        client = AKShareClient()
        with patch.dict(sys.modules, {"akshare": None}):
            result = client.fetch("stock_zh_a_hist")
        assert result["success"] is False
        assert "AKShare 未安装" in result["error"]

    def test_fetch_success_with_dataframe(self):
        """返回 DataFrame 时转换为 records 列表。"""
        records = [{"open": 1.0, "close": 2.0}]
        fake_func = MagicMock(return_value=_fake_dataframe(records))
        fake_ak = _make_module(stock_zh_a_hist=fake_func)
        client = AKShareClient()
        with patch.dict(sys.modules, {"akshare": fake_ak}):
            result = client.fetch("stock_zh_a_hist", symbol="000001")
        assert result["success"] is True
        assert result["data"] == records
        assert result["row_count"] == 1
        fake_func.assert_called_once_with(symbol="000001")

    def test_fetch_success_with_list(self):
        """返回 list 时直接作为 data。"""
        data = ["a", "b"]
        fake_ak = _make_module(some_api=MagicMock(return_value=data))
        client = AKShareClient()
        with patch.dict(sys.modules, {"akshare": fake_ak}):
            result = client.fetch("some_api")
        assert result["success"] is True
        assert result["data"] == data
        assert result["row_count"] == 2

    def test_fetch_attribute_error(self):
        """接口不存在时返回 AttributeError 错误。"""
        fake_ak = _make_module()
        client = AKShareClient()
        with patch.dict(sys.modules, {"akshare": fake_ak}):
            result = client.fetch("missing_api")
        assert result["success"] is False
        assert result["error_type"] == "AttributeError"
        assert "missing_api" in result["error"]

    def test_fetch_generic_exception(self):
        """API 调用抛异常时返回错误信息。"""
        fake_ak = _make_module(broken_api=MagicMock(side_effect=ValueError("boom")))
        client = AKShareClient()
        with patch.dict(sys.modules, {"akshare": fake_ak}):
            result = client.fetch("broken_api")
        assert result["success"] is False
        assert result["error_type"] == "ValueError"
        assert "boom" in result["error"]

    def test_get_stock_hist(self):
        """get_stock_hist 拼装参数并调用 fetch。"""
        records = [{"close": 10.0}]
        fake_func = MagicMock(return_value=_fake_dataframe(records))
        fake_ak = _make_module(stock_zh_a_hist=fake_func)
        client = AKShareClient()
        with patch.dict(sys.modules, {"akshare": fake_ak}):
            result = client.get_stock_hist(
                "000001", period="weekly", adjust="qfq",
                start_date="20240101", end_date="20241231",
            )
        assert result["success"] is True
        fake_func.assert_called_once_with(
            symbol="000001",
            period="weekly",
            adjust="qfq",
            start_date="20240101",
            end_date="20241231",
        )

    def test_get_futures_hist(self):
        """get_futures_hist 拼装参数并调用 fetch。"""
        records = [{"close": 20.0}]
        fake_func = MagicMock(return_value=_fake_dataframe(records))
        fake_ak = _make_module(futures_hist=fake_func)
        client = AKShareClient()
        with patch.dict(sys.modules, {"akshare": fake_ak}):
            result = client.get_futures_hist(
                "RB2501", period="daily",
                start_date="20240101", end_date="20241231",
            )
        assert result["success"] is True
        fake_func.assert_called_once_with(
            symbol="RB2501",
            period="daily",
            start_date="20240101",
            end_date="20241231",
        )


# ============================================================
#  TavilyClient
# ============================================================

class TestTavilyClientMock:
    """TavilyClient 外部依赖 mock 测试。"""

    def _fake_httpx(self, response: Any) -> Any:
        """构造一个返回指定 response 的伪 httpx 模块。"""
        client_instance = MagicMock()
        client_instance.post.return_value = response
        return _make_module(Client=MagicMock(return_value=client_instance))

    def test_check_available_true(self):
        """API Key 与 httpx 均存在时返回 True。"""
        fake_httpx = _make_module()
        client = TavilyClient(api_key="test-key")
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            assert client.check_available() is True

    def test_check_available_false_no_key(self):
        """缺少 API Key 时返回 False。"""
        client = TavilyClient(api_key="")
        assert client.check_available() is False

    def test_check_available_false_no_httpx(self):
        """httpx 不可导入时返回 False。"""
        client = TavilyClient(api_key="test-key")
        with patch.dict(sys.modules, {"httpx": None}):
            assert client.check_available() is False

    def test_get_client_caches_instance(self):
        """_get_client 缓存 httpx.Client 实例。"""
        response = MagicMock(status_code=200, json=MagicMock(return_value={"results": []}))
        fake_httpx = self._fake_httpx(response)
        client = TavilyClient(api_key="test-key")
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            first = client._get_client()
            second = client._get_client()
            assert first is second
            fake_httpx.Client.assert_called_once_with(
                base_url="https://api.tavily.com", timeout=30.0
            )

    def test_fetch_success(self):
        """搜索返回 200 时解析结果。"""
        payload = {
            "results": [{"title": "t1"}],
            "answer": "ans",
            "images": ["img1"],
        }
        response = MagicMock(status_code=200, json=MagicMock(return_value=payload))
        fake_httpx = self._fake_httpx(response)
        client = TavilyClient(api_key="test-key")
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.fetch("query", max_results=3, include_answer=False)
        assert result["success"] is True
        assert result["result_count"] == 1
        assert result["answer"] == "ans"
        assert result["images"] == ["img1"]

    def test_fetch_http_error(self):
        """搜索返回非 200 时返回 HTTPError。"""
        response = MagicMock(status_code=500, text="server error")
        fake_httpx = self._fake_httpx(response)
        client = TavilyClient(api_key="test-key")
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.fetch("query")
        assert result["success"] is False
        assert result["error_type"] == "HTTPError"
        assert "500" in result["error"]

    def test_fetch_exception(self):
        """请求抛异常时返回错误。"""
        client_instance = MagicMock()
        client_instance.post.side_effect = TimeoutError("timeout")
        fake_httpx = _make_module(Client=MagicMock(return_value=client_instance))
        client = TavilyClient(api_key="test-key")
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.fetch("query")
        assert result["success"] is False
        assert result["error_type"] == "TimeoutError"

    def test_fetch_not_available(self):
        """不可用时直接返回错误。"""
        client = TavilyClient(api_key="")
        result = client.fetch("query")
        assert result["success"] is False
        assert "不可用" in result["error"]

    def test_search(self):
        """search 便捷方法转发到 fetch。"""
        response = MagicMock(status_code=200, json=MagicMock(return_value={"results": []}))
        fake_httpx = self._fake_httpx(response)
        client = TavilyClient(api_key="test-key")
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.search("q", max_results=2, include_answer=False)
        assert result["success"] is True

    def test_close(self):
        """close 关闭并清空内部客户端。"""
        client = TavilyClient(api_key="test-key")
        inner = MagicMock()
        client._client = inner
        client.close()
        inner.close.assert_called_once()
        assert client._client is None

    def test_context_manager_exit_closes(self):
        """上下文管理器退出时调用 close。"""
        response = MagicMock(status_code=200, json=MagicMock(return_value={"results": []}))
        fake_httpx = self._fake_httpx(response)
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            with TavilyClient(api_key="test-key") as client:
                client.fetch("q")
                inner = client._client
            assert client._client is None
            inner.close.assert_called_once()


# ============================================================
#  WebCollectorClient
# ============================================================

class TestWebCollectorClientMock:
    """WebCollectorClient 外部依赖 mock 测试。"""

    def _fake_httpx(self, response: Any) -> Any:
        client_instance = MagicMock()
        client_instance.request.return_value = response
        return _make_module(Client=MagicMock(return_value=client_instance))

    def test_check_available_true(self):
        """httpx 可导入时返回 True。"""
        fake_httpx = _make_module()
        client = WebCollectorClient()
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            assert client.check_available() is True

    def test_check_available_false(self):
        """httpx 不可导入时返回 False。"""
        client = WebCollectorClient()
        with patch.dict(sys.modules, {"httpx": None}):
            assert client.check_available() is False

    def test_get_client_caches_instance(self):
        """_get_client 缓存 httpx.Client 实例。"""
        response = MagicMock(status_code=200, text="ok", headers={})
        fake_httpx = self._fake_httpx(response)
        client = WebCollectorClient(timeout=5.0)
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            first = client._get_client()
            second = client._get_client()
            assert first is second
            fake_httpx.Client.assert_called_once_with(
                timeout=5.0,
                headers=client.headers,
                follow_redirects=True,
            )

    def test_fetch_success(self):
        """正常抓取网页。"""
        response = MagicMock(status_code=200, text="<html></html>", headers={"ct": "text/html"})
        fake_httpx = self._fake_httpx(response)
        client = WebCollectorClient()
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.fetch("http://example.com", method="GET")
        assert result["success"] is True
        assert result["status_code"] == 200
        assert result["content"] == "<html></html>"

    def test_fetch_unavailable(self):
        """httpx 不可用时返回错误。"""
        client = WebCollectorClient()
        with patch.dict(sys.modules, {"httpx": None}):
            result = client.fetch("http://example.com")
        assert result["success"] is False
        assert "httpx 不可用" in result["error"]

    def test_fetch_exception(self):
        """请求抛异常时返回错误。"""
        client_instance = MagicMock()
        client_instance.request.side_effect = ConnectionError("refused")
        fake_httpx = _make_module(Client=MagicMock(return_value=client_instance))
        client = WebCollectorClient()
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.fetch("http://example.com")
        assert result["success"] is False
        assert result["error_type"] == "ConnectionError"

    def test_fetch_json_success(self):
        """fetch_json 成功解析 JSON。"""
        response = MagicMock(status_code=200, text='{"a": 1}', headers={})
        fake_httpx = self._fake_httpx(response)
        client = WebCollectorClient()
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.fetch_json("http://api.example.com")
        assert result["success"] is True
        assert result["data"] == {"a": 1}

    def test_fetch_json_parse_error(self):
        """fetch_json 解析失败时返回 JSONDecodeError。"""
        response = MagicMock(status_code=200, text="not json", headers={})
        fake_httpx = self._fake_httpx(response)
        client = WebCollectorClient()
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.fetch_json("http://api.example.com")
        assert result["success"] is False
        assert result["error_type"] == "JSONDecodeError"

    def test_fetch_json_propagates_failure(self):
        """fetch 失败时 fetch_json 直接返回失败结果。"""
        client = WebCollectorClient()
        with patch.dict(sys.modules, {"httpx": None}):
            result = client.fetch_json("http://api.example.com")
        assert result["success"] is False
        assert "httpx 不可用" in result["error"]

    def test_close(self):
        """close 关闭并清空内部客户端。"""
        client = WebCollectorClient()
        inner = MagicMock()
        client._client = inner
        client.close()
        inner.close.assert_called_once()
        assert client._client is None

    def test_context_manager_exit_closes(self):
        """上下文管理器退出时调用 close。"""
        response = MagicMock(status_code=200, text="ok", headers={})
        fake_httpx = self._fake_httpx(response)
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            with WebCollectorClient() as client:
                client.fetch("http://example.com")
                inner = client._client
            assert client._client is None
            inner.close.assert_called_once()


# ============================================================
#  PdfExcelReader
# ============================================================

class TestPdfExcelReaderMock:
    """PdfExcelReader 外部依赖 mock 测试。"""

    def _fake_pandas(self, df: Any) -> Any:
        """构造一个返回指定 DataFrame 的伪 pandas 模块。"""
        mod = type(sys)("pandas")
        mod.read_csv = MagicMock(return_value=df)
        mod.read_excel = MagicMock(return_value=df)
        mod.ExcelFile = MagicMock(return_value=MagicMock(sheet_names=["Sheet1", "Sheet2"]))
        return mod

    def test_check_available_true(self):
        """pandas 可导入时返回 True。"""
        fake_pd = type(sys)("pandas")
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pandas": fake_pd}):
            assert reader.check_available() is True

    def test_check_available_false(self):
        """pandas 不可导入时返回 False。"""
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pandas": None}):
            assert reader.check_available() is False

    def test_check_pdf_available_pdfplumber(self):
        """仅有 pdfplumber 时 PDF 可用。"""
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pdfplumber": _make_module(), "PyPDF2": None}):
            assert reader._check_pdf_available() is True

    def test_check_pdf_available_pypdf2_fallback(self):
        """pdfplumber 缺失但 PyPDF2 存在时可用。"""
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pdfplumber": None, "PyPDF2": _make_module()}):
            assert reader._check_pdf_available() is True

    def test_check_pdf_available_false(self):
        """PDF 库均缺失时返回 False。"""
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pdfplumber": None, "PyPDF2": None}):
            assert reader._check_pdf_available() is False

    def test_fetch_file_not_exists(self):
        """文件不存在时返回错误。"""
        reader = PdfExcelReader()
        result = reader.fetch("/nonexistent/file.xlsx")
        assert result["success"] is False
        assert "不存在" in result["error"]

    def test_fetch_unsupported_type(self, tmp_path):
        """不支持的扩展名返回错误。"""
        path = tmp_path / "data.txt"
        path.write_text("test")
        reader = PdfExcelReader()
        result = reader.fetch(str(path))
        assert result["success"] is False
        assert "不支持的文件类型" in result["error"]

    def test_read_csv_success(self, tmp_path):
        """CSV 文件读取成功。"""
        path = tmp_path / "data.csv"
        path.write_text("x")
        df = _fake_dataframe([{"a": 1}])
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pandas": self._fake_pandas(df)}):
            result = reader.fetch(str(path))
        assert result["success"] is True
        assert result["file_type"] == "excel"
        assert result["row_count"] == 1

    def test_read_excel_success(self, tmp_path):
        """Excel 文件读取成功。"""
        path = tmp_path / "data.xlsx"
        path.write_bytes(b"fake")
        df = _fake_dataframe([{"b": 2}])
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pandas": self._fake_pandas(df)}):
            result = reader.fetch(str(path), sheet_name="Sheet1")
        assert result["success"] is True
        assert result["file_type"] == "excel"

    def test_read_excel_exception(self, tmp_path):
        """Excel 读取异常时返回错误。"""
        path = tmp_path / "data.xlsx"
        path.write_bytes(b"fake")
        fake_pd = type(sys)("pandas")
        fake_pd.read_excel = MagicMock(side_effect=RuntimeError("bad file"))
        fake_pd.read_csv = MagicMock(side_effect=RuntimeError("bad file"))
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pandas": fake_pd}):
            result = reader.fetch(str(path))
        assert result["success"] is False
        assert result["error_type"] == "RuntimeError"

    def test_read_pdf_pdfplumber_success(self, tmp_path):
        """使用 pdfplumber 读取 PDF 成功。"""
        path = tmp_path / "data.pdf"
        path.write_bytes(b"pdf")
        page = MagicMock(extract_text=MagicMock(return_value="hello"))
        pdf = MagicMock(pages=[page])
        pdf.__enter__ = MagicMock(return_value=pdf)
        pdf.__exit__ = MagicMock(return_value=None)
        fake_pdfplumber = _make_module(open=MagicMock(return_value=pdf))
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pdfplumber": fake_pdfplumber, "PyPDF2": None}):
            result = reader.fetch(str(path))
        assert result["success"] is True
        assert result["file_type"] == "pdf"
        assert result["page_count"] == 1
        assert "hello" in result["data"]

    def test_read_pdf_pypdf2_success(self, tmp_path):
        """pdfplumber 缺失时使用 PyPDF2 读取成功。"""
        path = tmp_path / "data.pdf"
        path.write_bytes(b"pdf")
        page = MagicMock(extract_text=MagicMock(return_value="world"))
        reader = MagicMock(pages=[page])
        fake_pypdf2 = _make_module(PdfReader=MagicMock(return_value=reader))
        reader_obj = PdfExcelReader()
        with patch.dict(sys.modules, {"pdfplumber": None, "PyPDF2": fake_pypdf2}):
            result = reader_obj.fetch(str(path))
        assert result["success"] is True
        assert result["file_type"] == "pdf"
        assert "world" in result["data"]

    def test_read_pdf_pypdf2_exception(self, tmp_path):
        """PyPDF2 读取 PDF 抛异常时返回错误。"""
        path = tmp_path / "data.pdf"
        path.write_bytes(b"pdf")
        fake_pypdf2 = _make_module(PdfReader=MagicMock(side_effect=RuntimeError("broken")))
        reader_obj = PdfExcelReader()
        with patch.dict(sys.modules, {"pdfplumber": None, "PyPDF2": fake_pypdf2}):
            result = reader_obj.fetch(str(path))
        assert result["success"] is False
        assert result["error_type"] == "RuntimeError"

    def test_read_pdf_no_library(self, tmp_path):
        """PDF 库缺失时返回错误。"""
        path = tmp_path / "data.pdf"
        path.write_bytes(b"pdf")
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pdfplumber": None, "PyPDF2": None}):
            result = reader.fetch(str(path))
        assert result["success"] is False
        assert "PDF 读取库未安装" in result["error"]

    def test_read_pdf_exception(self, tmp_path):
        """PDF 读取抛异常时返回错误。"""
        path = tmp_path / "data.pdf"
        path.write_bytes(b"pdf")
        fake_pdfplumber = _make_module(open=MagicMock(side_effect=OSError("bad")))
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pdfplumber": fake_pdfplumber, "PyPDF2": None}):
            result = reader.fetch(str(path))
        assert result["success"] is False
        assert result["error_type"] == "OSError"

    def test_list_sheets_success(self, tmp_path):
        """列出 Excel 工作表成功。"""
        path = tmp_path / "data.xlsx"
        path.write_bytes(b"fake")
        df = _fake_dataframe([{"a": 1}])
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pandas": self._fake_pandas(df)}):
            result = reader.list_sheets(str(path))
        assert result["success"] is True
        assert result["sheets"] == ["Sheet1", "Sheet2"]
        assert result["sheet_count"] == 2

    def test_list_sheets_exception(self, tmp_path):
        """列出工作表异常时返回错误。"""
        path = tmp_path / "data.xlsx"
        path.write_bytes(b"fake")
        fake_pd = type(sys)("pandas")
        fake_pd.ExcelFile = MagicMock(side_effect=ValueError("no sheets"))
        reader = PdfExcelReader()
        with patch.dict(sys.modules, {"pandas": fake_pd}):
            result = reader.list_sheets(str(path))
        assert result["success"] is False
        assert "no sheets" in result["error"]
