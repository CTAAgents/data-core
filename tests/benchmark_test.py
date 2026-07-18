"""性能基准测试 — Data-Core 性能基线。

v1.0.0 新增: 单机 QPS / P50 / P95 / P99 延迟基准。

运行方式:
    pytest tests/benchmark_test.py -v --benchmark
    python -m pytest tests/benchmark_test.py -v --benchmark

注意: 这些测试因依赖外部 HTTP 源和缓存状态，仅做参考基线。
真正的压力测试请使用 locust 或自定义并发脚本。
"""
import pytest
import time
from typing import Any

# 标记为 benchmark 类型
pytestmark = pytest.mark.benchmark


class TestDataProviderBenchmark:
    """UnifiedDataProvider 基本操作基准测试。"""

    @pytest.fixture
    def provider(self):
        from datacore import UnifiedDataProvider
        return UnifiedDataProvider()

    def test_symbol_list_benchmark(self, provider):
        """list_symbols() 基准测试。"""
        from datacore.models.enums import MarketType
        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            provider.list_symbols()
            provider.list_symbols(MarketType.FUTURES)

        elapsed = time.perf_counter() - start
        ops = iterations * 2 / elapsed
        print(f"\n  list_symbols: {elapsed:.3f}s for {iterations*2} ops = {ops:.0f} ops/s")
        assert ops > 500, f"性能不足: {ops:.0f} ops/s < 500"

    def test_cache_operations_benchmark(self):
        """MemoryCache 操作基准测试。"""
        from datacore.store.cache import MemoryCache
        cache = MemoryCache(default_ttl=3600)
        iterations = 10000
        key_prefix = "bench_key_"

        # Set
        start = time.perf_counter()
        for i in range(iterations):
            cache.set(f"{key_prefix}{i}", {"data": i, "payload": "x" * 100})
        set_time = time.perf_counter() - start

        # Get (hit)
        start = time.perf_counter()
        for i in range(iterations):
            cache.get(f"{key_prefix}{i}")
        get_hit_time = time.perf_counter() - start

        # Get (miss)
        start = time.perf_counter()
        for i in range(iterations):
            cache.get(f"nonexistent_{i}")
        get_miss_time = time.perf_counter() - start

        print(f"\n  MemoryCache set({iterations}): {set_time:.3f}s = {iterations/set_time:.0f} ops/s")
        print(f"  MemoryCache get(hit, {iterations}): {get_hit_time:.3f}s = {iterations/get_hit_time:.0f} ops/s")
        print(f"  MemoryCache get(miss, {iterations}): {get_miss_time:.3f}s = {iterations/get_miss_time:.0f} ops/s")

        assert iterations / set_time > 10000, f"set 性能不足: {iterations/set_time:.0f}"

    def test_metrics_collector_benchmark(self):
        """MetricsCollector 基准测试。"""
        from datacore.metrics import MetricsCollector
        metrics = MetricsCollector()
        iterations = 10000

        start = time.perf_counter()
        for i in range(iterations):
            metrics.record(f"endpoint_{i % 100}", duration=0.1, success=True)
        record_time = time.perf_counter() - start

        start = time.perf_counter()
        snap = metrics.snapshot()
        snap_time = time.perf_counter() - start

        print(f"\n  MetricsCollector record({iterations}): {record_time:.3f}s = {iterations/record_time:.0f} ops/s")
        print(f"  MetricsCollector snapshot: {snap_time:.3f}s, {len(snap)} endpoints")
        assert iterations / record_time > 10000, f"record 性能不足: {iterations/record_time:.0f}"

    def test_registry_lookup_benchmark(self):
        """SymbolRegistry 解析基准测试。"""
        from datacore.registry.symbol_registry import SymbolRegistry
        registry = SymbolRegistry()
        symbols = ["RB", "CU", "AU", "M", "TA", "SC", "FG", "I", "J", "JM",
                   "HC", "AL", "ZN", "PB", "NI", "SN", "AG", "A", "B", "SR"]
        iterations = 10000

        start = time.perf_counter()
        for _ in range(iterations):
            for sym in symbols:
                registry.resolve(sym)
                registry.resolve_market(sym)
        elapsed = time.perf_counter() - start
        ops = iterations * len(symbols) * 2 / elapsed

        print(f"\n  SymbolRegistry resolve({iterations*len(symbols)*2}): {elapsed:.3f}s = {ops:.0f} ops/s")
        assert ops > 50000, f"性能不足: {ops:.0f} ops/s < 50000"

    def test_breaker_benchmark(self):
        """Breaker 基准测试。"""
        from datacore.breaker import Breaker
        breaker = Breaker("bench_breaker", max_failures=100)
        iterations = 5000

        def fast_fn():
            return 42

        start = time.perf_counter()
        for _ in range(iterations):
            breaker.call(fast_fn)
        elapsed = time.perf_counter() - start
        ops = iterations / elapsed

        print(f"\n  Breaker.call({iterations}): {elapsed:.3f}s = {ops:.0f} ops/s")
        assert ops > 1000, f"性能不足: {ops:.0f} ops/s < 1000"

    def test_model_construction_benchmark(self):
        """DataPayload 构建基准测试。"""
        from datacore.models.payload import DataPayload
        from datacore.models.enums import DataType, MarketType, SourceGrade
        iterations = 10000

        start = time.perf_counter()
        for _ in range(iterations):
            DataPayload(
                symbol="RB", data_type=DataType.OHLCV,
                market=MarketType.FUTURES,
                source="test", grade=SourceGrade.PRIMARY,
                collected_at=time.time(),
            )
        elapsed = time.perf_counter() - start
        ops = iterations / elapsed

        print(f"\n  DataPayload construct({iterations}): {elapsed:.3f}s = {ops:.0f} ops/s")
        assert ops > 50000, f"性能不足: {ops:.0f} ops/s < 50000"


class TestProcessingBenchmark:
    """数据加工层基准测试。"""

    def test_sentiment_rule_benchmark(self):
        """情绪规则基线基准测试。"""
        from datacore.processing.sentiment.sentiment_rule import SentimentRuleStage
        stage = SentimentRuleStage()
        texts = [
            "利好: 央行降息刺激经济，股市大幅上涨",
            "利空: 贸易摩擦升级，出口大幅下降",
            "中性: 今日市场窄幅震荡，成交量萎缩",
            "利好: 国家出台减税政策，企业盈利改善",
            "利空: 通胀压力增大，央行可能加息",
        ]
        iterations = 1000

        start = time.perf_counter()
        for _ in range(iterations):
            for text in texts:
                stage.process(text)
        elapsed = time.perf_counter() - start
        ops = iterations * len(texts) / elapsed

        print(f"\n  SentimentRuleStage({iterations*len(texts)}): {elapsed:.3f}s = {ops:.0f} ops/s")
        assert ops > 5000, f"性能不足: {ops:.0f} ops/s < 5000"

    def test_market_regime_benchmark(self):
        """市场制度检测基准测试。"""
        from datacore.processing.market_regime import MarketRegimeDetector
        detector = MarketRegimeDetector()
        # 生成 120 根 K 线
        candles = []
        for i in range(120):
            close = 3500 + i * 10 + (i % 5) * 20
            candles.append({
                "date": f"2026-{i//30+1:02d}-{i%30+1:02d}",
                "open": close - 10, "high": close + 20, "low": close - 30,
                "close": close, "volume": 10000 + i * 100,
            })
        iterations = 1000

        start = time.perf_counter()
        for _ in range(iterations):
            detector.process(candles, symbol="RB")
        elapsed = time.perf_counter() - start
        ops = iterations / elapsed

        print(f"\n  MarketRegimeDetector({iterations}): {elapsed:.3f}s = {ops:.0f} ops/s")
        assert ops > 500, f"性能不足: {ops:.0f} ops/s < 500"
