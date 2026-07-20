# Data-Core Testing

Version: v2.4.0 | Updated: 2026-07-20

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
| `tests/test_alert.py` | 24 | **告警引擎规则/渠道测试（v1.0.0 新增）** |
| `tests/benchmark_test.py` | 8 | **性能基准测试（v1.0.0 新增）** |
| `tests/test_phase1.py` | 28 | **Phase 1 综合测试（v1.1.0 新增）** |
| `tests/test_indicators.py` | 90 | **技术指标模块测试（v1.2.0 新增）** |
| `tests/test_indicators_extra.py` | 78 | **技术指标模块边界补充测试（v2.2.0 补充）** |
| `tests/test_futures_new_providers.py` | 20 | **新期货数据源测试（v1.2.0 新增）** |
| `tests/test_tools.py` | 89 | **BaseTool 接口层测试（v1.3.0 新增）** |
| `tests/test_adjustment.py` | 80 | **复权/换月引擎测试（v1.3.0 新增）** |
| `tests/test_resampler.py` | 74 | **周期转换引擎测试（v1.3.0 新增）** |
| `tests/test_issue.py` | 34 | **消费者反馈通道测试（v1.3.0 新增）** |
| `tests/test_cleaning.py` | 31 | **数据清洗模块测试（v1.3.0 新增）** |
| `tests/test_validation.py` | 27 | **数据校验模块测试（v1.3.0 新增）** |
| `tests/test_collectors.py` | 18 | **采集模块骨架测试（v1.3.0 新增）** |
| `tests/test_operations.py` | 19 | **运维工具模块测试（v1.3.0 新增）** |
| `tests/test_fdc_compat.py` | 68 | **FDT 兼容层测试（v2.0.0 新增）** |
| `tests/test_qlib_adapter.py` | 99 | **Qlib/RD-Agent 适配器测试（v2.0.0 新增）** |
| `tests/test_observability.py` | 19 | **Prometheus 可观测性测试（v2.2.0 新增）** |
| `tests/test_adjustment_provider.py` | 10 | **Provider adjustment 参数测试（v2.4.0 新增）** |
| `tests/test_equity.py` | 76 | 股票数据模块（v0.6.0 补充） |
| `tests/test_futures.py` | 18 | 期货数据模块 |
| `tests/test_cli.py` | 8 | CLI 命令行工具 |

**总计: 42 个测试文件，1974 个测试用例**

> 注：本次覆盖补充将 `tests/test_fdc_compat.py` 与 `tests/test_equity.py` 的用例数修正为实际收集值，并新增 21 个用例（fdc_compat +16，equity_provider +5）。
>
> 本次覆盖补充为 `tests/test_resampler.py` 新增 5 个用例，`tests/test_alert.py` 新增 6 个用例，覆盖 ohlcv.py 与 alert.py 的剩余未覆盖分支。

## v2.2.0 新增测试

v2.2.0 新增 `tests/test_observability.py`，覆盖 Prometheus 可观测性模块的三件套：observability.py 核心指标 + metrics_endpoint.py HTTP 端点 + metrics.py 的 _format_prometheus() 方法。

| 测试类 | 用例数 | 说明 |
|:-------|:-------|:-----|
| TestObservability | 11 | Counter/Gauge/Histogram 三种指标类型 + generate_text() exposition format + observe_api_call/observe_tool_call 装饰器（mock provider/tool）+ record_resampler_operation/update_issues_open/update_source_availability 辅助函数 |
| TestMetricsEndpoint | 5 | generate_metrics() 返回字符串/非空 + start_metrics_server 启动后可访问 /metrics + /healthz 返回 200 + 服务器可正常停止（幂等 stop） |
| TestPrometheusFormat | 3 | _format_prometheus() 输出包含 HELP/TYPE 注释 + 指标名以 datacore_ 开头 + 标签 {key="value"} 格式 |

**新增 19 个测试用例，总计 1437 个测试用例**

### v2.2.0 技术指标边界补充测试

补充 `tests/test_indicators_extra.py`，重点覆盖 `datacore/indicators/` 四个文件的边界分支、数据不足场景与未覆盖函数：

| 测试类 | 用例数 | 覆盖文件 |
|:-------|:-------|:---------|
| TestTdxCompatExtra | 22 | `datacore/indicators/tdx_compat.py` |
| TestCoreExtra | 35 | `datacore/indicators/core.py` |
| TestInitExtra | 13 | `datacore/indicators/__init__.py` |
| TestLegacyExtra | 8 | `datacore/indicators/legacy_numpy.py` |

**新增 78 个测试用例，总计 1515 个测试用例**

#### 技术指标补充测试覆盖原则
- TDX 对齐实现边界：空输入、周期非法、数据不足、价格=flat 等分支
- NumPy core 边界：`_shift`/`_rolling_window` 非法参数、各指标非法参数/数据不足返回全 NaN
- 统一入口路由：`use_tdx=True` 时缺少 high/low/volume 的降级路径、TA-Lib 兜底成功/异常分支
- 旧版兼容实现：数据不足场景与 `old_atr` 基本路径
- 剩余不可覆盖行说明：`__init__.py` 204/241 为当前指标映射下不可达的防御性 `return None`；core.py 152-155 与 tdx_compat.py 45/81-86 受 coverage 与 NumPy 2.2.6 `_NoValueType` 交互问题影响，普通 pytest 运行可正常覆盖

### v2.2.0 测试覆盖原则
- Counter/Gauge/Histogram 三种指标类型全覆盖（基本操作 + 标签维度）
- observe_api_call / observe_tool_call 装饰器使用 mock provider / mock tool 验证真实逻辑（不 mock 整个 observability 模块）
- generate_text() / generate_metrics() 输出格式符合 Prometheus exposition format 标准（HELP/TYPE 注释、指标名前缀、标签格式）
- HTTP 端点（/metrics、/healthz）使用 urllib.request 实际访问验证（端口 19090 避免冲突）
- 服务器资源清理（try/finally + stop 幂等）
- prometheus_client 可选依赖降级路径覆盖（HAS_PROMETHEUS_CLIENT 分支）

## v2.1.0 测试说明

v2.1.0 新增功能（API 层周期自动转换 + BaseTool args_schema）通过既有测试覆盖，测试总数保持 1418 个不变。

| 新增功能 | 覆盖方式 | 说明 |
|:---------|:---------|:-----|
| API 层周期自动转换 | test_resampler.py（69 个） + test_api.py | 复用 resampler 模块全量测试，API 层通过既有 api 测试覆盖 |
| BaseTool args_schema | test_tools.py（89 个） | 23 个 Tool 全覆盖，args_schema 作为可选能力集成测试 |

**测试覆盖原则**:
- API 层周期转换复用 resampler 模块的 69 个测试用例（全周期 + OHLCV 聚合 + auto 模式）
- args_schema 作为 Tool 的可选属性，集成在 23 个 Tool 的 89 个测试中
- pydantic 未安装时的降级路径通过既有 LangChain 兼容测试覆盖
- 测试总数保持 1418 个，无新增测试文件

## v2.0.0 新增测试

| 测试类 | 用例数 | 说明 |
|:-------|:-------|:-----|
| TestFdcCompatFunctions | 35 | FDC 兼容函数签名测试（get_kline/get_quote/get_fundamental/get_indicators 等） |
| TestFdcCompatFormat | 25 | 数据格式适配测试（DataFrame/Series/native 格式） |
| TestFdcCompatFieldMapping | 15 | 字段名映射测试（FDC 风格 ↔ Data-Core 风格） |
| TestFdcCompatErrorCodes | 12 | 错误码兼容测试 |
| TestFdcCompatMigration | 11 | 渐进式迁移 + 双轨运行测试 |
| TestQlibProviderCalendars | 15 | Qlib 交易日历接口测试 |
| TestQlibProviderInstruments | 15 | Qlib 品种池接口测试 |
| TestQlibProviderFeatures | 20 | Qlib 特征数据接口测试（OHLCV + 指标） |
| TestQlibProviderFundamentals | 15 | Qlib 基本面数据接口测试 |
| TestQlibExpressionEngine | 18 | Qlib 表达式引擎测试（Alpha158 等） |
| TestQlibConverter | 16 | 数据格式双向转换器测试（Data-Core ↔ Qlib） |

## v1.3.0 新增测试

| 测试类 | 用例数 | 说明 |
|:-------|:-------|:-----|
| TestBaseTool | 15 | DataCoreBaseTool 基类测试（LangChain 兼容 + 接口契约） |
| TestToolsDataAccess | 30 | 13 个数据获取 Tool 测试（OHLCV/Quote/Sentiment/Health 等） |
| TestToolsDataProcessing | 10 | 2 个数据处理 Tool 测试（Adjustment/Period） |
| TestToolsCleaning | 12 | 4 个数据清洗 Tool 测试（UnitUnify/DateAlign/DuplicateMerge/OutlierFilter） |
| TestToolsValidation | 10 | 3 个数据校验 Tool 测试（CrossSourceVerify/MissingDetect/CalMathCompute） |
| TestToolsOperations | 6 | 1 个运维 Tool 测试（ConfigRead） |
| TestToolsAutoDiscovery | 6 | all_tools 自动发现机制测试 |
| TestStockAdjustment | 25 | 股票复权测试（前复权/后复权/不复权） |
| TestFuturesRollover | 30 | 期货主力连续合约测试（成交量/持仓量/固定日换月） |
| TestSpreadAdjustment | 25 | 期货换月价差调整测试（前复权/后复权/等权） |
| TestResamplerPeriods | 35 | 全周期转换测试（1m→5m→15m→30m→60m→daily→weekly→monthly） |
| TestOHLCVAggregation | 20 | OHLCV 正确聚合测试（Open/High/Low/Close/Volume） |
| TestAutoDetector | 14 | auto 模式自动检测测试 |
| TestIssueRegistry | 15 | IssueRegistry 注册表测试（注册/查询/清理） |
| TestReportIssue | 8 | report_issue() API 测试 |
| TestIssueAutoDegrade | 8 | 自动降级应对测试（LOW/MEDIUM/HIGH/CRITICAL） |
| TestIssueHealthIntegration | 3 | get_health() consumer_issues 集成测试 |
| TestUnitUnify | 8 | 单位统一测试 |
| TestDateAlign | 8 | 日期对齐测试 |
| TestDuplicateMerge | 8 | 去重合并测试 |
| TestOutlierFilter | 7 | 异常值过滤测试（3σ / IQR） |
| TestWeightScore | 7 | 权重评分测试 |
| TestCrossSource | 7 | 跨源校验测试 |
| TestMissingDetect | 7 | 缺失检测测试 |
| TestCalMath | 6 | 计算校验测试 |
| TestWebCrawlCollector | 5 | 网页爬虫采集骨架测试 |
| TestOpenSourceCollector | 4 | 开源数据采集骨架测试 |
| TestLocalDocCollector | 5 | 本地文档采集骨架测试 |
| TestSearchCollector | 4 | 搜索采集骨架测试 |
| TestCrawlRetry | 7 | 爬取重试机制测试 |
| TestErrorLog | 6 | 错误日志收集测试 |
| TestConfigTools | 6 | 配置工具测试 |

## v1.2.0 新增测试

| 测试类 | 用例数 | 说明 |
|:-------|:-------|:-----|
| TestIndicatorsCore | 25 | 核心指标计算测试（MA/EMA/MACD/RSI/BOLL 等 37+ 指标） |
| TestIndicatorsTdxCompat | 20 | TDX 通达信对齐指标测试（精度验证） |
| TestIndicatorsTalibWrapper | 15 | TA-Lib 兜底层测试（降级路径验证） |
| TestTrendMaturity | 15 | 趋势成熟度评估测试（5 等级 + 牛/熊/横盘场景） |
| TestIndicatorsDegradation | 15 | 三层路由降级测试（TDX → numpy → TA-Lib） |
| TestQmtProvider | 7 | QMT 迅投资讯源 mock 测试 |
| TestWebFallbackProvider | 7 | WebFallback 网页备用源 mock 测试 |
| TestTqSdkProvider | 6 | TqSdk 兜底源 mock 测试 |

## v1.1.0 新增测试

| 测试类 | 用例数 | 说明 |
|:-------|:-------|:-----|
| TestAsyncDataProvider | 8 | AsyncDataProvider 异步双接口测试（kline/quote/f10） |
| TestF10Report | 8 | F10 综合报告聚合测试（期限结构/价差/基差/仓单/持仓排名） |
| TestCoreTypes | 6 | core/types.py 数据结构测试（KlineBar/QuoteData/FreshnessStatus） |
| TestDataFreshness | 6 | DataFreshnessAssessor 新鲜度评估测试（FRESH/STALE/EXPIRED） |

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
| 覆盖率 | ≥ 88% | ✅ 达标（v2.2.0: 88%，核心模块接近 100%） |

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
14. **异步接口测试**: AsyncDataProvider 异步方法 + run_in_executor 桥接必须覆盖（v1.1.0 新增）
15. **F10 报告测试**: F10 聚合逻辑 + 各子字段完整性必须覆盖（v1.1.0 新增）
16. **数据新鲜度测试**: FreshnessStatus 三级状态 + 阈值边界必须覆盖（v1.1.0 新增）
17. **core 模块测试**: KlineBar/QuoteData/FreshnessStatus 数据结构必须覆盖（v1.1.0 新增）
18. **技术指标测试**: 37+ 基础指标 + TDX 对齐 + TA-Lib 兜底三层路由必须全覆盖（v1.2.0 新增）
19. **趋势成熟度测试**: 5 个成熟度等级 + 牛/熊/横盘三种场景必须覆盖（v1.2.0 新增）
20. **新期货数据源测试**: QMT/WebFallback/TqSdk 三个新数据源的 mock 异常路径必须覆盖（v1.2.0 新增）
21. **指标降级测试**: TDX → numpy → TA-Lib 三层降级链每一层失败/恢复必须 mock 覆盖（v1.2.0 新增）
22. **BaseTool 接口测试**: DataCoreBaseTool 基类 + LangChain 协议兼容性必须全覆盖（v1.3.0 新增）
23. **23 个 Tool 全覆盖**: 每个 Tool 的正常/异常/边界路径必须覆盖（v1.3.0 新增）
24. **复权换月测试**: 股票复权（前/后/不复权）+ 期货换月（3 种方式）+ 价差调整（3 种方式）全覆盖（v1.3.0 新增）
25. **周期转换测试**: 全周期转换 + OHLCV 正确聚合 + auto 模式必须全覆盖（v1.3.0 新增）
26. **消费者反馈测试**: IssueRegistry + report_issue() + 四级自动降级应对必须全覆盖（v1.3.0 新增）
27. **数据清洗测试**: 4 种清洗工具（UnitUnify/DateAlign/DuplicateMerge/OutlierFilter）全覆盖（v1.3.0 新增）
28. **数据校验测试**: 4 种校验工具（WeightScore/CrossSource/MissingDetect/CalMath）全覆盖（v1.3.0 新增）
29. **all_tools 自动发现测试**: 自动发现机制 + 加载失败容错必须覆盖（v1.3.0 新增）
30. **FDT 兼容层测试**: FDC 函数签名 + 数据格式 + 错误码兼容必须全覆盖（v2.0.0 新增）
31. **Qlib 适配器测试**: Qlib DataProvider 完整接口 + 表达式引擎 + 格式转换必须全覆盖（v2.0.0 新增）
32. **终验标准**: 1418 测试全部通过，88% 覆盖率（核心模块接近 100%），ruff 零错误（v2.0.0 新增）
33. **API 层周期转换测试**: 复用 resampler 全量测试 + API 层集成测试，自动重采样 + 失败降级 + meta 记录必须覆盖（v2.1.0 新增）
34. **BaseTool args_schema 测试**: 23 个 Tool 的 args_schema + pydantic 可选依赖降级路径必须覆盖（v2.1.0 新增）
35. **Prometheus 可观测性测试**: Counter/Gauge/Histogram 三种指标类型 + 11 个标准指标 + observe_api_call/observe_tool_call 装饰器 + generate_metrics() exposition format + HTTP 端点（/metrics、/healthz、/）+ 线程安全 + prometheus_client 可选依赖降级必须全覆盖（v2.2.0 新增）
