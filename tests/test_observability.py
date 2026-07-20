"""Tests for datacore.observability / datacore.metrics_endpoint / metrics._format_prometheus。

覆盖 Prometheus 可观测性三件套：
- datacore/observability.py — Counter/Gauge/Histogram + 装饰器 + 辅助函数
- datacore/metrics_endpoint.py — HTTP /metrics 端点
- datacore/metrics.py 的 _format_prometheus() — Prometheus exposition 格式
"""
from __future__ import annotations

import time
import urllib.error
import urllib.request
from typing import Any
from unittest import mock

from datacore.metrics import MetricsCollector
from datacore.metrics_endpoint import (
    generate_metrics,
    start_metrics_server,
)
from datacore.models.enums import DataType, MarketType, SourceGrade
from datacore.observability import (
    Counter,
    Gauge,
    HAS_PROMETHEUS_CLIENT,
    Histogram,
    generate_text,
    observe_api_call,
    observe_tool_call,
    record_resampler_operation,
    update_issues_open,
    update_source_availability,
)


# ============================================================
#  辅助类 — mock provider / mock tool
# ============================================================


class _MockResult:
    """模拟 DataPayload，供 observe_api_call 装饰器测试使用。"""

    market = MarketType.FUTURES
    grade = SourceGrade.PRIMARY


class _MockProvider:
    """模拟 UnifiedDataProvider，含 observe_api_call 装饰的 get()。"""

    name = "mock_provider"

    @observe_api_call
    def get(
        self,
        symbol: str,
        data_type: Any,
        params: Any = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        return _MockResult()


class _MockTool:
    """模拟 BaseTool，含 observe_tool_call 装饰的 invoke()。"""

    name = "mock_tool"

    @observe_tool_call
    def invoke(
        self,
        input: Any = None,
        config: Any = None,
        **kwargs: Any,
    ) -> Any:
        return {"success": True, "result": "ok"}


# ============================================================
#  Fake prometheus_client — 用于模拟官方库存在时的路径
# ============================================================


class _FakePromCounter:
    """模拟 prometheus_client.Counter。"""

    def __init__(self, name: str, documentation: str, labelnames: list[str]):
        self.name = name
        self.documentation = documentation
        self.labelnames = labelnames
        self._label_calls: list[dict] = []
        self._inc_calls: list[float] = []

    def labels(self, **kwargs):
        self._label_calls.append(kwargs)
        return self

    def inc(self, amount: float = 1.0):
        self._inc_calls.append(amount)


class _FakePromGauge:
    """模拟 prometheus_client.Gauge。"""

    def __init__(self, name: str, documentation: str, labelnames: list[str]):
        self.name = name
        self.documentation = documentation
        self.labelnames = labelnames
        self._label_calls: list[dict] = []
        self._set_calls: list[float] = []
        self._inc_calls: list[float] = []
        self._dec_calls: list[float] = []

    def labels(self, **kwargs):
        self._label_calls.append(kwargs)
        return self

    def set(self, value: float):
        self._set_calls.append(value)

    def inc(self, amount: float = 1.0):
        self._inc_calls.append(amount)

    def dec(self, amount: float = 1.0):
        self._dec_calls.append(amount)


class _FakePromHistogram:
    """模拟 prometheus_client.Histogram。"""

    def __init__(self, name: str, documentation: str, labelnames: list[str]):
        self.name = name
        self.documentation = documentation
        self.labelnames = labelnames
        self._label_calls: list[dict] = []
        self._observe_calls: list[float] = []

    def labels(self, **kwargs):
        self._label_calls.append(kwargs)
        return self

    def observe(self, value: float):
        self._observe_calls.append(value)


class _FakePrometheusClient:
    """模拟 prometheus_client 模块。"""

    Counter = _FakePromCounter
    Gauge = _FakePromGauge
    Histogram = _FakePromHistogram

    @staticmethod
    def generate_latest() -> bytes:
        return b"# fake prometheus generate_latest\n"


# ============================================================
#  TestObservability — 可观测性核心
# ============================================================


class TestObservability:
    """可观测性核心模块测试。"""

    def test_counter_increment(self):
        """Counter 递增正确。"""
        c = Counter(
            "datacore_test_counter_inc_total",
            "Test counter for increment",
            ("label_a",),
        )
        c.inc(label_a="alpha")
        c.inc(2.5, label_a="alpha")
        c.inc(label_a="beta")

        text = generate_text()
        assert "datacore_test_counter_inc_total" in text

        # 自定义实现可直接访问内部状态
        if not HAS_PROMETHEUS_CLIENT:
            items = dict(c._impl.collect())
            assert items.get(("alpha",)) == 3.5
            assert items.get(("beta",)) == 1.0

    def test_gauge_set(self):
        """Gauge 设置正确。"""
        g = Gauge(
            "datacore_test_gauge_set",
            "Test gauge set",
            ("tag",),
        )
        g.set(42.0, tag="x")
        g.set(-7.5, tag="y")
        g.inc(1.0, tag="x")  # 42 + 1 = 43

        text = generate_text()
        assert "datacore_test_gauge_set" in text

        if not HAS_PROMETHEUS_CLIENT:
            items = dict(g._impl.collect())
            assert items.get(("x",)) == 43.0
            assert items.get(("y",)) == -7.5

    def test_histogram_observe(self):
        """Histogram 观测正确。"""
        h = Histogram(
            "datacore_test_histogram_obs",
            "Test histogram observe",
            ("sym",),
        )
        h.observe(0.05, sym="A")
        h.observe(0.5, sym="A")
        h.observe(2.0, sym="A")

        text = generate_text()
        assert "datacore_test_histogram_obs_bucket" in text
        assert "datacore_test_histogram_obs_sum" in text
        assert "datacore_test_histogram_obs_count" in text

        if not HAS_PROMETHEUS_CLIENT:
            # 三次观测均落到不同 bucket，total/sum 必须正确
            assert h._impl._totals.get(("A",)) == 3
            assert abs(h._impl._sums.get(("A",)) - 2.55) < 1e-9
            # +Inf bucket 等于总观测数
            assert h._impl._totals.get(("A",)) == 3

    def test_generate_text(self):
        """generate_text() 返回标准 Prometheus 格式字符串。"""
        text = generate_text()
        assert isinstance(text, str)
        assert len(text) > 0
        # Prometheus exposition format 每行以 \n 结尾
        assert text.endswith("\n")

    def test_generate_text_contains_help(self):
        """generate_text() 输出包含 # HELP 行。"""
        text = generate_text()
        assert "# HELP " in text

    def test_generate_text_contains_type(self):
        """generate_text() 输出包含 # TYPE 行。"""
        text = generate_text()
        assert "# TYPE " in text

    def test_observe_api_call_decorator(self):
        """observe_api_call 装饰器正常工作（mock provider）。"""
        provider = _MockProvider()
        result = provider.get("RB", DataType.OHLCV, {"limit": 10})

        # 装饰器不影响返回值
        assert isinstance(result, _MockResult)

        # 调用后 generate_text() 应包含 API 请求指标
        text = generate_text()
        assert "datacore_api_requests_total" in text
        assert 'symbol="RB"' in text
        assert 'data_type="ohlcv"' in text
        assert 'market="futures"' in text

    def test_observe_tool_call_decorator(self):
        """observe_tool_call 装饰器正常工作（mock tool）。"""
        tool = _MockTool()
        result = tool.invoke({"x": 1})

        # 装饰器不影响返回值
        assert result["success"] is True

        # 调用后 generate_text() 应包含 tool 调用指标
        text = generate_text()
        assert "datacore_tool_invocations_total" in text
        assert 'tool_name="mock_tool"' in text

    def test_record_resampler_operation(self):
        """record_resampler_operation 记录重采样指标正确。"""
        record_resampler_operation("1m", "5m")
        record_resampler_operation("1m", "5m")
        record_resampler_operation("daily", "weekly")

        text = generate_text()
        assert "datacore_resampler_operations_total" in text
        assert 'source_period="1m"' in text
        assert 'target_period="5m"' in text
        assert 'source_period="daily"' in text
        assert 'target_period="weekly"' in text

    def test_update_issues_open(self):
        """update_issues_open 更新问题数 gauge 正确。"""
        update_issues_open({"data_quality": 5, "missing_data": 3})

        text = generate_text()
        assert "datacore_issues_open" in text
        assert 'issue_type="data_quality"' in text
        assert 'issue_type="missing_data"' in text

    def test_update_source_availability(self):
        """update_source_availability 更新数据源可用性 gauge 正确。"""
        update_source_availability("eastmoney", True)
        update_source_availability("tdx_local", False)

        text = generate_text()
        assert "datacore_source_availability" in text
        assert 'source="eastmoney"' in text
        assert 'source="tdx_local"' in text


# ============================================================
#  TestObservabilityEdgeCases — 可观测性边界与异常分支
# ============================================================


class TestObservabilityEdgeCases:
    """可观测性边界与异常分支测试。"""

    def test_prometheus_client_installed_import_path(self):
        """模拟 prometheus_client 已安装，覆盖导入时 HAS_PROMETHEUS_CLIENT=True 分支。"""
        fake_pc = _FakePrometheusClient()
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", True), \
             mock.patch("datacore.observability._pc", fake_pc):
            c = Counter("datacore_test_native_counter", "test", ("a",))
            c.inc(a="x")
            assert c._is_pc is True
            assert len(c._impl._label_calls) == 1

            g = Gauge("datacore_test_native_gauge", "test", ("a",))
            g.dec(2.0, a="x")
            assert g._is_pc is True
            assert len(g._impl._label_calls) == 1
            assert g._impl._inc_calls == [-2.0]

            h = Histogram("datacore_test_native_hist", "test", ("a",))
            h.observe(0.1, a="x")
            assert h._is_pc is True
            assert len(h._impl._label_calls) == 1
            assert h._impl._observe_calls == [0.1]

            text = generate_text()
            assert text == "# fake prometheus generate_latest\n"

    def test_counter_with_prometheus_client(self):
        """HAS_PROMETHEUS_CLIENT=True 时 Counter 走原生实现。"""
        fake_pc = _FakePrometheusClient()
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", True), \
             mock.patch("datacore.observability._pc", fake_pc):
            c = Counter("datacore_test_pc_counter", "test", ("a",))
            c.inc(a="x")
            c.inc(2.5, a="x")
            assert c._is_pc is True
            assert len(c._impl._label_calls) == 2
            assert c._impl._inc_calls == [1.0, 2.5]

    def test_counter_native_without_labels(self):
        """原生 Counter 无 label 时直接调用 _impl.inc(amount)。"""
        fake_pc = _FakePrometheusClient()
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", True), \
             mock.patch("datacore.observability._pc", fake_pc):
            c = Counter("datacore_test_pc_counter_no_labels", "test")
            c.inc()
            c.inc(3.0)
            assert c._is_pc is True
            assert c._impl._inc_calls == [1.0, 3.0]
            assert c._impl._label_calls == []

    def test_gauge_with_prometheus_client(self):
        """HAS_PROMETHEUS_CLIENT=True 时 Gauge 走原生实现（含 dec）。"""
        fake_pc = _FakePrometheusClient()
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", True), \
             mock.patch("datacore.observability._pc", fake_pc):
            g = Gauge("datacore_test_pc_gauge", "test", ("a",))
            g.set(5.0, a="x")
            g.inc(1.0, a="x")
            g.dec(2.0, a="x")
            assert g._is_pc is True
            assert g._impl._set_calls == [5.0]
            assert g._impl._inc_calls == [1.0, -2.0]

    def test_gauge_native_without_labels(self):
        """原生 Gauge 无 label 时直接调用 _impl.set/inc。"""
        fake_pc = _FakePrometheusClient()
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", True), \
             mock.patch("datacore.observability._pc", fake_pc):
            g = Gauge("datacore_test_pc_gauge_no_labels", "test")
            g.set(5.0)
            g.inc(1.0)
            g.dec(2.0)
            assert g._is_pc is True
            assert g._impl._set_calls == [5.0]
            assert g._impl._inc_calls == [1.0, -2.0]
            assert g._impl._label_calls == []

    def test_histogram_with_prometheus_client(self):
        """HAS_PROMETHEUS_CLIENT=True 时 Histogram 走原生实现。"""
        fake_pc = _FakePrometheusClient()
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", True), \
             mock.patch("datacore.observability._pc", fake_pc):
            h = Histogram("datacore_test_pc_hist", "test", ("a",))
            h.observe(0.1, a="x")
            h.observe(0.5, a="x")
            assert h._is_pc is True
            assert len(h._impl._label_calls) == 2
            assert h._impl._observe_calls == [0.1, 0.5]

    def test_histogram_native_without_labels(self):
        """原生 Histogram 无 label 时直接调用 _impl.observe(value)。"""
        fake_pc = _FakePrometheusClient()
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", True), \
             mock.patch("datacore.observability._pc", fake_pc):
            h = Histogram("datacore_test_pc_hist_no_labels", "test")
            h.observe(0.1)
            h.observe(0.5)
            assert h._is_pc is True
            assert h._impl._observe_calls == [0.1, 0.5]
            assert h._impl._label_calls == []

    def test_generate_text_with_prometheus_client(self):
        """HAS_PROMETHEUS_CLIENT=True 时 generate_text 调用原生 generate_latest。"""
        fake_pc = _FakePrometheusClient()
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", True), \
             mock.patch("datacore.observability._pc", fake_pc):
            text = generate_text()
            assert text == "# fake prometheus generate_latest\n"

    def test_custom_counter_exception_silenced(self):
        """_CustomCounter.inc 内部异常被静默，不影响业务。"""
        c = Counter("datacore_test_exc_counter", "test", ("a",))
        with mock.patch(
            "datacore.observability._normalize_label",
            side_effect=RuntimeError("boom"),
        ):
            c.inc(a="x")

    def test_custom_gauge_exception_silenced(self):
        """_CustomGauge.set/inc 内部异常被静默。"""
        g = Gauge("datacore_test_exc_gauge", "test", ("a",))
        with mock.patch(
            "datacore.observability._normalize_label",
            side_effect=RuntimeError("boom"),
        ):
            g.set(1.0, a="x")
            g.inc(1.0, a="x")

    def test_custom_histogram_exception_silenced(self):
        """_CustomHistogram.observe 内部异常被静默。"""
        h = Histogram("datacore_test_exc_hist", "test", ("a",))
        with mock.patch(
            "datacore.observability._normalize_label",
            side_effect=RuntimeError("boom"),
        ):
            h.observe(0.1, a="x")

    def _raising(self, msg: str):
        """构造一个调用即抛错的可调用对象。"""
        def _func(*args, **kwargs):
            raise RuntimeError(msg)
        return _func

    def test_counter_native_exception_silenced(self):
        """Counter 原生路径内部异常被静默。"""
        fake_pc = _FakePrometheusClient()
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", True), \
             mock.patch("datacore.observability._pc", fake_pc):
            c = Counter("datacore_test_pc_exc_counter", "test", ("a",))
            c._impl.labels().inc = self._raising("boom")
            c.inc(a="x")

    def test_gauge_native_exception_silenced(self):
        """Gauge 原生路径内部异常被静默。"""
        fake_pc = _FakePrometheusClient()
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", True), \
             mock.patch("datacore.observability._pc", fake_pc):
            g = Gauge("datacore_test_pc_exc_gauge", "test", ("a",))
            g._impl.labels().set = self._raising("boom")
            g._impl.labels().inc = self._raising("boom")
            g.set(1.0, a="x")
            g.inc(1.0, a="x")
            g.dec(1.0, a="x")

    def test_histogram_native_exception_silenced(self):
        """Histogram 原生路径内部异常被静默。"""
        fake_pc = _FakePrometheusClient()
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", True), \
             mock.patch("datacore.observability._pc", fake_pc):
            h = Histogram("datacore_test_pc_exc_hist", "test", ("a",))
            h._impl.labels().observe = self._raising("boom")
            h.observe(0.1, a="x")

    def test_gauge_dec_custom(self):
        """Gauge.dec 通过 inc(-amount) 实现。"""
        g = Gauge("datacore_test_gauge_dec", "test", ("tag",))
        g.set(10.0, tag="x")
        g.dec(3.0, tag="x")
        if not HAS_PROMETHEUS_CLIENT:
            items = dict(g._impl.collect())
            assert items.get(("x",)) == 7.0

    def test_custom_gauge_dec_directly(self):
        """直接调用 _CustomGauge.dec 覆盖内部实现。"""
        from datacore.observability import _CustomGauge

        cg = _CustomGauge("datacore_test_custom_gauge_dec_direct", "test", ("tag",))
        cg.set(10.0, tag="x")
        cg.dec(3.0, tag="x")
        items = dict(cg.collect())
        assert items.get(("x",)) == 7.0

    def test_histogram_without_labels(self):
        """无 label 的 Histogram 输出 sum/count 行（无花括号）。"""
        h = Histogram("datacore_test_hist_no_labels", "test")
        h.observe(0.05)
        h.observe(0.5)
        text = generate_text()
        assert "datacore_test_hist_no_labels_sum " in text
        assert "datacore_test_hist_no_labels_count " in text

    def test_custom_metric_base_format_exposition(self):
        """_CustomMetric.format_exposition 应抛出 NotImplementedError。"""
        from datacore.observability import _CustomMetric

        m = _CustomMetric("base_metric", "test")
        raised = False
        try:
            m.format_exposition()
        except NotImplementedError:
            raised = True
        assert raised

    def test_format_label_value_enum(self):
        """_format_label_value 处理 enum.value 分支。"""
        from datacore.observability import _format_label_value

        assert _format_label_value(DataType.OHLCV) == "ohlcv"

    def test_format_label_value_none(self):
        """_format_label_value 处理 None 为空字符串。"""
        from datacore.observability import _format_label_value

        assert _format_label_value(None) == ""

    def test_normalize_label_enum(self):
        """_normalize_label 处理 enum.value 分支。"""
        from datacore.observability import _normalize_label

        assert _normalize_label(DataType.OHLCV) == "ohlcv"

    def test_normalize_label_none(self):
        """_normalize_label 处理 None 为空字符串。"""
        from datacore.observability import _normalize_label

        assert _normalize_label(None) == ""

    def test_observe_api_call_success_exception_silenced(self):
        """observe_api_call 成功路径指标记录异常被静默，不影响返回值。"""
        provider = _MockProvider()
        with mock.patch(
            "datacore.observability._record_api_success",
            side_effect=RuntimeError("boom"),
        ):
            result = provider.get("RB", DataType.OHLCV)
            assert isinstance(result, _MockResult)

    def test_observe_api_call_failure_exception_silenced(self):
        """observe_api_call 失败路径指标记录异常被静默，原异常继续抛出。"""

        class _FailProvider:
            @observe_api_call
            def get(self, symbol, data_type, params=None, *args, **kwargs):
                raise ValueError("intentional")

        provider = _FailProvider()
        with mock.patch(
            "datacore.observability._record_api_failure",
            side_effect=RuntimeError("boom"),
        ):
            try:
                provider.get("RB", DataType.OHLCV)
                assert False, "应抛出 ValueError"
            except ValueError as e:
                assert str(e) == "intentional"

    def test_observe_api_call_failure_records_metrics(self):
        """observe_api_call 失败时 _record_api_failure 正常记录指标。"""

        class _FailProvider:
            @observe_api_call
            def get(self, symbol, data_type, params=None, *args, **kwargs):
                raise ValueError("intentional")

        provider = _FailProvider()
        try:
            provider.get("RB", DataType.OHLCV)
            assert False, "应抛出 ValueError"
        except ValueError:
            pass

        text = generate_text()
        assert "datacore_api_errors_total" in text
        assert 'error_type="ValueError"' in text

    def test_observe_api_call_cache_hit(self):
        """observe_api_call 检测到 grade=cached 时记录 cache_hits_total。"""

        class _CachedResult:
            market = MarketType.FUTURES
            grade = SourceGrade.CACHED

        class _CachedProvider:
            @observe_api_call
            def get(self, symbol, data_type, params=None, *args, **kwargs):
                return _CachedResult()

        provider = _CachedProvider()
        result = provider.get("RB", DataType.OHLCV)
        assert result.grade == SourceGrade.CACHED

        text = generate_text()
        assert "datacore_cache_hits_total" in text

    def test_observe_tool_call_success_exception_silenced(self):
        """observe_tool_call 成功路径指标记录异常被静默，不影响返回值。"""
        tool = _MockTool()
        with mock.patch(
            "datacore.observability.tool_invocations_total.inc",
            side_effect=RuntimeError("boom"),
        ):
            result = tool.invoke({"x": 1})
            assert result["success"] is True

    def test_observe_tool_call_fail_result_records_error(self):
        """observe_tool_call 对 success=False 结果记录 tool_errors_total。"""

        class _FailResultTool:
            name = "mock_tool_fail_result"

            @observe_tool_call
            def invoke(self, input=None, config=None, **kwargs):
                return {"success": False, "error": "oops"}

        tool = _FailResultTool()
        result = tool.invoke({"x": 1})
        assert result["success"] is False
        text = generate_text()
        assert "datacore_tool_errors_total" in text
        assert 'tool_name="mock_tool_fail_result"' in text

    def test_observe_tool_call_error_inc_exception_silenced(self):
        """observe_tool_call 失败结果中 tool_errors_total.inc 异常被静默。"""

        class _FailResultTool:
            name = "mock_tool_fail_result_exc"

            @observe_tool_call
            def invoke(self, input=None, config=None, **kwargs):
                return {"success": False, "error": "oops"}

        tool = _FailResultTool()
        with mock.patch(
            "datacore.observability.tool_errors_total.inc",
            side_effect=RuntimeError("boom"),
        ):
            result = tool.invoke({"x": 1})
            assert result["success"] is False

    def test_observe_tool_call_invoke_exception_silenced(self):
        """observe_tool_call 在 invoke 抛错时指标记录异常被静默，原异常继续抛出。"""

        class _RaiseTool:
            name = "mock_tool_raise"

            @observe_tool_call
            def invoke(self, input=None, config=None, **kwargs):
                raise ValueError("tool error")

        tool = _RaiseTool()
        with mock.patch(
            "datacore.observability.tool_invocations_total.inc",
            side_effect=RuntimeError("boom"),
        ):
            try:
                tool.invoke({"x": 1})
                assert False, "应抛出 ValueError"
            except ValueError as e:
                assert str(e) == "tool error"

    def test_observe_tool_call_invoke_records_errors(self):
        """observe_tool_call 在 invoke 抛错时正常记录调用和错误指标。"""

        class _RaiseTool:
            name = "mock_tool_raise_record"

            @observe_tool_call
            def invoke(self, input=None, config=None, **kwargs):
                raise ValueError("tool error")

        tool = _RaiseTool()
        try:
            tool.invoke({"x": 1})
            assert False, "应抛出 ValueError"
        except ValueError:
            pass

        text = generate_text()
        assert "datacore_tool_invocations_total" in text
        assert "datacore_tool_errors_total" in text
        assert 'tool_name="mock_tool_raise_record"' in text


# ============================================================
#  TestMetricsEndpoint — HTTP 端点
# ============================================================

# 端口 19090 避免与默认 9090 冲突
_TEST_PORT = 19090
_TEST_HOST = "127.0.0.1"


def _fetch_url(url: str, timeout: float = 3.0) -> tuple[int, str]:
    """用 urllib 请求 url，返回 (status_code, body)。"""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return e.code, body


def _wait_server_ready(host: str, port: int, max_retries: int = 30) -> bool:
    """轮询等待服务器就绪。"""
    for _ in range(max_retries):
        try:
            with urllib.request.urlopen(
                f"http://{host}:{port}/healthz", timeout=0.5
            ) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.05)
    return False


class TestMetricsEndpoint:
    """HTTP 端点测试。"""

    def test_generate_metrics(self):
        """generate_metrics() 返回字符串。"""
        text = generate_metrics()
        assert isinstance(text, str)

    def test_generate_metrics_not_empty(self):
        """generate_metrics() 返回内容不为空。"""
        text = generate_metrics()
        assert len(text) > 0
        # 至少包含 HELP 或 TYPE 注释
        assert "# HELP " in text or "# TYPE " in text

    def test_start_metrics_server(self):
        """启动服务器后可访问 /metrics。"""
        server = start_metrics_server(port=_TEST_PORT, host=_TEST_HOST)
        try:
            assert server.is_running() is True
            assert _wait_server_ready(_TEST_HOST, _TEST_PORT) is True

            status, body = _fetch_url(f"http://{_TEST_HOST}:{_TEST_PORT}/metrics")
            assert status == 200
            assert isinstance(body, str)
            assert len(body) > 0
            # /metrics 必须返回 Prometheus exposition format
            assert "# HELP " in body or "# TYPE " in body
        finally:
            server.stop()

    def test_metrics_server_healthz(self):
        """/healthz 端点返回 200。"""
        server = start_metrics_server(port=_TEST_PORT, host=_TEST_HOST)
        try:
            assert _wait_server_ready(_TEST_HOST, _TEST_PORT) is True

            status, body = _fetch_url(f"http://{_TEST_HOST}:{_TEST_PORT}/healthz")
            assert status == 200
            assert "datacore" in body
        finally:
            server.stop()

    def test_metrics_server_stop(self):
        """服务器可正常停止。"""
        server = start_metrics_server(port=_TEST_PORT, host=_TEST_HOST)
        assert server.is_running() is True

        server.stop()
        assert server.is_running() is False

        # 重复 stop 不抛错（幂等）
        server.stop()


# ============================================================
#  TestMetricsEndpointEdgeCases — HTTP 端点边界与异常分支
# ============================================================


class TestMetricsEndpointEdgeCases:
    """HTTP 端点边界与异常分支测试。"""

    def test_metrics_server_500_on_generate_error(self):
        """generate_text 抛错时 /metrics 返回 500。"""
        server = start_metrics_server(port=_TEST_PORT, host=_TEST_HOST)
        try:
            assert _wait_server_ready(_TEST_HOST, _TEST_PORT) is True
            with mock.patch(
                "datacore.metrics_endpoint.generate_text",
                side_effect=RuntimeError("boom"),
            ):
                status, body = _fetch_url(
                    f"http://{_TEST_HOST}:{_TEST_PORT}/metrics"
                )
                assert status == 500
                assert "error generating metrics" in body
        finally:
            server.stop()

    def test_metrics_server_404(self):
        """访问未知路径返回 404。"""
        server = start_metrics_server(port=_TEST_PORT, host=_TEST_HOST)
        try:
            assert _wait_server_ready(_TEST_HOST, _TEST_PORT) is True
            status, body = _fetch_url(
                f"http://{_TEST_HOST}:{_TEST_PORT}/notfound"
            )
            assert status == 404
        finally:
            server.stop()

    def test_metrics_server_start_idempotent(self):
        """重复调用 start() 应直接返回，不抛错。"""
        server = start_metrics_server(port=_TEST_PORT, host=_TEST_HOST)
        try:
            assert server.is_running() is True
            server.start()
            assert server.is_running() is True
        finally:
            server.stop()


# ============================================================
#  TestPrometheusFormat — Prometheus 格式验证
# ============================================================


class TestPrometheusFormat:
    """Prometheus exposition 格式验证（基于 metrics._format_prometheus）。"""

    def test_format_has_help_type(self):
        """格式包含 HELP 和 TYPE 注释。"""
        collector = MetricsCollector()
        collector.record("endpoint_a", 0.1, success=True)
        collector.record("endpoint_a", 0.2, success=False)

        text = collector._format_prometheus()
        assert "# HELP " in text
        assert "# TYPE " in text
        # 应同时包含 counter 和 gauge 类型
        assert "# TYPE datacore_calls_total counter" in text
        assert "# TYPE datacore_success_rate gauge" in text

    def test_format_metric_naming(self):
        """所有指标名以 datacore_ 开头。"""
        collector = MetricsCollector()
        collector.record("api", 0.1, success=True)
        collector.record("db", 0.2, success=True)

        text = collector._format_prometheus()
        assert text != ""  # 必须有内容才能验证

        for line in text.strip().split("\n"):
            if not line or line.startswith("#"):
                continue
            # 形如 metric_name{labels} value 或 metric_name value
            metric_part = line.split("{", 1)[0].split()[0]
            assert metric_part.startswith("datacore_"), (
                f"metric '{metric_part}' 不以 datacore_ 开头"
            )

    def test_format_labels(self):
        """标签格式正确：{key="value"}。"""
        collector = MetricsCollector()
        collector.record("api_endpoint", 0.1, success=True)

        text = collector._format_prometheus()
        has_labeled_line = False

        for line in text.strip().split("\n"):
            if line.startswith("#"):
                continue
            if "{" in line and "}" in line:
                has_labeled_line = True
                # 提取 { ... } 部分
                label_str = line[line.index("{") + 1: line.index("}")]
                # 应包含 endpoint="api_endpoint" 形式的标签
                assert 'endpoint="api_endpoint"' in label_str

        assert has_labeled_line, "未找到任何带标签的指标行"


# ============================================================
#  TestCustomMetricsFallback — 自定义指标实现覆盖（无 prometheus_client）
# ============================================================


class TestCustomMetricsFallback:
    """自定义指标 fallback 实现测试 — 覆盖无 prometheus_client 时的代码路径。"""

    def test_custom_counter_full(self):
        """_CustomCounter 完整功能测试。"""
        from datacore.observability import _CustomCounter

        c = _CustomCounter("datacore_test_custom_counter_full", "test", ("tag",))
        c.inc(tag="a")
        c.inc(2.5, tag="a")
        c.inc(tag="b")

        items = dict(c.collect())
        assert items.get(("a",)) == 3.5
        assert items.get(("b",)) == 1.0

        text = c.format_exposition()
        assert "# HELP datacore_test_custom_counter_full" in text
        assert "# TYPE datacore_test_custom_counter_full counter" in text
        assert 'tag="a"' in text
        assert 'tag="b"' in text

    def test_custom_gauge_full(self):
        """_CustomGauge 完整功能测试。"""
        from datacore.observability import _CustomGauge

        g = _CustomGauge("datacore_test_custom_gauge_full", "test", ("tag",))
        g.set(10.0, tag="x")
        g.inc(2.0, tag="x")
        g.dec(3.0, tag="x")
        g.set(5.0, tag="y")

        items = dict(g.collect())
        assert items.get(("x",)) == 9.0
        assert items.get(("y",)) == 5.0

        text = g.format_exposition()
        assert "# HELP datacore_test_custom_gauge_full" in text
        assert "# TYPE datacore_test_custom_gauge_full gauge" in text
        assert 'tag="x"' in text
        assert 'tag="y"' in text

    def test_custom_histogram_full(self):
        """_CustomHistogram 完整功能测试（带标签和无标签）。"""
        from datacore.observability import _CustomHistogram

        h = _CustomHistogram("datacore_test_custom_hist_full", "test", ("sym",))
        h.observe(0.05, sym="A")
        h.observe(0.5, sym="A")
        h.observe(2.0, sym="A")

        assert h._totals.get(("A",)) == 3
        assert abs(h._sums.get(("A",)) - 2.55) < 1e-9

        text = h.format_exposition()
        assert "# HELP datacore_test_custom_hist_full" in text
        assert "# TYPE datacore_test_custom_hist_full histogram" in text
        assert 'sym="A"' in text
        assert "_bucket" in text
        assert "_sum" in text
        assert "_count" in text

    def test_custom_histogram_without_labels_full(self):
        """_CustomHistogram 无标签时输出正确格式。"""
        from datacore.observability import _CustomHistogram

        h = _CustomHistogram("datacore_test_custom_hist_no_labels_full", "test")
        h.observe(0.05)
        h.observe(0.5)

        text = h.format_exposition()
        assert "datacore_test_custom_hist_no_labels_full_sum " in text
        assert "datacore_test_custom_hist_no_labels_full_count " in text

    def test_format_labels(self):
        """_format_labels 格式化正确。"""
        from datacore.observability import _format_labels

        result = _format_labels(["a", "b"], ("x", "y"))
        assert result == '{a="x",b="y"}'

        result = _format_labels([], ())
        assert result == ""

    def test_format_label_value_special_chars(self):
        """_format_label_value 处理特殊字符。"""
        from datacore.observability import _format_label_value

        assert _format_label_value('hello"world') == 'hello\\"world'
        assert _format_label_value("hello\\world") == "hello\\\\world"

    def test_generate_text_without_prometheus_client(self):
        """generate_text 在无 prometheus_client 时使用自定义注册表。"""
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", False):
            text = generate_text()
            assert isinstance(text, str)

    def test_counter_fallback_path(self):
        """Counter 在 HAS_PROMETHEUS_CLIENT=False 时走自定义实现。"""
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", False), \
             mock.patch("datacore.observability._pc", None):
            c = Counter("datacore_test_counter_fallback", "test", ("a",))
            c.inc(a="x")
            assert c._is_pc is False

    def test_gauge_fallback_path(self):
        """Gauge 在 HAS_PROMETHEUS_CLIENT=False 时走自定义实现。"""
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", False), \
             mock.patch("datacore.observability._pc", None):
            g = Gauge("datacore_test_gauge_fallback", "test", ("a",))
            g.set(5.0, a="x")
            assert g._is_pc is False

    def test_histogram_fallback_path(self):
        """Histogram 在 HAS_PROMETHEUS_CLIENT=False 时走自定义实现。"""
        with mock.patch("datacore.observability.HAS_PROMETHEUS_CLIENT", False), \
             mock.patch("datacore.observability._pc", None):
            h = Histogram("datacore_test_hist_fallback", "test", ("a",))
            h.observe(0.1, a="x")
            assert h._is_pc is False
