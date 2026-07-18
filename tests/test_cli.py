#!/usr/bin/env python3
"""Tests for datacore.cli — 覆盖 main() 及所有子命令。"""
import sys
import pytest
from unittest.mock import patch, MagicMock
from datacore import cli


# ── cmd_quote ──────────────────────────────────────────────────────────

class TestCmdQuote:
    def test_single_symbol(self, capsys):
        mock_dc = MagicMock()
        mock_dc.get.return_value = {"price": 123.45}
        with patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc):
            args = type("args", (), {"symbols": ["000001"]})()
            cli.cmd_quote(args)
        out, _ = capsys.readouterr()
        assert "000001:" in out
        assert "price" in out
        mock_dc.get.assert_called_once_with("000001", "quote")

    def test_multiple_symbols(self, capsys):
        mock_dc = MagicMock()
        mock_dc.get.side_effect = [{"price": 10}, {"price": 20}]
        with patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc):
            args = type("args", (), {"symbols": ["A", "B"]})()
            cli.cmd_quote(args)
        out, _ = capsys.readouterr()
        assert "A:" in out
        assert "B:" in out
        assert mock_dc.get.call_count == 2

    def test_empty_symbols(self, capsys):
        mock_dc = MagicMock()
        with patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc):
            args = type("args", (), {"symbols": []})()
            cli.cmd_quote(args)
        out, _ = capsys.readouterr()
        assert out.strip() == ""
        mock_dc.get.assert_not_called()

    def test_provider_exception_propagates(self):
        """异常路径：UnifiedDataProvider.get 抛出异常时冒泡。"""
        mock_dc = MagicMock()
        mock_dc.get.side_effect = RuntimeError("API down")
        with patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc):
            args = type("args", (), {"symbols": ["X"]})()
            with pytest.raises(RuntimeError, match="API down"):
                cli.cmd_quote(args)


# ── cmd_list ───────────────────────────────────────────────────────────

class TestCmdList:
    def test_list_symbols(self, capsys):
        mock_dc = MagicMock()
        mock_dc.list_symbols.return_value = [
            {"symbol": "000001", "name": "平安银行", "market": "SZ"},
            {"symbol": "600519", "name": "贵州茅台", "market": "SH"},
        ]
        with patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc):
            cli.cmd_list(None)
        out, _ = capsys.readouterr()
        assert "000001" in out
        assert "平安银行" in out
        assert "SZ" in out
        assert "600519" in out
        assert "贵州茅台" in out
        assert "SH" in out
        mock_dc.list_symbols.assert_called_once()

    def test_list_empty(self, capsys):
        mock_dc = MagicMock()
        mock_dc.list_symbols.return_value = []
        with patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc):
            cli.cmd_list(None)
        out, _ = capsys.readouterr()
        assert out.strip() == ""
        mock_dc.list_symbols.assert_called_once()

    def test_list_exception_propagates(self):
        mock_dc = MagicMock()
        mock_dc.list_symbols.side_effect = OSError("network error")
        with patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc):
            with pytest.raises(OSError, match="network error"):
                cli.cmd_list(None)


# ── cmd_status ─────────────────────────────────────────────────────────

class TestCmdStatus:
    def test_status_output(self, capsys):
        mock_dc = MagicMock()
        mock_dc.list_symbols.return_value = [{"symbol": "A"}, {"symbol": "B"}]
        mock_dc.get_health.return_value = {
            "status": "degraded",
            "version": "0.1.0",
            "sources": {
                "tdx_lc": {"available": True, "latency_ms": 5.0},
                "tencent": {"available": False, "latency_ms": 0.0, "error": "timeout"},
                "eastmoney": {"available": True, "latency_ms": 12.0},
            },
            "timestamp": 1000.0,
        }
        with (
            patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc),
            patch("datacore.cli.__version__", "0.1.0"),
        ):
            cli.cmd_status(None)
        out, _ = capsys.readouterr()
        assert "Data-Core v0.1.0" in out
        assert "注册表" in out
        assert "2 个标的" in out
        assert "tdx_lc" in out
        assert "tencent" in out
        assert "eastmoney" in out

    def test_status_provider_exception_propagates(self):
        mock_dc = MagicMock()
        mock_dc.list_symbols.side_effect = ConnectionError("refused")
        with patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc):
            with pytest.raises(ConnectionError, match="refused"):
                cli.cmd_status(None)


# ── main() ─────────────────────────────────────────────────────────────

class TestMain:
    def test_no_args_shows_help(self, capsys):
        with patch("datacore.cli.__version__", "0.1.0"):
            with patch.object(sys, "argv", ["datacore"]):
                cli.main()
        out, _ = capsys.readouterr()
        assert "Data-Core v0.1.0" in out
        assert "用法" in out
        assert "datacore list" in out
        assert "datacore status" in out
        assert "datacore quote" in out

    def test_main_list(self, capsys):
        mock_dc = MagicMock()
        mock_dc.list_symbols.return_value = [{"symbol": "X", "name": "Y", "market": "Z"}]
        with patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc):
            with patch.object(sys, "argv", ["datacore", "list"]):
                cli.main()
        out, _ = capsys.readouterr()
        assert "X" in out
        assert "Y" in out
        assert "Z" in out
        mock_dc.list_symbols.assert_called_once()

    def test_main_status(self, capsys):
        mock_dc = MagicMock()
        mock_dc.list_symbols.return_value = [{"symbol": "A"}]
        with (
            patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc),
            patch("datacore.cli.__version__", "0.2.0"),
            patch.object(sys, "argv", ["datacore", "status"]),
        ):
            cli.main()
        out, _ = capsys.readouterr()
        assert "Data-Core v0.2.0" in out
        assert "注册表" in out

    def test_main_quote(self, capsys):
        mock_dc = MagicMock()
        mock_dc.get.return_value = {"price": 99.9}
        with patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc):
            with patch.object(sys, "argv", ["datacore", "quote", "000001"]):
                cli.main()
        out, _ = capsys.readouterr()
        assert "000001:" in out
        mock_dc.get.assert_called_once_with("000001", "quote")

    def test_main_quote_multiple(self, capsys):
        mock_dc = MagicMock()
        mock_dc.get.side_effect = [{"p": 1}, {"p": 2}]
        with patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc):
            with patch.object(sys, "argv", ["datacore", "quote", "A", "B"]):
                cli.main()
        out, _ = capsys.readouterr()
        assert "A:" in out
        assert "B:" in out
        assert mock_dc.get.call_count == 2

    def test_main_quote_no_symbol(self, capsys):
        """quote 不带 symbol 时进入 else 分支输出未知命令。"""
        with patch.object(sys, "argv", ["datacore", "quote"]):
            cli.main()
        out, _ = capsys.readouterr()
        assert "未知命令" in out

    def test_main_unknown_command(self, capsys):
        with patch.object(sys, "argv", ["datacore", "foobar"]):
            cli.main()
        out, _ = capsys.readouterr()
        assert "未知命令" in out

    def test_main_extra_args_ignored_for_list(self, capsys):
        """list 后面多传参数不应报错。"""
        mock_dc = MagicMock()
        mock_dc.list_symbols.return_value = []
        with patch("datacore.cli.UnifiedDataProvider", return_value=mock_dc):
            with patch.object(sys, "argv", ["datacore", "list", "--all"]):
                cli.main()
        out, _ = capsys.readouterr()
        mock_dc.list_symbols.assert_called_once()

    def test_main_entry_point(self):
        """覆盖 if __name__ == '__main__' 入口 — 通过 subprocess 执行。"""
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "datacore.cli"],
            capture_output=True, text=True, cwd="d:\\Programs\\data-core",
        )
        assert result.returncode == 0
        assert "Data-Core" in result.stdout
        assert "用法" in result.stdout
