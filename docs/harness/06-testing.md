# Data-Core Testing

Version: v0.4.0 | Updated: 2026-07-18

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

**总计: 13 个测试文件，184 个测试用例**

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

## 测试覆盖原则

1. **模型测试**: 所有数据模型必须有完整的字段验证测试
2. **降级测试**: LLM→规则降级、数据源降级链必须有测试
3. **边界测试**: 空输入、数据不足、异常输入必须有对应用例
4. **契约测试**: ProcessingStage 接口契约必须验证
5. **市场场景测试**: 牛市/熊市/横盘三种 regime 必须覆盖
6. **Mock 测试**: 外部数据源（HTTP/Socket）必须通过 mock 测试覆盖所有异常路径
7. **覆盖率目标**: 整体 ≥ 95%，核心模块（models/processing/api）≥ 100%
8. **熔断器测试**: 三种状态转换、超时、半开探测必须全覆盖（v0.4.0 新增）
