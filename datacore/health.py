from __future__ import annotations
from typing import Any, Callable
import time


class HealthChecker:
    """数据源健康检查器。"""

    def __init__(self):
        self._source_checks: dict[str, Any] = {}

    def register(self, name: str, check_fn: Callable[[], bool]) -> None:
        self._source_checks[name] = check_fn

    def check_all(self) -> dict[str, Any]:
        """检查所有注册源，返回健康状态。"""
        results = {}
        for name, check_fn in self._source_checks.items():
            try:
                ok = check_fn()
                results[name] = {"available": ok, "latency_ms": 0}
            except Exception as e:
                results[name] = {"available": False, "error": str(e)}
        return results

    def check(self, name: str) -> dict:
        """检查单个数据源。"""
        fn = self._source_checks.get(name)
        if fn is None:
            return {"available": False, "error": f"unknown source: {name}"}
        t0 = time.time()
        try:
            ok = fn()
            return {"available": ok, "latency_ms": round((time.time() - t0) * 1000, 1)}
        except Exception as e:
            return {"available": False, "error": str(e), "latency_ms": round((time.time() - t0) * 1000, 1)}
