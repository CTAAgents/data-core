"""统一可观测性入口 — Prometheus 指标 + 装饰器。

提供 Prometheus 标准指标类型（Counter/Gauge/Histogram），不依赖 prometheus_client 库
即可输出符合 exposition format 的文本。安装 prometheus_client 时优先使用官方库。

标准指标定义:
- datacore_api_requests_total (Counter): API 请求总数 [symbol, data_type, market]
- datacore_api_request_duration_seconds (Histogram): API 请求延迟 [symbol, data_type]
- datacore_api_errors_total (Counter): API 错误总数 [symbol, data_type, error_type]
- datacore_source_degradations_total (Counter): 数据源降级次数 [source, reason]
- datacore_source_availability (Gauge): 数据源可用性 0/1 [source]
- datacore_cache_hits_total (Counter): 缓存命中次数
- datacore_cache_misses_total (Counter): 缓存未命中次数
- datacore_resampler_operations_total (Counter): 重采样操作次数 [source_period, target_period]
- datacore_issues_open (Gauge): 未解决问题数 [issue_type]
- datacore_tool_invocations_total (Counter): Tool 调用次数 [tool_name]
- datacore_tool_errors_total (Counter): Tool 错误次数 [tool_name]
"""

from __future__ import annotations

import functools
import threading
import time
from typing import Any, Callable, Optional

try:
    import prometheus_client as _pc  # type: ignore
    HAS_PROMETHEUS_CLIENT = True
except ImportError:
    _pc = None  # type: ignore
    HAS_PROMETHEUS_CLIENT = False


# ============================================================
#  自定义 Prometheus 指标类型（fallback 实现）
# ============================================================

_CUSTOM_REGISTRY: list["_CustomMetric"] = []


def _format_label_value(val: Any) -> str:
    """将任意值转换为 Prometheus label value 字符串。"""
    if hasattr(val, "value"):
        val = val.value
    if val is None:
        return ""
    return str(val).replace("\\", "\\\\").replace('"', '\\"')


def _format_labels(label_names: list[str], label_values: tuple) -> str:
    """格式化 label 字符串。"""
    if not label_names:
        return ""
    parts = []
    for name, val in zip(label_names, label_values):
        parts.append(f'{name}="{_format_label_value(val)}"')
    return "{" + ",".join(parts) + "}"


class _CustomMetric:
    """自定义指标基类。"""

    metric_type: str = ""

    def __init__(self, name: str, documentation: str, labelnames: tuple = ()):
        self.name = name
        self.documentation = documentation
        self.label_names: list[str] = list(labelnames) if labelnames else []
        self._lock = threading.Lock()

    def format_exposition(self) -> str:
        raise NotImplementedError


class _CustomCounter(_CustomMetric):
    """自定义 Counter 实现。"""

    metric_type = "counter"

    def __init__(self, name: str, documentation: str, labelnames: tuple = ()):
        super().__init__(name, documentation, labelnames)
        self._values: dict[tuple, float] = {}
        _CUSTOM_REGISTRY.append(self)

    def inc(self, amount: float = 1.0, **labels) -> None:
        try:
            key = tuple(_normalize_label(labels.get(name, "")) for name in self.label_names)
            with self._lock:
                self._values[key] = self._values.get(key, 0.0) + amount
        except Exception:
            pass

    def collect(self) -> list[tuple[tuple, float]]:
        with self._lock:
            return list(self._values.items())

    def format_exposition(self) -> str:
        lines = [
            f"# HELP {self.name} {self.documentation}",
            f"# TYPE {self.name} counter",
        ]
        for label_values, value in sorted(self.collect()):
            label_str = _format_labels(self.label_names, label_values)
            lines.append(f"{self.name}{label_str} {value}")
        return "\n".join(lines) + "\n"


class _CustomGauge(_CustomMetric):
    """自定义 Gauge 实现。"""

    metric_type = "gauge"

    def __init__(self, name: str, documentation: str, labelnames: tuple = ()):
        super().__init__(name, documentation, labelnames)
        self._values: dict[tuple, float] = {}
        _CUSTOM_REGISTRY.append(self)

    def set(self, value: float, **labels) -> None:
        try:
            key = tuple(_normalize_label(labels.get(name, "")) for name in self.label_names)
            with self._lock:
                self._values[key] = value
        except Exception:
            pass

    def inc(self, amount: float = 1.0, **labels) -> None:
        try:
            key = tuple(_normalize_label(labels.get(name, "")) for name in self.label_names)
            with self._lock:
                self._values[key] = self._values.get(key, 0.0) + amount
        except Exception:
            pass

    def dec(self, amount: float = 1.0, **labels) -> None:
        self.inc(-amount, **labels)

    def collect(self) -> list[tuple[tuple, float]]:
        with self._lock:
            return list(self._values.items())

    def format_exposition(self) -> str:
        lines = [
            f"# HELP {self.name} {self.documentation}",
            f"# TYPE {self.name} gauge",
        ]
        for label_values, value in sorted(self.collect()):
            label_str = _format_labels(self.label_names, label_values)
            lines.append(f"{self.name}{label_str} {value}")
        return "\n".join(lines) + "\n"


class _CustomHistogram(_CustomMetric):
    """自定义 Histogram 实现。"""

    metric_type = "histogram"
    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def __init__(self, name: str, documentation: str, labelnames: tuple = (),
                 buckets: tuple = DEFAULT_BUCKETS):
        super().__init__(name, documentation, labelnames)
        self.buckets: list[float] = sorted(buckets)
        self._bucket_counts: dict[tuple, list[int]] = {}
        self._sums: dict[tuple, float] = {}
        self._totals: dict[tuple, int] = {}
        _CUSTOM_REGISTRY.append(self)

    def observe(self, value: float, **labels) -> None:
        try:
            key = tuple(_normalize_label(labels.get(name, "")) for name in self.label_names)
            with self._lock:
                if key not in self._bucket_counts:
                    self._bucket_counts[key] = [0] * len(self.buckets)
                    self._sums[key] = 0.0
                    self._totals[key] = 0
                # Cumulative: increment all buckets where value <= bound
                for i, bound in enumerate(self.buckets):
                    if value <= bound:
                        self._bucket_counts[key][i] += 1
                self._sums[key] += value
                self._totals[key] += 1
        except Exception:
            pass

    def format_exposition(self) -> str:
        lines = [
            f"# HELP {self.name} {self.documentation}",
            f"# TYPE {self.name} histogram",
        ]
        with self._lock:
            for label_values in sorted(self._bucket_counts.keys()):
                bucket_counts = self._bucket_counts[label_values]
                total = self._totals[label_values]
                sum_val = self._sums[label_values]

                base_labels = list(zip(self.label_names, label_values))

                # 各 bucket（cumulative）
                for i, bound in enumerate(self.buckets):
                    le_labels = base_labels + [("le", str(bound))]
                    label_str = "{" + ",".join(
                        f'{n}="{_format_label_value(v)}"' for n, v in le_labels
                    ) + "}"
                    lines.append(f"{self.name}_bucket{label_str} {bucket_counts[i]}")

                # +Inf bucket
                le_labels = base_labels + [("le", "+Inf")]
                label_str = "{" + ",".join(
                    f'{n}="{_format_label_value(v)}"' for n, v in le_labels
                ) + "}"
                lines.append(f"{self.name}_bucket{label_str} {total}")

                # sum 和 count
                if base_labels:
                    label_str = "{" + ",".join(
                        f'{n}="{_format_label_value(v)}"' for n, v in base_labels
                    ) + "}"
                    lines.append(f"{self.name}_sum{label_str} {sum_val}")
                    lines.append(f"{self.name}_count{label_str} {total}")
                else:
                    lines.append(f"{self.name}_sum {sum_val}")
                    lines.append(f"{self.name}_count {total}")
        return "\n".join(lines) + "\n"


# ============================================================
#  统一对外 API — 透明切换 prometheus_client / 自定义实现
# ============================================================

class Counter:
    """Counter 指标。安装 prometheus_client 时使用官方库，否则使用自定义实现。"""

    def __init__(self, name: str, documentation: str, labelnames: tuple = ()):
        self.name = name
        self.documentation = documentation
        self.label_names: list[str] = list(labelnames) if labelnames else []
        if HAS_PROMETHEUS_CLIENT:
            self._impl: Any = _pc.Counter(name, documentation, self.label_names)
            self._is_pc = True
        else:
            self._impl: Any = _CustomCounter(name, documentation, tuple(self.label_names))
            self._is_pc = False

    def inc(self, amount: float = 1.0, **labels) -> None:
        try:
            if self._is_pc:
                if self.label_names:
                    self._impl.labels(**labels).inc(amount)
                else:
                    self._impl.inc(amount)
            else:
                self._impl.inc(amount, **labels)
        except Exception:
            pass


class Gauge:
    """Gauge 指标。"""

    def __init__(self, name: str, documentation: str, labelnames: tuple = ()):
        self.name = name
        self.documentation = documentation
        self.label_names: list[str] = list(labelnames) if labelnames else []
        if HAS_PROMETHEUS_CLIENT:
            self._impl: Any = _pc.Gauge(name, documentation, self.label_names)
            self._is_pc = True
        else:
            self._impl: Any = _CustomGauge(name, documentation, tuple(self.label_names))
            self._is_pc = False

    def set(self, value: float, **labels) -> None:
        try:
            if self._is_pc:
                if self.label_names:
                    self._impl.labels(**labels).set(value)
                else:
                    self._impl.set(value)
            else:
                self._impl.set(value, **labels)
        except Exception:
            pass

    def inc(self, amount: float = 1.0, **labels) -> None:
        try:
            if self._is_pc:
                if self.label_names:
                    self._impl.labels(**labels).inc(amount)
                else:
                    self._impl.inc(amount)
            else:
                self._impl.inc(amount, **labels)
        except Exception:
            pass

    def dec(self, amount: float = 1.0, **labels) -> None:
        self.inc(-amount, **labels)


class Histogram:
    """Histogram 指标。"""

    def __init__(self, name: str, documentation: str, labelnames: tuple = ()):
        self.name = name
        self.documentation = documentation
        self.label_names: list[str] = list(labelnames) if labelnames else []
        if HAS_PROMETHEUS_CLIENT:
            self._impl: Any = _pc.Histogram(name, documentation, self.label_names)
            self._is_pc = True
        else:
            self._impl: Any = _CustomHistogram(
                name, documentation, tuple(self.label_names)
            )
            self._is_pc = False

    def observe(self, value: float, **labels) -> None:
        try:
            if self._is_pc:
                if self.label_names:
                    self._impl.labels(**labels).observe(value)
                else:
                    self._impl.observe(value)
            else:
                self._impl.observe(value, **labels)
        except Exception:
            pass


def generate_text() -> str:
    """生成 Prometheus exposition format 文本。"""
    if HAS_PROMETHEUS_CLIENT:
        return _pc.generate_latest().decode("utf-8")
    return "".join(m.format_exposition() for m in _CUSTOM_REGISTRY)


# ============================================================
#  标准指标定义
# ============================================================

api_requests_total = Counter(
    "datacore_api_requests_total",
    "Total API requests",
    ("symbol", "data_type", "market"),
)

api_request_duration_seconds = Histogram(
    "datacore_api_request_duration_seconds",
    "API request duration in seconds",
    ("symbol", "data_type"),
)

api_errors_total = Counter(
    "datacore_api_errors_total",
    "Total API errors",
    ("symbol", "data_type", "error_type"),
)

source_degradations_total = Counter(
    "datacore_source_degradations_total",
    "Total source degradations",
    ("source", "reason"),
)

source_availability = Gauge(
    "datacore_source_availability",
    "Source availability (0/1)",
    ("source",),
)

cache_hits_total = Counter(
    "datacore_cache_hits_total",
    "Total cache hits",
)

cache_misses_total = Counter(
    "datacore_cache_misses_total",
    "Total cache misses",
)

resampler_operations_total = Counter(
    "datacore_resampler_operations_total",
    "Total resampler operations",
    ("source_period", "target_period"),
)

issues_open = Gauge(
    "datacore_issues_open",
    "Open issues count",
    ("issue_type",),
)

tool_invocations_total = Counter(
    "datacore_tool_invocations_total",
    "Total tool invocations",
    ("tool_name",),
)

tool_errors_total = Counter(
    "datacore_tool_errors_total",
    "Total tool errors",
    ("tool_name",),
)


# ============================================================
#  辅助函数
# ============================================================

def _normalize_label(val: Any) -> str:
    """将 enum 或其他值转换为 label 字符串。"""
    if hasattr(val, "value"):
        return str(val.value)
    if val is None:
        return ""
    return str(val)


def _record_api_success(symbol: str, data_type: Any,
                        duration: float, result: Any) -> None:
    """记录 API 成功调用指标。"""
    market = ""
    if result is not None and hasattr(result, "market"):
        market = _normalize_label(result.market)

    data_type_str = _normalize_label(data_type)
    api_requests_total.inc(
        symbol=symbol, data_type=data_type_str, market=market
    )
    api_request_duration_seconds.observe(
        duration, symbol=symbol, data_type=data_type_str
    )

    # 缓存命中检测：通过 payload.grade 判断
    is_cache_hit = False
    if result is not None and hasattr(result, "grade"):
        grade = result.grade
        grade_str = _normalize_label(grade)
        if grade_str == "cached":
            is_cache_hit = True

    if is_cache_hit:
        cache_hits_total.inc()
    else:
        cache_misses_total.inc()


def _record_api_failure(symbol: str, data_type: Any,
                        duration: float, error: BaseException) -> None:
    """记录 API 失败调用指标。"""
    data_type_str = _normalize_label(data_type)
    api_requests_total.inc(
        symbol=symbol, data_type=data_type_str, market=""
    )
    api_request_duration_seconds.observe(
        duration, symbol=symbol, data_type=data_type_str
    )
    api_errors_total.inc(
        symbol=symbol,
        data_type=data_type_str,
        error_type=type(error).__name__,
    )
    cache_misses_total.inc()


def record_resampler_operation(source_period: str, target_period: str) -> None:
    """记录一次重采样操作。供 resampler 模块调用。"""
    resampler_operations_total.inc(
        source_period=source_period, target_period=target_period
    )


def update_issues_open(unresolved_by_type: dict[str, int]) -> None:
    """更新未解决问题 gauge。供 issue 模块调用。"""
    for issue_type, count in unresolved_by_type.items():
        issues_open.set(count, issue_type=issue_type)


def update_source_availability(source: str, available: bool) -> None:
    """更新数据源可用性 gauge。"""
    source_availability.set(1.0 if available else 0.0, source=source)


# ============================================================
#  装饰器
# ============================================================

def observe_api_call(func: Callable) -> Callable:
    """API 调用观测装饰器。

    用于 UnifiedDataProvider.get() 方法，自动记录:
    - 调用次数 (Counter)
    - 延迟分布 (Histogram)
    - 成功/失败 (Counter)
    - 缓存命中/未命中 (Counter)

    所有指标记录包裹在 try/except 中，不影响业务逻辑。
    """
    @functools.wraps(func)
    def wrapper(self, symbol: str, data_type: Any,
                params: Optional[dict] = None, *args: Any,
                **kwargs: Any) -> Any:
        start = time.time()
        try:
            result = func(self, symbol, data_type, params, *args, **kwargs)
            duration = time.time() - start
            try:
                _record_api_success(symbol, data_type, duration, result)
            except Exception:
                pass
            return result
        except Exception as e:
            duration = time.time() - start
            try:
                _record_api_failure(symbol, data_type, duration, e)
            except Exception:
                pass
            raise
    return wrapper


def observe_tool_call(func: Callable) -> Callable:
    """Tool 调用观测装饰器。

    用于 DataCoreBaseTool.invoke() 方法，自动记录:
    - Tool 调用次数 (Counter)
    - Tool 错误次数 (Counter)

    所有指标记录包裹在 try/except 中，不影响业务逻辑。
    """
    @functools.wraps(func)
    def wrapper(self: Any, input: Optional[dict] = None,
                config: Any = None, **kwargs: Any) -> Any:
        tool_name = getattr(self, "name", "") or ""
        try:
            result = func(self, input, config, **kwargs)
            try:
                tool_invocations_total.inc(tool_name=tool_name)
                # 结果中 success=False 也算错误
                if isinstance(result, dict) and not result.get("success", True):
                    tool_errors_total.inc(tool_name=tool_name)
            except Exception:
                pass
            return result
        except Exception:
            try:
                tool_invocations_total.inc(tool_name=tool_name)
                tool_errors_total.inc(tool_name=tool_name)
            except Exception:
                pass
            raise
    return wrapper


__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "HAS_PROMETHEUS_CLIENT",
    "generate_text",
    "observe_api_call",
    "observe_tool_call",
    "record_resampler_operation",
    "update_issues_open",
    "update_source_availability",
    "api_requests_total",
    "api_request_duration_seconds",
    "api_errors_total",
    "source_degradations_total",
    "source_availability",
    "cache_hits_total",
    "cache_misses_total",
    "resampler_operations_total",
    "issues_open",
    "tool_invocations_total",
    "tool_errors_total",
]
