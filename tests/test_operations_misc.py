"""Tests for datacore.operations crawl_retry / error_log — 覆盖未覆盖分支。"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from datacore.operations.crawl_retry import (
    RetryConfig,
    retry_call,
    retry_with_backoff,
)
from datacore.operations.error_log import ErrorLogger, log_error_json


class TestCrawlRetryExtras:
    """重试装饰器补充测试。"""

    def test_retry_decorator_bare_form(self):
        """不带括号的装饰器形式。"""

        @retry_with_backoff
        def bare_func():
            return "ok"

        assert bare_func() == "ok"

    def test_retry_call_raises_original_exception(self):
        """命令式重试超过次数后抛出原异常。"""
        calls = []

        def failing():
            calls.append(1)
            raise ValueError("original")

        with patch("datacore.operations.crawl_retry.time.sleep"):
            with pytest.raises(ValueError, match="original"):
                retry_call(
                    failing,
                    config=RetryConfig(max_retries=2, base_delay=0.001, jitter=False),
                )

        assert len(calls) == 3

    def test_retry_call_full_loop(self):
        """重试循环完整分支：第 3 次成功。"""
        calls = []

        def unstable():
            calls.append(1)
            if len(calls) < 3:
                raise RuntimeError("not yet")
            return "done"

        with patch("datacore.operations.crawl_retry.time.sleep"):
            result = retry_call(
                unstable,
                config=RetryConfig(max_retries=3, base_delay=0.001, jitter=False),
            )

        assert result == "done"
        assert len(calls) == 3


class TestErrorLogExtras:
    """错误日志补充测试。"""

    def test_log_error_json_with_dynamic_severity(self):
        """使用 logger 的动态严重级别方法。"""
        logger = MagicMock(spec=logging.Logger)
        logger.warning = MagicMock()

        try:
            raise ValueError("warn")
        except ValueError as e:
            log_error_json(e, severity="WARNING", logger=logger)

        logger.warning.assert_called_once()

    def test_error_logger_file_handler(self):
        """ErrorLogger 文件 handler 写入日志。"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False
        ) as log_file:
            log_path = log_file.name

        try:
            logger = ErrorLogger(
                name="test_file_logger",
                level=logging.INFO,
                output_file=log_path,
            )
            try:
                try:
                    raise RuntimeError("file error")
                except RuntimeError as e:
                    logger.log_error(e, module="test", function="file")

                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                assert "RuntimeError" in content
                assert "file error" in content
            finally:
                # 清理 handler，避免污染其他测试
                for handler in logger.logger.handlers[:]:
                    handler.close()
                    logger.logger.removeHandler(handler)
        finally:
            os.unlink(log_path)

    def test_error_logger_with_context(self):
        """ErrorLogger 上下文合并到错误日志。"""
        logger = ErrorLogger(name="test_ctx_logger")
        try:
            logger.add_context(request_id="abc", env="test")
            try:
                raise TypeError("ctx")
            except TypeError as e:
                log_str = logger.log_error(
                    e,
                    module="mod",
                    function="fn",
                    context={"extra": "data"},
                )

            record = json.loads(log_str)
            assert record["context"]["request_id"] == "abc"
            assert record["context"]["env"] == "test"
            assert record["context"]["extra"] == "data"
        finally:
            for handler in logger.logger.handlers[:]:
                handler.close()
                logger.logger.removeHandler(handler)

    def test_error_logger_info(self, caplog):
        """ErrorLogger.info 输出 JSON 格式 INFO 日志。"""
        logger = ErrorLogger(name="test_info_logger", level=logging.INFO)
        try:
            logger.add_context(service="ops")
            with caplog.at_level(logging.INFO, logger="test_info_logger"):
                logger.info("hello", user="me")

            assert len(caplog.records) == 1
            record = json.loads(caplog.records[0].message)
            assert record["severity"] == "INFO"
            assert record["message"] == "hello"
            assert record["service"] == "ops"
            assert record["user"] == "me"
        finally:
            for handler in logger.logger.handlers[:]:
                handler.close()
                logger.logger.removeHandler(handler)
