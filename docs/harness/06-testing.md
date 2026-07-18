# Data-Core Testing

Version: v1.0.0 | Updated: 2026-07-19

## Test Files

| 测试文件 | 用例数 | 覆盖模块 |
|:---------|:-------|:---------|
| `tests/test_models.py` | 7 | 枚举/Payload/OHLCV 模型 |
| `tests/test_registry.py` | 5 | SymbolRegistry 品种注册表 |
| `tests/test_store.py` | 5 | MemoryCache 内存缓存 |
| `tests/test_futures_mock.py` | 11 | 期货数据源 mock 测试 |
| `tests/test_futures_models.py` | 18 | 期货数据模型 |
| `tests/test_equity_mock.py` | 4 | 股票数据源 mock 测试 |
| `tests/test_api.py` | 4 | UnifiedDataProvider 路由测试 |
| `tests/test_news.py` | 11 | 新闻分类器 + 新闻模型 |
| `tests/test_macro.py` | 3 | 宏观数据模型 |
| `tests/test_processing.py` | 36 | 数据加工层（情绪管线 + 市场制度） |
| `tests/test_breaker.py` | 30 | **熔断器（v0.4.0 新增）** |
| `tests/test_health.py` | 20 | **健康检查（v0.4.0 新增）** |
| `tests/test_metrics.py` | 30 | **指标收集（v0.4.0 新增）** |
| `tests/test_macro_providers.py` | 28 | **宏观数据源 mock（v0.5.0 新增）** |
| `tests/test_futures_providers.py` | 6 | **期货基本面 mock（v0.5.0 新增）** |
| `tests/test_guosen.py` | 7 | **国信证券 mock（v0.5.0 新增）** |
| `tests/test_news_providers.py` | 19 | **新闻数据源 mock（v0.5.0 新增）** |
| `tests/test_api_cache.py` | 12 | **缓存层测试（v0.5.0 新增）** |
| `tests/test_sentiment_llm.py` | 15 | **LLM 情绪打分端到端测试（v0.6.0 新增）** |
| `tests/test_fundamental_llm.py` | 12 | **基本面 LLM 加工测试（v0.6.0 新增）** |
| `tests/test_stream.py` | 15 | **WebSocket 连接/重连/订阅测试（v1.0.0 新增）** |
| `tests/test_alert.py` | 18 | **告警引擎规则/渠道测试（v1.0.0 新增）** |
| `tests/benchmark_test.py` | 8 | **性能基准测试（v1.0.0 新增）** |
| `tests/test_equity.py` | 10 | 股票数据模块（v0.6.0 补充） |
| `tests/test_futures.py` | 18 | 期货数据模块 |
| `tests/test_cli.py` | 8 | CLI 命令行工具 |

**总计: 26 个测试文件，724+ 个测试用例**

> 注：部分测试文件（如 test_equity.py, test_futures.py, test_cli.py）可能包含更多用例，实际总数可能超过 724。

## v1.0.0 新增测试

| 测试类 | 用例数 | 说明 |
|:-------|:-------|:-----|
| TestStreamConnection | 5 | WebSocket 连接/断开/重连测试 |
| TestStreamSubscribe | 5 | WebSocket 订阅/取消订阅测试 |
| TestStreamHeartbeat | 5 | WebSocket 心跳保活测试 |
| TestAlertRules | 6 | 告警规则触发测试（价格/波动率/延迟/熔断） |
| TestAlertChannels | 6 | 告警渠道通知测试（Webhook/文件/日志） |
| TestAlertDegradation | 6 | 告警渠道降级测试 |
| BenchmarkDataFetch | 2 | 数据获取性能基准 |
| BenchmarkCacheLayer | 2 | 缓存层性能基准 |
| BenchmarkProcessing | 2 | 数据加工性能基准 |
| BenchmarkConcurrency | 2 | 并发处理性能基准 |

## v0.6.0 新增测试

| 测试类 | 用例数 | 说明 |
|:-------|:-------|:-----|
| TestSentimentLLM | 15 | LLM 情绪打分端到端验证测试 |
| TestFundamentalLLM | 12 | 基本面 LLM 加工测试（研报摘要 + 财报提取） |

## v0.5.0 新增测试

| 测试类 | 用例数 | 说明 |
|:-------|:-------|:-----|
| TestNationalBureauProvider | 8 | 国家统计局数据源 mock 测试 |
| TestPboCProvider | 8 | 央行数据源 mock 测试 |
| TestMacroProviderDegradation | 12 | 宏观 3 源降级链 mock 测试 |
| TestExchangeApiProvider | 2 | 交易所官方数据源 mock 测试 |
| TestShengYiSheProvider | 4 | 生意社数据源 mock 测试 |
| TestGuosenProvider | 7 | 国信证券数据源 mock 测试 |
| TestClsProvider | 8 | 财联社新闻 mock 测试 |
| TestWallstreetProvider | 6 | 华尔街见闻 mock 测试 |
| TestEastMoneyResearchProvider | 5 | 东方财富研报 mock 测试 |
| TestCacheLayer | 12 | MemoryCache→DuckDB 双层缓存测试 |

## v0.4.0 新增测试

| 测试类 | 用例数 | 说明 |
|:-------|:-------|:-----|
| TestBreakerStateTransitions | 12 | CLOSED→OPEN→HALF_OPEN→CLOSED 完整状态转换 |
| TestBreakerTimeout | 6 | 超时触发熔断 |
| TestBreakerHalfOpenProbe | 6 | 半开探测成功/失败逻辑 |
| TestBreakerConfig | 6 | 自定义 max_failures/recovery_timeout |
| TestHealthBasic | 8 | get_health() 基本返回结构 |
| TestHealthSources | 8 | 各数据源状态探测 |
| TestHealthDegraded | 4 | 部分源不可用时整体 degraded 状态 |
| TestMetricsCounter | 8 | 调用次数统计（成功/失败） |
| TestMetricsLatency | 8 | 延迟 P50/P95/P99 统计 |
| TestMetricsCacheRate | 8 | 缓存命中率统计 |
| TestMetricsReport | 6 | MetricsCollector.report() 快照 |

## Run Tests

```bash
cd d:\Programs\data-core
python -m pytest tests/ -v
```

## Run Benchmarks

```bash
cd d:\Programs\data-core
python -m pytest tests/benchmark_test.py -v --benchmark
```

## 代码质量

| 工具 | 阈值 | 当前状态 |
|:-----|:-----|:---------|
| pylint | ≥ 9.50/10 | ✅ 达标 |
| mypy | 0 错误 | ✅ 达标 |
| ruff | 0 错误 | ✅ 达标 |
| 覆盖率 | ≥ 95% | ✅ 达标 |

## 测试覆盖原则

1. **模型测试**: 所有数据模型必须有完整的字段验证测试
2. **降级测试**: LLM→规则降级、数据源降级链、告警渠道降级必须有测试
3. **边界测试**: 空输入、数据不足、异常输入必须有对应用例
4. **契约测试**: ProcessingStage 接口契约必须验证
5. **市场场景测试**: 牛市/熊市/横盘三种 regime 必须覆盖
6. **Mock 测试**: 外部数据源（HTTP/Socket）必须通过 mock 测试覆盖所有异常路径
7. **覆盖率目标**: 整体 ≥ 95%，核心模块（models/processing/api）≥ 100%
8. **熔断器测试**: 三种状态转换、超时、半开探测必须全覆盖（v0.4.0 新增）
9. **缓存层测试**: MemoryCache→DuckDB 双层缓存读写一致性必须覆盖（v0.5.0 新增）
10. **降级链测试**: 多源降级链每个环节的失败/恢复必须 mock 覆盖（v0.5.0 新增）
11. **WebSocket 测试**: 连接/断开/重连/心跳/订阅必须覆盖（v1.0.0 新增）
12. **告警测试**: 规则触发/渠道通知/渠道降级必须覆盖（v1.0.0 新增）
13. **基准测试**: 数据获取/缓存/加工/并发性能基准必须覆盖（v1.0.0 新增）
