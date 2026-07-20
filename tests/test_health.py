"""Tests for datacore.health — HealthChecker 健康检查器。"""
from __future__ import annotations

from datacore.health import HealthChecker


def _healthy() -> bool:
    return True


def _unhealthy() -> bool:
    return False


def _explode() -> bool:
    raise ConnectionError("connection refused")


class TestHealthChecker:
    def test_check_all_empty(self):
        """check_all() 空注册返回空 dict。"""
        hc = HealthChecker()
        assert hc.check_all() == {}

    def test_register_and_check_normal(self):
        """register() 后 check 正常。"""
        hc = HealthChecker()
        hc.register("src_a", _healthy)
        result = hc.check("src_a")
        assert result["available"] is True
        assert "latency_ms" in result

    def test_check_all_returns_all(self):
        """check_all() 返回所有注册源结果。"""
        hc = HealthChecker()
        hc.register("a", _healthy)
        hc.register("b", _unhealthy)
        results = hc.check_all()
        assert set(results.keys()) == {"a", "b"}
        assert results["a"]["available"] is True
        assert results["b"]["available"] is False

    def test_check_available_true(self):
        """check_available() 返回 True。"""
        hc = HealthChecker()
        hc.register("db", _healthy)
        assert hc.check("db")["available"] is True

    def test_check_available_false(self):
        """check_available() 返回 False。"""
        hc = HealthChecker()
        hc.register("db", _unhealthy)
        assert hc.check("db")["available"] is False

    def test_check_exception(self):
        """check() 时函数抛出异常。"""
        hc = HealthChecker()
        hc.register("broken", _explode)
        result = hc.check("broken")
        assert result["available"] is False
        assert "error" in result
        assert "connection refused" in result["error"]

    def test_check_unknown_name(self):
        """check() 未知名称返回 error。"""
        hc = HealthChecker()
        result = hc.check("nonexistent")
        assert result["available"] is False
        assert "unknown source" in result["error"]

    def test_check_all_mixed_success_and_failure(self):
        """check_all() 混合成功/失败源。"""
        hc = HealthChecker()
        hc.register("good", _healthy)
        hc.register("bad", _unhealthy)
        hc.register("ugly", _explode)
        results = hc.check_all()
        assert results["good"]["available"] is True
        assert results["bad"]["available"] is False
        assert results["ugly"]["available"] is False
        assert "error" in results["ugly"]
        assert "error" not in results["good"]

    def test_check_has_latency_ms(self):
        """check() 包含 latency_ms 字段。"""
        hc = HealthChecker()
        hc.register("api", _healthy)
        result = hc.check("api")
        assert "latency_ms" in result
        assert isinstance(result["latency_ms"], (int, float))
        assert result["latency_ms"] >= 0

    def test_register_overwrite(self):
        """多次注册覆盖。"""
        hc = HealthChecker()

        def _first() -> bool:
            return True

        def _second() -> bool:
            return False

        hc.register("src", _first)
        assert hc.check("src")["available"] is True
        hc.register("src", _second)
        assert hc.check("src")["available"] is False
