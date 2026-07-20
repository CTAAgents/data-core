"""Tests for datacore.operations.config_tools — 覆盖未覆盖分支。"""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
from unittest.mock import patch

import pytest

from datacore.operations import config_tools
from datacore.operations.config_tools import (
    ConfigLoader,
    _convert_value,
    load_config,
    load_yaml_config,
)


class TestConfigToolsExtras:
    """配置工具补充测试。"""

    def test_yaml_import_failure_sets_has_yaml_false(self):
        """yaml 导入失败时 HAS_YAML 为 False 且走空分支。"""
        original_yaml = sys.modules.get("yaml")

        def blocking_import(name, *args, **kwargs):
            if name == "yaml":
                raise ImportError("no yaml")
            return importlib.__import__(name, *args, **kwargs)

        try:
            if original_yaml is not None:
                del sys.modules["yaml"]
            with patch("builtins.__import__", side_effect=blocking_import):
                reloaded = importlib.reload(config_tools)
                assert reloaded.HAS_YAML is False

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                f.write("key: value\n")
                path = f.name

            try:
                assert config_tools.load_yaml_config(path) == {}
            finally:
                os.unlink(path)
        finally:
            if original_yaml is not None:
                sys.modules["yaml"] = original_yaml
            importlib.reload(config_tools)

    def test_load_yaml_config_parsing_error(self):
        """YAML 解析异常时返回空字典。"""
        with patch.object(config_tools.yaml, "safe_load", side_effect=RuntimeError("boom")):
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                f.write("key: value\n")
                path = f.name

            try:
                assert load_yaml_config(path) == {}
            finally:
                os.unlink(path)

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("true", True),
            ("True", True),
            ("yes", True),
            ("1", True),
            ("false", False),
            ("False", False),
            ("no", False),
            ("0", False),
            ("42", 42),
            ("3.14", 3.14),
            ("hello", "hello"),
        ],
    )
    def test_convert_value_various_types(self, raw, expected):
        """_convert_value 各种类型转换。"""
        assert _convert_value(raw) == expected

    def test_load_config_env_override_and_conversion(self, monkeypatch):
        """环境变量覆盖 YAML 并做类型转换。"""
        monkeypatch.setenv("DATACORE_FLAG", "true")
        monkeypatch.setenv("DATACORE_COUNT", "7")
        monkeypatch.setenv("DATACORE_RATIO", "2.5")
        monkeypatch.setenv("DATACORE_NAME", "ops")

        config = load_config(env_prefix="DATACORE_")
        assert config["flag"] is True
        assert config["count"] == 7
        assert config["ratio"] == 2.5
        assert config["name"] == "ops"

    def test_config_loader_auto_reload(self):
        """ConfigLoader 文件热重载。"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("version: 1\n")
            path = f.name

        try:
            loader = ConfigLoader(yaml_path=path, auto_reload=True)
            assert loader.get("version") == 1

            # 修改文件并强制更新 mtime，使其大于 _last_mtime
            with open(path, "w", encoding="utf-8") as f:
                f.write("version: 2\n")

            import os as _os
            new_mtime = _os.path.getmtime(path) + 1
            _os.utime(path, (new_mtime, new_mtime))

            assert loader.get("version") == 2
        finally:
            os.unlink(path)

    def test_config_loader_to_dict_triggers_reload(self):
        """to_dict 也会触发 _check_reload。"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("name: first\n")
            path = f.name

        try:
            loader = ConfigLoader(yaml_path=path, auto_reload=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write("name: second\n")

            import os as _os
            new_mtime = _os.path.getmtime(path) + 1
            _os.utime(path, (new_mtime, new_mtime))

            assert loader.to_dict()["name"] == "second"
        finally:
            os.unlink(path)

    def test_config_loader_getitem_or_raise(self):
        """__getitem__ 返回配置值，缺失时抛出 KeyError。"""
        loader = ConfigLoader()
        loader.set("existing.nested", "value")
        assert loader["existing.nested"] == "value"

        with pytest.raises(KeyError):
            _ = loader["missing"]

    def test_config_loader_auto_reload_missing_file(self):
        """热重载时 YAML 文件不存在，不抛异常。"""
        loader = ConfigLoader(
            yaml_path="/nonexistent/path/config.yaml",
            auto_reload=True,
        )
        assert loader.get("any") is None
        assert loader.to_dict() == {}
