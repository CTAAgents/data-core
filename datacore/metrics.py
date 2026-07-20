"""指标收集框架 — 调用统计、延迟、成功率。"""
from __future__ import annotations
import time
from typing import Optional
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class MetricEntry:
    calls: int = 0
    failures: int = 0
    total_duration: float = 0.0
    last_call: float = 0.0


class MetricsCollector:
    """轻量级指标收集器。"""

    def __init__(self, max_entries: int = 1000):
        self._metrics: dict[str, MetricEntry] = defaultdict(MetricEntry)
        self.max_entries = max_entries

    def record(self, key: str, duration: float, success: bool = True) -> None:
        entry = self._metrics[key]
        entry.calls += 1
        if not success:
            entry.failures += 1
        entry.total_duration += duration
        entry.last_call = time.time()
        if len(self._metrics) > self.max_entries:
            oldest = min(self._metrics, key=lambda k: self._metrics[k].last_call)
            del self._metrics[oldest]

    def snapshot(self) -> dict[str, dict]:
        result = {}
        for key, entry in self._metrics.items():
            avg_duration = round(entry.total_duration / entry.calls, 3) if entry.calls > 0 else 0.0
            success_rate = round((entry.calls - entry.failures) / entry.calls * 100, 1) if entry.calls > 0 else 0.0
            result[key] = {
                "calls": entry.calls,
                "failures": entry.failures,
                "success_rate": success_rate,
                "avg_duration": avg_duration,
                "last_call": entry.last_call,
            }
        return result

    def summary(self) -> dict:
        snap = self.snapshot()
        total_calls = sum(v["calls"] for v in snap.values())
        total_failures = sum(v["failures"] for v in snap.values())
        rate = round((total_calls - total_failures) / total_calls * 100, 1) if total_calls > 0 else 0.0
        return {
            "total_calls": total_calls,
            "total_failures": total_failures,
            "overall_success_rate": rate,
            "endpoints": snap,
        }

    def reset(self) -> None:
        self._metrics.clear()

    def _format_prometheus(self) -> str:
        """输出 Prometheus exposition format 文本。

        将内部统计指标转换为标准 Prometheus 文本格式，便于
        Prometheus 服务抓取。指标命名遵循 datacore_<name> 规范。

        Returns:
            Prometheus exposition format 字符串
        """
        snap = self.snapshot()
        if not snap:
            return ""

        lines: list[str] = []

        # Counter: 总调用次数
        lines.append("# HELP datacore_calls_total Total calls by endpoint")
        lines.append("# TYPE datacore_calls_total counter")
        for key in sorted(snap.keys()):
            entry = snap[key]
            lines.append(
                f'datacore_calls_total{{endpoint="{key}"}} {entry["calls"]}'
            )

        # Counter: 失败次数
        lines.append("# HELP datacore_failures_total Total failures by endpoint")
        lines.append("# TYPE datacore_failures_total counter")
        for key in sorted(snap.keys()):
            entry = snap[key]
            lines.append(
                f'datacore_failures_total{{endpoint="{key}"}} {entry["failures"]}'
            )

        # Gauge: 成功率
        lines.append("# HELP datacore_success_rate Success rate by endpoint (percent)")
        lines.append("# TYPE datacore_success_rate gauge")
        for key in sorted(snap.keys()):
            entry = snap[key]
            lines.append(
                f'datacore_success_rate{{endpoint="{key}"}} {entry["success_rate"]}'
            )

        # Gauge: 平均延迟（秒）
        lines.append("# HELP datacore_avg_duration_seconds Average duration in seconds")
        lines.append("# TYPE datacore_avg_duration_seconds gauge")
        for key in sorted(snap.keys()):
            entry = snap[key]
            lines.append(
                f'datacore_avg_duration_seconds{{endpoint="{key}"}} {entry["avg_duration"]}'
            )

        return "\n".join(lines) + "\n"


_metrics_instance: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance
