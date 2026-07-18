"""Tests for datacore.breaker — Breaker 熔断器。"""
from __future__ import annotations

import time
import pytest
from unittest.mock import patch
from datacore.breaker import Breaker, BreakerState


def _ok():
    return "ok"


def _fail():
    raise ValueError("boom")


class TestBreaker:
    def test_initial_state(self):
        """初始状态为 CLOSED。"""
        b = Breaker("test")
        assert b.state == BreakerState.CLOSED

    def test_success_keeps_closed(self):
        """成功调用保持 CLOSED。"""
        b = Breaker("test")
        result = b.call(_ok)
        assert result == "ok"
        assert b.state == BreakerState.CLOSED

    def test_threshold_opens(self):
        """连续失败达到阈值切换为 OPEN。"""
        b = Breaker("test", max_failures=3)
        for _ in range(3):
            with pytest.raises(ValueError):
                b.call(_fail)
        assert b.state == BreakerState.OPEN
        assert b.stats["fail_count"] == 3

    def test_open_raises_runtime_error(self):
        """OPEN 状态下调用抛 RuntimeError。"""
        b = Breaker("test", max_failures=1)
        with pytest.raises(ValueError):
            b.call(_fail)
        assert b.state == BreakerState.OPEN
        with pytest.raises(RuntimeError, match="is OPEN"):
            b.call(_ok)

    def test_timeout_recovers_to_half_open(self):
        """超时后自动切换为 HALF_OPEN。"""
        b = Breaker("test", max_failures=1, recovery_timeout=10)
        with pytest.raises(ValueError):
            b.call(_fail)
        assert b.state == BreakerState.OPEN

        fake_now = time.time() + 15  # 超过 recovery_timeout
        with patch("datacore.breaker.time.time", return_value=fake_now):
            # 此时应切换为 HALF_OPEN，然后调用成功
            result = b.call(_ok)
            assert result == "ok"
            assert b.state == BreakerState.CLOSED

    def test_half_open_success_recovers(self):
        """HALF_OPEN 下成功调用恢复 CLOSED。"""
        b = Breaker("test", max_failures=1, recovery_timeout=0)
        with pytest.raises(ValueError):
            b.call(_fail)
        assert b.state == BreakerState.OPEN

        # recovery_timeout=0，下次 call 立即进入 HALF_OPEN
        result = b.call(_ok)
        assert result == "ok"
        assert b.state == BreakerState.CLOSED

    def test_half_open_failure_reopens(self):
        """HALF_OPEN 下失败调用回到 OPEN。"""
        b = Breaker("test", max_failures=1, recovery_timeout=0)
        with pytest.raises(ValueError):
            b.call(_fail)
        assert b.state == BreakerState.OPEN

        # recovery_timeout=0，进入 HALF_OPEN，但再次失败
        with pytest.raises(ValueError):
            b.call(_fail)
        assert b.state == BreakerState.OPEN

    def test_reset(self):
        """reset() 重置为 CLOSED。"""
        b = Breaker("test", max_failures=1)
        with pytest.raises(ValueError):
            b.call(_fail)
        assert b.state == BreakerState.OPEN
        b.reset()
        assert b.state == BreakerState.CLOSED
        assert b.stats["fail_count"] == 0

    def test_stats(self):
        """stats 属性返回正确值。"""
        b = Breaker("test", max_failures=5)
        b.call(_ok)
        with pytest.raises(ValueError):
            b.call(_fail)
        stats = b.stats
        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["fail_count"] == 1
        assert stats["total_calls"] == 2
        assert stats["total_failures"] == 1

    def test_max_failures_one(self):
        """max_failures=1 时一次失败即熔断。"""
        b = Breaker("test", max_failures=1)
        with pytest.raises(ValueError):
            b.call(_fail)
        assert b.state == BreakerState.OPEN
        assert b.stats["fail_count"] == 1

    def test_recovery_timeout_zero(self):
        """recovery_timeout=0 时立即恢复尝试。"""
        b = Breaker("test", max_failures=1, recovery_timeout=0)
        with pytest.raises(ValueError):
            b.call(_fail)
        assert b.state == BreakerState.OPEN
        # recovery_timeout=0，call 立即进入 HALF_OPEN 并成功
        result = b.call(_ok)
        assert result == "ok"
        assert b.state == BreakerState.CLOSED

    def test_fail_count_reset_on_success(self):
        """成功调用后 fail_count 归零（HALF_OPEN→CLOSED）。"""
        b = Breaker("test", max_failures=1, recovery_timeout=0)
        with pytest.raises(ValueError):
            b.call(_fail)
        assert b.state == BreakerState.OPEN
        assert b.stats["fail_count"] == 1

        # recovery_timeout=0 → 进入 HALF_OPEN，成功调用后 fail_count 归零
        result = b.call(_ok)
        assert result == "ok"
        assert b.state == BreakerState.CLOSED
        assert b.stats["fail_count"] == 0

    def test_multiple_exception_types(self):
        """多种异常类型都能触发失败计数。"""
        b = Breaker("test", max_failures=3)

        def _type_error():
            raise TypeError("type err")

        def _key_error():
            raise KeyError("key err")

        def _value_error():
            raise ValueError("value err")

        with pytest.raises(TypeError):
            b.call(_type_error)
        with pytest.raises(KeyError):
            b.call(_key_error)
        with pytest.raises(ValueError):
            b.call(_value_error)

        assert b.state == BreakerState.OPEN
        assert b.stats["fail_count"] == 3

    def test_nested_breakers(self):
        """嵌套熔断器 — 各自独立工作。"""
        b1 = Breaker("src_a", max_failures=1)
        b2 = Breaker("src_b", max_failures=2)

        # b1 熔断
        with pytest.raises(ValueError):
            b1.call(_fail)
        assert b1.state == BreakerState.OPEN

        # b2 仍未熔断
        assert b2.state == BreakerState.CLOSED
        b2.call(_ok)
        assert b2.state == BreakerState.CLOSED

        # b2 第二次失败才熔断
        with pytest.raises(ValueError):
            b2.call(_fail)
        assert b2.state == BreakerState.CLOSED  # max_failures=2，一次失败不够
        with pytest.raises(ValueError):
            b2.call(_fail)
        assert b2.state == BreakerState.OPEN

    def test_breaker_state_enum_values(self):
        """BreakerState 枚举值正确。"""
        assert BreakerState.CLOSED.value == "closed"
        assert BreakerState.OPEN.value == "open"
        assert BreakerState.HALF_OPEN.value == "half_open"
        assert BreakerState.CLOSED.name == "CLOSED"
        assert BreakerState.OPEN.name == "OPEN"
        assert BreakerState.HALF_OPEN.name == "HALF_OPEN"

    def test_exception_reraised(self):
        """原始异常被重新抛出。"""
        b = Breaker("test")

        def _custom():
            raise RuntimeError("custom error")

        with pytest.raises(RuntimeError, match="custom error"):
            b.call(_custom)
        assert b.stats["fail_count"] == 1
