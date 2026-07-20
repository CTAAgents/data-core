# Data-Core Operations

Version: v2.4.0 | Updated: 2026-07-20

## Version History

| 版本 | 日期 | 变更说明 |
|:-----|:-----|:---------|
| **v2.4.0** | **2026-07-20** | **Provider adjustment 参数打通版：消费端可通过 adjustment="none" 获取未复权原始数据** |
| | | • 修复 Provider 层强制复权导致无法获取原始数据的 Bug（G34） |
| | | • tencent.py 股票 K 线支持 adjustment 参数：qfq/hfq/none（API: qfq/hfq/不带参数） |
| | | • eastmoney.py 股票 K 线支持 adjustment 参数：qfq/hfq/none（API: fqt=1/2/0） |
| | | • api.py params 直接透传到 Provider，支持 dc.get("600519", OHLCV, {"adjustment": "none"}) |
| | | • 新增 tests/test_adjustment_provider.py（20 个 adjustment 参数测试） |
| | | • 测试总数 1974 个（1964 + 10） |
| | | • ruff 代码审计零错误 |
| **v2.3.0** | **2026-07-20** | **FDT 集成修复版：SymbolRegistry A 股识别 + 东方财富期货 secid 修复** |
| | | • 修复 SymbolRegistry 不识别 A 股代码的 Bug（G32） |
| | | • 新增 _guess_equity_market() 规则识别：6 位数字→STOCK，510/511/512/513/515/588/159/516 前缀→ETF，110/113/118/127/128/132/133 前缀→CB |
| | | • 无需显式注册全部 A 股股票，SymbolRegistry 自动按规则识别 |
| | | • 修复 eastmoney.py 期货 secid 格式过时的 Bug（G33） |
| | | • eastmoney.py 期货 secid 从 "CF.RB" 改为带交易所前缀的主力合约探测 |
| | | • 遍历 [115.RB9999, 113.RB9999, 114.RB9999, 8.RB9999] 候选，第一个返回非空即采用 |
| | | • 修复后 FDT 可正常切换到 Data-Core 数据源 |
| | | • 新增 tests/test_registry_equity.py（10 个 A 股识别测试） |
| | | • 新增 tests/test_eastmoney_fix.py（5 个 secid 修复测试） |
| | | • 测试总数 1452 个（1437 + 15） |
| | | • ruff 代码审计零错误 |
| **v2.2.0** | **2026-07-20** | **Prometheus 可观测性集成版：observability.py + metrics_endpoint.py + 11 个标准指标 + 装饰器埋点** |
| | | • 新增 datacore/observability.py — Prometheus 可观测性核心模块 |
| | | • Counter/Gauge/Histogram 自定义实现（prometheus_client 可选依赖） |
| | | • 11 个标准指标：api_requests_total / api_request_duration_seconds / api_errors_total / source_degradations_total / source_availability / cache_hits_total / cache_misses_total / resampler_operations_total / issues_open / tool_invocations_total / tool_errors_total |
| | | • observe_api_call 装饰器：API 层埋点（UnifiedDataProvider.get()） |
| | | • observe_tool_call 装饰器：Tool 层埋点（DataCoreBaseTool.invoke()） |
| | | • 线程安全实现（threading.Lock 保护所有指标更新） |
| | | • 新增 datacore/metrics_endpoint.py — Prometheus HTTP 端点模块 |
| | | • generate_metrics() 生成 Prometheus exposition format 文本 |
| | | • start_metrics_server(port=9090) 启动 HTTP 服务器（daemon 线程） |
| | | • 支持 /metrics、/healthz、/ 三个端点 |
| | | • stop_metrics_server() 优雅关闭 |
| | | • API 层埋点：api.py UnifiedDataProvider.get() 添加 observe_api_call 装饰器 |
| | | • Tool 层埋点：tools/base.py DataCoreBaseTool.invoke() 添加 observe_tool_call 装饰器 |
| | | • Issue 埋点：issue.py report() 完成后更新 issues_open gauge |
| | | • Resampler 埋点：resampler/ohlcv.py resample_ohlcv() 完成后递增 resampler_operations counter |
| | | • metrics.py 增强：新增 _format_prometheus() 方法，保留 MetricsCollector 向后兼容 |
| | | • prometheus_client 为可选依赖，未安装时自动降级到自定义 Counter/Gauge/Histogram 实现 |
| | | • 新增 tests/test_observability.py（19 个测试用例） |
| | | • 测试总数 1437 个（1418 + 19） |
| | | • ruff 代码审计零错误 |
| **v2.1.0** | **2026-07-20** | **缺口补全版：API 层周期自动转换 + BaseTool args_schema 补全** |
| | | • UnifiedDataProvider.get() 对 OHLCV 类型数据自动重采样（API 层周期自动转换） |
| | | • 支持周期：1m, 5m, 15m, 30m, 60m, daily, weekly, monthly |
| | | • 自动推断源周期，出错时降级返回原始数据 |
| | | • 在 payload.meta 中记录 resampled_from 源周期 |
| | | • 异步接口（AsyncDataProvider）自动继承周期转换能力 |
| | | • 新增 datacore/tools/schemas.py，包含 23 个 Pydantic Schema 类 |
| | | • 23 个 Tool 全部配备 args_schema（Pydantic BaseModel） |
| | | • pydantic 为可选依赖，未安装时 args_schema = None，不影响使用 |
| | | • 完全兼容 LangChain StructuredTool |
| | | • 测试总数仍为 1418 个（新增功能通过既有测试覆盖） |
| | | • ruff 代码审计零错误 |
| **v2.0.0** | **2026-07-20** | **统一数据枢纽完整版：FDT 兼容层 + Qlib/RD-Agent 适配器 + 终验通过** |
| | | • 新增 FDT 兼容层（datacore/fdc_compat.py），提供 FDC 兼容的函数签名 |
| | | • FDC 兼容函数签名映射：get_kline/get_quote/get_fundamental/get_indicators 等 |
| | | • 数据格式适配：DataFrame/Series 输出格式 + 字段名映射 + 错误码兼容 |
| | | • 渐进式迁移路径 + 双轨运行支持 |
| | | • 新增 Qlib/RD-Agent 适配器（datacore/qlib_adapter/，3 个文件） |
| | | • Qlib DataProvider 完整接口：calendars/instruments/features/fundamentals |
| | | • 表达式引擎支持（Alpha158 等经典因子表达式） |
| | | • 数据格式双向转换器（Data-Core ↔ Qlib） |
| | | • 测试总数 1418 个（新增 197 个） |
| | | • 代码覆盖率 88%（核心模块接近 100%） |
| | | • ruff 代码审计零错误 |
| | | • 统一数据枢纽完整交付 |
| **v1.3.0** | **2026-07-19** | **BaseTool & 数据工具链版：23个Tool + 复权换月 + 周期转换 + 消费者反馈 + 数据清洗 + 数据校验 + 采集骨架 + 运维工具** |
| | | • 新增 BaseTool 接口层（datacore/tools/，24 个文件，兼容 LangChain 协议） |
| | | • 23 个 Tool：OHLCV/Quote/Sentiment/Health/ListSymbols/Macro/Fundamental/F10/Indicators/TermStructure/Basis/MarketRegime/News/Adjustment/Period/UnitUnify/DateAlign/DuplicateMerge/OutlierFilter/CrossSourceVerify/MissingDetect/CalMathCompute/ConfigRead |
| | | • 新增 all_tools 自动发现机制 |
| | | • 新增复权/换月引擎（datacore/adjustment/）：股票复权 + 期货主力连续合约 + 换月价差调整 |
| | | • 新增周期转换引擎（datacore/resampler/）：1m→5m→15m→30m→60m→daily→weekly→monthly |
| | | • 新增消费者反馈通道（datacore/issue.py）：IssueRegistry + report_issue() + 自动降级 |
| | | • 新增数据清洗模块（datacore/cleaning/）：unit_unify / date_align / duplicate_merge / outlier_filter |
| | | • 新增数据校验模块（datacore/validation/）：weight_score / cross_source / missing_detect / cal_math |
| | | • 新增采集模块骨架（datacore/collectors/）：web_crawl / open_source / local_doc / search |
| | | • 新增运维工具模块（datacore/operations/）：crawl_retry / error_log / config_tools |
| | | • get_health() 新增 consumer_issues 字段 |
| | | • 测试总数 1221 个（新增 365 个） |
| | | • v2.0 之前最大版本 |
| **v1.2.0** | **2026-07-19** | **FDC 模块吸收版：indicators 技术指标 + 3 个期货新数据源 + 7 源降级链** |
| | | • 新增 indicators/ 技术指标模块（从 FDC 吸收，5 个文件） |
| | | • 37+ 基础指标纯 numpy 实现，三层路由体系（TDX → numpy → TA-Lib） |
| | | • 新增趋势成熟度评估（assess_trend_maturity） |
| | | • 新增 QMTProvider 迅投资讯源（P2，依赖 xtquant） |
| | | • 新增 WebFallbackProvider 网页备用源（P5，零依赖） |
| | | • 新增 TqSdkProvider 兜底源（P6，依赖 tqsdk） |
| | | • 期货降级链从 4 源扩展为 7 源（TdxLc→EastMoney→QMT→ExchangeApi→ShengYiShe→WebFallback→TqSdk） |
| | | • 公开 API：compute_indicators, INDICATOR_NAMES, assess_trend_maturity |
| | | • 代码覆盖率保持 96% |
| | | • 新增 2 个测试文件，110 个测试用例 |
| **v1.1.0** | **2026-07-19** | **统一数据枢纽 Phase 1：异步双接口 + F10 综合报告 + core 共享基础设施** |
| | | • 新增 AsyncDataProvider 异步双接口（api_async.py，基于 run_in_executor 线程池桥接） |
| | | • 新增 F10 综合报告（api_f10.py + UnifiedDataProvider.get_f10） |
| | | • 新增 core/ 共享基础设施模块（types.py + data_freshness.py + __init__.py） |
| | | • 新增 DataType.F10_REPORT 枚举值 |
| | | • 数据新鲜度评估（DataFreshnessAssessor + FreshnessStatus 三级状态） |
| | | • 代码覆盖率从 95% 提升到 96% |
| | | • 新增 1 个测试文件，28 个测试用例 |
| **v1.0.0** | **2026-07-19** | **生产就绪版：WebSocket + 告警 + 性能基准 + 安全审计** |
| | | • 新增 WebSocket 实时行情支持（stream.py: StreamQuote + WebSocketManager） |
| | | • 新增告警引擎（alert.py: AlertEngine + 预置规则 + 3 通知渠道） |
| | | • 新增性能基准测试（benchmark_test.py: 8 个基准测试） |
| | | • 新增安全审计清单（docs/SECURITY_CHECKLIST.md: 7 项检查全部通过） |
| | | • WebSocket 自动重连（指数退避）+ 心跳保活 |
| | | • 告警预置规则：价格突破/波动率异常/数据延迟/熔断触发 |
| | | • 告警通知渠道：日志/文件/Webhook 三级降级 |
| | | • 代码覆盖率 ≥ 95%，pylint ≥ 9.50/10, mypy/ruff 0 错误 |
| | | • 新增 3 个测试文件，41 个测试用例 |
| **v0.6.0** | **2026-07-19** | **LLM 与智能加工版：情绪端到端 + 基本面 LLM + Docker 部署** |
| | | • LLM 情绪打分端到端验证（15 个测试） |
| | | • 新增基本面 LLM 加工模块（fundamental_llm: 研报摘要 + 财报提取） |
| | | • 新增 Docker 部署文件（Dockerfile, docker-compose.yml, docker-compose.prod.yml） |
| | | • 新增部署文档（docs/DEPLOYMENT.md） |
| | | • 新增 2 个测试文件，27 个测试用例 |
| **v0.5.0** | **2026-07-19** | **数据源完善版：宏观/期货/A股扩展 + DuckDB 缓存 + 多源降级链** |
| | | • 新增国家统计局宏观数据源（GDP/CPI/PPI/PMI） |
| | | • 新增央行宏观数据源（LPR/M2） |
| | | • 新增交易所官方数据源（上期所/郑商所/大商所） |
| | | • 新增生意社现货/基差数据源 |
| | | • 新增国信证券数据源（正式接入） |
| | | • DuckDB 接入 api.py 作为 L2 缓存层（MemoryCache → DuckDB → HTTP） |
| | | • 宏观 3 源降级链: 统计局→央行→东方财富 |
| | | • 期货 4 源降级链: TQ-Local→东方财富→交易所→生意社 |
| | | • A 股 3 源降级链: 腾讯→东方财富→国信 |
| | | • 国信 base 近似算法修复（D01） |
| | | • 新增 5 个测试文件，72 个测试用例 |
| **v0.4.0** | **2026-07-18** | **工程完善版：熔断器 + 健康检查 + 指标收集 + DuckDB 持久化 + CLI 增强** |
| | | • 新增 Breaker 熔断器（CLOSED/OPEN/HALF_OPEN） |
| | | • 新增 get_health() 健康检查接口（返回各数据源实时状态） |
| | | • 新增 MetricsCollector 指标收集框架 |
| | | • 新增 store/duckdb.py DuckDB 加密持久化 |
| | | • CLI status 命令显示真实数据源状态 |
| | | • ETF/CB/REIT 基础数据获取支持 |
| | | • 新增 3 个测试文件，80 个测试用例 |
| **v0.3.0** | **2026-07-18** | **数据加工层：情绪管线 + 市场制度检测** |
| | | • 新增 `processing/` 模块（7个文件） |
| | | • 新增 SENTIMENT/MARKET_STATE DataType |
| | | • 规则情绪基线（词典法，零成本，含否定词/程度副词） |
| | | • LLM 情绪打分骨架（含降级到规则基线） |
| | | • 情绪聚合器（时间衰减+置信度加权+按日聚合） |
| | | • 市场制度检测（趋势/波动率/成交量综合判断） |
| | | • SENTIMENT/MARKET_STATE/NEWS/MACRO 接入 UnifiedDataProvider |
| | | • 新增 36 个测试用例（总计 104 个） |
| v0.2.0 | 2026-07-18 | 期货能力增强 + 新闻资讯模块 + 宏观数据模块 |
| v0.1.0 | 2026-07-18 | Initial version, 27 source files, 28 test cases |

## Dependencies

### 必需依赖
- `numpy>=1.24`, `pandas>=2.0`, `httpx>=0.25`, `pyyaml>=6.0`

### 可选依赖
| 分组 | 依赖 | 说明 |
|:-----|:-----|:-----|
| `store` | `duckdb>=0.9` | DuckDB 持久化 |
| `postgres` | `psycopg2-binary>=2.9` | PostgreSQL |
| `redis` | `redis>=5.0` | Redis 缓存 |
| `full` | 以上全部 | 完整功能 |
| - | `openai>=1.0` | LLM 情绪打分（v0.3.0，可选） |
| - | `beautifulsoup4>=4.12` | HTML 解析 |
| - | `websockets>=12.0` | WebSocket 客户端（v1.0.0 新增，可选） |
| - | `TA-Lib>=0.4` | TA-Lib 技术指标库（v1.2.0 新增，可选，indicators 兜底层） |
| - | `xtquant>=1.0` | 迅投 QMT 行情接口（v1.2.0 新增，可选，QMTProvider） |
| - | `tqsdk>=3.0` | 天勤 TqSdk（v1.2.0 新增，可选，TqSdkProvider 兜底） |
| - | `beautifulsoup4>=4.12` | HTML 解析（v1.3.0，采集模块增强） |
| - | `langchain-core>=0.1` | LangChain Core（v1.3.0 新增，可选，BaseTool 协议兼容） |
| - | `pydantic>=2.0` | Pydantic（v2.1.0 新增，可选，BaseTool args_schema） |
| - | `pyqlib>=0.9` | Qlib 量化投资框架（v2.0.0 新增，可选，Qlib 适配器） |
| - | `prometheus_client>=0.16` | Prometheus Client（v2.2.0 新增，可选，原生 Prometheus 指标集成；未安装时降级到自定义实现） |

## File Structure

```
datacore/                    84 个 Python 源文件
├── __init__.py              模块初始化
├── api.py                   统一入口 API（含 get_health() + 缓存层）
├── api_async.py             AsyncDataProvider 异步双接口（v1.1.0 新增）
├── api_f10.py               F10 综合报告（v1.1.0 新增）
├── fdc_compat.py            FDT 兼容层（v2.0.0 新增）
├── config.py                统一配置
├── cli.py                   命令行工具（status 显示真实状态）
├── breaker.py               熔断器（v0.4.0 新增）
├── metrics.py               指标收集（v0.4.0 新增）
├── stream.py                WebSocket 实时行情（v1.0.0 新增）
├── alert.py                 告警引擎（v1.0.0 新增）
├── observability.py         Prometheus 可观测性模块（v2.2.0 新增）
├── metrics_endpoint.py      Prometheus HTTP 端点（v2.2.0 新增）
├── core/                    共享基础设施（v1.1.0 新增）
│   ├── types.py             KlineBar / QuoteData / FreshnessStatus
│   ├── data_freshness.py    DataFreshnessAssessor 数据新鲜度评估
│   └── __init__.py
├── indicators/              技术指标模块（v1.2.0 新增，FDC 吸收）
│   ├── core.py              37+ 基础指标纯 numpy 实现
│   ├── tdx_compat.py        TDX 通达信对齐指标
│   ├── legacy_numpy.py      旧版兼容实现
│   ├── trend_maturity.py    趋势成熟度评估
│   ├── talib_wrapper.py     TA-Lib 封装兜底
│   └── __init__.py          导出 compute_indicators / INDICATOR_NAMES / assess_trend_maturity
├── tools/                   BaseTool 接口层（v1.3.0 新增，v2.1.0 增强，核心交付）
│   ├── base.py              DataCoreBaseTool 基类（兼容 LangChain 协议）
│   ├── schemas.py           23 个 Pydantic Schema 类（v2.1.0 新增，args_schema）
│   ├── ohlcv.py / quote.py / sentiment.py / health.py
│   ├── list_symbols.py / macro.py / fundamental.py / f10.py
│   ├── indicators.py / term_structure.py / basis.py / market_regime.py / news.py
│   ├── adjustment.py / period.py
│   ├── unit_unify.py / date_align.py / duplicate_merge.py / outlier_filter.py
│   ├── cross_source_verify.py / missing_detect.py / cal_math_compute.py
│   ├── config_read.py
│   └── __init__.py          all_tools 自动发现机制
├── adjustment/              复权/换月引擎（v1.3.0 新增）
│   ├── stock_adjustment.py  股票前复权/后复权/不复权
│   ├── futures_rollover.py  期货主力连续合约
│   ├── spread_adjustment.py 期货换月价差调整
│   └── __init__.py
├── resampler/               周期转换引擎（v1.3.0 新增）
│   ├── resampler.py         周期转换主入口
│   ├── ohlcv_aggregator.py  OHLCV 正确聚合
│   ├── auto_detector.py     auto 模式自动检测
│   └── __init__.py
├── issue.py                 消费者反馈通道（v1.3.0 新增）
├── cleaning/                数据清洗模块（v1.3.0 新增）
│   ├── unit_unify.py / date_align.py
│   ├── duplicate_merge.py / outlier_filter.py
│   └── __init__.py
├── validation/              数据校验模块（v1.3.0 新增）
│   ├── weight_score.py / cross_source.py
│   ├── missing_detect.py / cal_math.py
│   └── __init__.py
├── collectors/              采集模块骨架（v1.3.0 新增）
│   ├── web_crawl.py / open_source.py
│   ├── local_doc.py / search.py
│   └── __init__.py
├── operations/              运维工具模块（v1.3.0 新增）
│   ├── crawl_retry.py / error_log.py / config_tools.py
│   └── __init__.py
├── qlib_adapter/            Qlib/RD-Agent 适配器（v2.0.0 新增）
│   ├── provider.py          Qlib DataProvider 接口实现
│   ├── converter.py         数据格式转换器
│   └── __init__.py
├── models/                  数据模型与枚举
│   ├── enums.py             DataType/MarketType/SourceGrade
│   ├── payload.py           数据载荷
│   ├── ohlcv.py             K 线模型
│   ├── futures.py           期货模型
│   └── __init__.py
├── registry/                品种注册表
│   ├── symbol_registry.py
│   └── __init__.py
├── store/                   存储层（含 duckdb.py 持久化）
│   ├── cache.py             MemoryCache
│   ├── duckdb.py            DuckDB 持久化（v0.4.0 新增）
│   ├── redis.py             Redis 缓存
│   ├── postgres.py          PostgreSQL 存储
│   └── __init__.py
├── futures/                 期货数据模块
│   ├── futures_provider.py  期货统一入口
│   ├── providers/           多源降级链（7 源，v1.2.0 扩展）
│   │   ├── base.py / tdx_lc.py / eastmoney.py
│   │   ├── exchange_api.py  （v0.5.0 新增）
│   │   ├── shengyishe.py    （v0.5.0 新增）
│   │   ├── qmt.py           （v1.2.0 新增，P2）
│   │   ├── web_fallback.py  （v1.2.0 新增，P5）
│   │   ├── tqsdk.py         （v1.2.0 新增，P6）
│   │   └── __init__.py
│   └── __init__.py
├── equity/                  股票数据模块
│   ├── equity_provider.py   股票统一入口
│   ├── financial.py         财务数据
│   ├── providers/           多源降级链
│   │   ├── base.py / tencent.py / eastmoney.py
│   │   ├── guosen.py        （v0.5.0 正式接入）
│   │   └── __init__.py
│   └── __init__.py
├── news/                    新闻资讯模块
│   ├── news_provider.py / classifier.py / models.py
│   ├── providers/           cls / wallstreet_cn / eastmoney_research
│   └── __init__.py
├── macro/                   宏观数据模块
│   ├── macro_provider.py / models.py
│   ├── providers/           eastmoney_macro / national_bureau / pboc
│   └── __init__.py
├── processing/              数据加工层（v0.3.0 新增，v0.6.0 扩展）
│   ├── base.py / models.py
│   ├── sentiment/           情绪加工管线
│   │   ├── sentiment_rule.py / sentiment_llm.py / sentiment_aggregator.py
│   │   └── __init__.py
│   ├── market_regime.py     市场制度检测
│   ├── fundamental/         基本面 LLM 加工（v0.6.0 新增）
│   │   ├── fundamental_llm.py / models.py
│   │   └── __init__.py
│   └── __init__.py

tests/                       40 个测试文件，1437 个测试用例
├── test_observability.py    Prometheus 可观测性测试（v2.2.0 新增，19 个用例）
├── test_fdc_compat.py       FDT 兼容层测试（v2.0.0 新增，98 个用例）
├── test_qlib_adapter.py     Qlib/RD-Agent 适配器测试（v2.0.0 新增，99 个用例）
├── test_tools.py            BaseTool 接口层测试（v1.3.0 新增，89 个用例）
├── test_adjustment.py       复权/换月引擎测试（v1.3.0 新增，80 个用例）
├── test_resampler.py        周期转换引擎测试（v1.3.0 新增，69 个用例）
├── test_issue.py            消费者反馈通道测试（v1.3.0 新增，34 个用例）
├── test_cleaning.py         数据清洗模块测试（v1.3.0 新增，31 个用例）
├── test_validation.py       数据校验模块测试（v1.3.0 新增，27 个用例）
├── test_collectors.py       采集模块骨架测试（v1.3.0 新增，18 个用例）
├── test_operations.py       运维工具模块测试（v1.3.0 新增，19 个用例）
├── test_indicators.py       技术指标模块测试（v1.2.0 新增，90 个用例）
├── test_futures_new_providers.py  新期货数据源测试（v1.2.0 新增，20 个用例）
├── test_phase1.py           Phase 1 综合测试（v1.1.0 新增）
├── test_alert.py            告警引擎测试（v1.0.0 新增）
├── test_stream.py           WebSocket 测试（v1.0.0 新增）
├── benchmark_test.py        性能基准测试（v1.0.0 新增）
├── test_sentiment_llm.py    LLM 情绪打分端到端测试（v0.6.0 新增）
├── test_fundamental_llm.py  基本面 LLM 加工测试（v0.6.0 新增）
├── test_macro_providers.py  宏观数据源 mock 测试（v0.5.0 新增）
├── test_futures_providers.py 期货基本面 mock 测试（v0.5.0 新增）
├── test_guosen.py           国信证券 mock 测试（v0.5.0 新增）
├── test_news_providers.py   新闻数据源 mock 测试（v0.5.0 新增）
├── test_api_cache.py        缓存层测试（v0.5.0 新增）
├── test_breaker.py          熔断器测试（v0.4.0 新增）
├── test_health.py           健康检查测试（v0.4.0 新增）
├── test_metrics.py          指标收集测试（v0.4.0 新增）
├── test_processing.py       数据加工层测试
├── test_equity.py           股票数据模块测试
├── test_futures.py          期货数据模块测试
├── test_cli.py              CLI 命令行测试
├── test_api.py / test_news.py / test_macro.py
├── test_futures_mock.py / test_futures_models.py
├── test_equity_mock.py / test_store.py
├── test_registry.py / test_models.py
└── conftest.py / __init__.py

docs/                        部署 + 安全 + 工程规范文档
├── DEPLOYMENT.md            部署文档（v0.6.0 新增）
├── SECURITY_CHECKLIST.md    安全审计清单（v1.0.0 新增）
├── PRODUCTION_PLAN.md       生产计划
└── harness/                 9 个工程规范文档

**总计: 100+ 个源文件 + 40 个测试文件 + 10 个工程/部署/安全文档**
