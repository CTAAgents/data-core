from __future__ import annotations
import time
from typing import Any, Callable
from enum import Enum


class BreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class Breaker:
    """带状态熔断器 — 保护外部数据源调用。"""

    def __init__(self, name: str, max_failures: int = 3, recovery_timeout: float = 30.0):
        self.name = name
        self.max_failures = max_failures
        self.recovery_timeout = recovery_timeout
        self.state = BreakerState.CLOSED
        self._fail_count = 0
        self._last_failure_time = 0.0
        self._total_calls = 0
        self._total_failures = 0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """带熔断保护的函数调用。"""
        self._total_calls += 1
        if self.state == BreakerState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self.state = BreakerState.HALF_OPEN
            else:
                raise RuntimeError(f"Breaker {self.name} is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == BreakerState.HALF_OPEN:
                self.state = BreakerState.CLOSED
                self._fail_count = 0
            return result
        except Exception:
            self._fail_count += 1
            self._total_failures += 1
            self._last_failure_time = time.time()
            if self._fail_count >= self.max_failures:
                self.state = BreakerState.OPEN
            raise

    def reset(self):
        """手动重置熔断器。"""
        self.state = BreakerState.CLOSED
        self._fail_count = 0

    @property
    def stats(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "fail_count": self._fail_count,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
        }
