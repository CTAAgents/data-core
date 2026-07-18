"""Tests for datacore.metrics — MetricsCollector 指标收集器。"""
from __future__ import annotations

import time
import pytest
from unittest.mock import patch
from datacore.metrics import MetricsCollector, get_metrics


class TestMetricsCollector:
    def test_initial_empty(self):
        """初始空指标。"""
        m = MetricsCollector()
        assert m.snapshot() == {}

    def test_record_once(self):
        """record() 一次调用。"""
        m = MetricsCollector()
        m.record("api", 0.1, success=True)
        snap = m.snapshot()
        assert "api" in snap
        assert snap["api"]["calls"] == 1
        assert snap["api"]["failures"] == 0

    def test_record_failure(self):
        """record() 失败调用。"""
        m = MetricsCollector()
        m.record("api", 0.2, success=False)
        snap = m.snapshot()
        assert snap["api"]["calls"] == 1
        assert snap["api"]["failures"] == 1
        assert snap["api"]["success_rate"] == 0.0

    def test_snapshot_format(self):
        """snapshot() 返回正确格式。"""
        m = MetricsCollector()
        m.record("test", 0.5, success=True)
        snap = m.snapshot()
        entry = snap["test"]
        assert set(entry.keys()) == {"calls", "failures", "success_rate", "avg_duration", "last_call"}
        assert isinstance(entry["calls"], int)
        assert isinstance(entry["failures"], int)
        assert isinstance(entry["success_rate"], float)
        assert isinstance(entry["avg_duration"], float)

    def test_summary(self):
        """summary() 总览。"""
        m = MetricsCollector()
        m.record("a", 0.1, success=True)
        m.record("a", 0.2, success=False)
        m.record("b", 0.3, success=True)
        s = m.summary()
        assert s["total_calls"] == 3
        assert s["total_failures"] == 1
        assert "endpoints" in s
        assert set(s["endpoints"].keys()) == {"a", "b"}

    def test_multiple_keys(self):
        """多 key 记录。"""
        m = MetricsCollector()
        m.record("alpha", 0.1)
        m.record("beta", 0.2)
        m.record("gamma", 0.3)
        assert len(m.snapshot()) == 3

    def test_eviction(self):
        """自动淘汰旧条目（max_entries）。"""
        m = MetricsCollector(max_entries=3)
        m.record("a", 0.1)
        m.record("b", 0.1)
        m.record("c", 0.1)
        m.record("d", 0.1)  # 应淘汰一个
        snap = m.snapshot()
        assert len(snap) == 3  # max_entries=3 最多保留 3 个

    def test_reset(self):
        """reset() 清空。"""
        m = MetricsCollector()
        m.record("x", 0.5)
        assert len(m.snapshot()) == 1
        m.reset()
        assert m.snapshot() == {}

    def test_avg_duration(self):
        """avg_duration 计算正确。"""
        m = MetricsCollector()
        m.record("api", 0.2, success=True)
        m.record("api", 0.4, success=True)
        snap = m.snapshot()
        # (0.2 + 0.4) / 2 = 0.3
        assert snap["api"]["avg_duration"] == 0.3

    def test_success_rate(self):
        """success_rate 计算正确。"""
        m = MetricsCollector()
        m.record("api", 0.1, success=True)
        m.record("api", 0.1, success=True)
        m.record("api", 0.1, success=False)
        snap = m.snapshot()
        # (3 - 1) / 3 * 100 = 66.7
        assert snap["api"]["success_rate"] == 66.7

    def test_many_records(self):
        """大量记录性能。"""
        m = MetricsCollector()
        for i in range(1000):
            m.record(f"key_{i % 50}", 0.01, success=(i % 5 != 0))
        snap = m.snapshot()
        assert len(snap) == 50
        total_calls = sum(v["calls"] for v in snap.values())
        assert total_calls == 1000

    def test_get_metrics_singleton(self):
        """get_metrics() 单例。"""
        # 重置全局实例
        import datacore.metrics as metrics_mod
        metrics_mod._metrics_instance = None

        m1 = get_metrics()
        m2 = get_metrics()
        assert m1 is m2
