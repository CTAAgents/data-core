# Data-Core Lifecycle

Version: v1.0.0 | Updated: 2026-07-19

## Module Phases

| Phase | Version | Module | Status | Description |
|:------|:--------|:-------|:-------|:------------|
| Phase 1 | v0.1.0 | models/registry/store | COMPLETED | 数据模型、品种注册、存储层基础 |
| Phase 2 | v0.2.0 | futures providers | COMPLETED | 期货多源数据源 |
| Phase 3 | v0.2.0 | equity providers | COMPLETED | 股票多源数据源 |
| Phase 4 | v0.3.0 | processing layer | COMPLETED | 数据加工层：情绪管线 + 市场制度 |
| Phase 5 | v0.5.0 | data source expansion | COMPLETED | 数据源完善版（宏观/期货/A股扩展 + DuckDB缓存） |
| Phase 6 | v0.6.0 | LLM & intelligent processing | COMPLETED | LLM 情绪打分端到端验证 + 基本面LLM加工 |
| Phase 7 | v1.0.0 | production readiness | COMPLETED | WebSocket 实时行情 + 告警系统 + 性能基准 + 安全审计 |

## v0.5.0 数据源完善版

v0.5.0 聚焦数据源扩展：新增 5 个数据源提供者，DuckDB 接入 api.py 作为 L2 缓存层，多源降级链全面升级。

### v0.5.0 新增模块
- `datacore/macro/providers/national_bureau.py` — 国家统计局宏观数据源 (P0)
- `datacore/macro/providers/pboc.py` — 央行宏观数据源 (P1)
- `datacore/futures/providers/exchange_api.py` — 交易所官方数据源（上期所/郑商所/大商所）
- `datacore/futures/providers/shengyishe.py` — 生意社现货/基差数据源
- `datacore/equity/providers/guosen.py` — 国信证券数据源 (P2)

### v0.5.0 增强模块
- `datacore/api.py` — DuckDB L2 缓存集成（MemoryCache → DuckDB），版本号 v0.5.0
- `datacore/macro/macro_provider.py` — 3 源降级链: 统计局→央行→东方财富
- `datacore/macro/providers/__init__.py` — 新增 national_bureau/pboc 导出
- `datacore/futures/futures_provider.py` — 4 源降级链（新增 exchange_api/shengyishe）
- `datacore/futures/providers/__init__.py` — 新增 exchange_api/shengyishe 导出
- `datacore/equity/providers/__init__.py` — 新增 GuosenProvider 导出
- `datacore/equity/equity_provider.py` — 3 源降级链: 腾讯→东方财富→国信

### v0.5.0 新增测试
| 测试文件 | 用例数 | 说明 |
|:---------|:-------|:-----|
| `tests/test_macro_providers.py` | 28 | 宏观数据源 mock 测试 |
| `tests/test_futures_providers.py` | 6 | 期货基本面数据源 mock 测试 |
| `tests/test_guosen.py` | 7 | 国信证券 mock 测试 |
| `tests/test_news_providers.py` | 19 | 新闻数据源 mock 测试 |
| `tests/test_api_cache.py` | 12 | 缓存层测试 |

**新增 72 个测试用例，总计 656 个测试用例**

### v0.5.0 产出物清单

- ✅ 国家统计局宏观数据源（GDP/CPI/PPI/PMI）
- ✅ 央行宏观数据源（LPR/M2）
- ✅ 交易所官方数据源（上期所/郑商所/大商所）
- ✅ 生意社现货/基差数据源
- ✅ 国信证券数据源正式接入
- ✅ DuckDB L2 缓存集成（MemoryCache → DuckDB → HTTP）
- ✅ 宏观 3 源降级链
- ✅ 期货 4 源降级链
- ✅ A 股 3 源降级链
- ✅ 5 个新测试文件，72 个新测试用例
- ✅ D01 修复：shengyishe 提供真实基差，替换 eastmoney 近似算法
- ✅ D05 关闭：DuckDB 接入 api.py 缓存层

## v0.6.0 LLM 与智能加工版

v0.6.0 聚焦 LLM 能力完善：情绪打分端到端验证，基本面 LLM 加工模块，Docker 部署。

### v0.6.0 新增模块
- `datacore/processing/fundamental/fundamental_llm.py` — 基本面 LLM 加工（研报摘要 + 财报提取）
- `datacore/processing/fundamental/models.py` — 基本面加工数据模型
- `Dockerfile` — 应用 Dockerfile
- `docker-compose.yml` — 开发环境 Docker Compose
- `docker-compose.prod.yml` — 生产环境 Docker Compose
- `docs/DEPLOYMENT.md` — 部署文档

### v0.6.0 增强模块
- `datacore/processing/sentiment/sentiment_llm.py` — LLM 情绪打分端到端验证（15 个测试）

### v0.6.0 新增测试
| 测试文件 | 用例数 | 说明 |
|:---------|:-------|:-----|
| `tests/test_sentiment_llm.py` | 15 | LLM 情绪打分端到端测试 |
| `tests/test_fundamental_llm.py` | 12 | 基本面 LLM 加工测试 |

**新增 27 个测试用例，总计 683 个测试用例**

### v0.6.0 产出物清单

- ✅ LLM 情绪打分端到端验证（15 个测试）
- ✅ 基本面 LLM 加工模块（研报摘要 + 财报提取）
- ✅ 部署文档（docs/DEPLOYMENT.md）
- ✅ 2 个新测试文件，27 个新测试用例

## v1.0.0 生产就绪版

v1.0.0 聚焦生产就绪：WebSocket 实时行情、告警系统、性能基准测试、安全审计。

### v1.0.0 新增模块
- `datacore/stream.py` — WebSocket 实时行情（StreamQuote + WebSocketManager）
- `datacore/alert.py` — 告警引擎（AlertEngine + 预置规则 + 3 个通知渠道）
- `tests/benchmark_test.py` — 性能基准测试（8 个基准测试）
- `docs/SECURITY_CHECKLIST.md` — 安全审计清单（7 项检查）

### v1.0.0 新增测试
| 测试文件 | 用例数 | 说明 |
|:---------|:-------|:-----|
| `tests/test_stream.py` | 15 | WebSocket 连接/重连/订阅测试 |
| `tests/test_alert.py` | 18 | 告警引擎规则/渠道测试 |
| `tests/benchmark_test.py` | 8 | 性能基准测试（数据获取/缓存/加工/并发） |

**新增 41 个测试用例，总计 724 个测试用例**

### v1.0.0 产出物清单

- ✅ WebSocket 实时行情支持（StreamQuote + WebSocketManager）
- ✅ 告警系统（AlertEngine、预置规则、3 个通知渠道）
- ✅ 性能基准测试（8 个基准测试）
- ✅ 安全审计（docs/SECURITY_CHECKLIST.md，7 项检查全部通过）
- ✅ 3 个新测试文件，41 个新测试用例
- ✅ 代码覆盖率 ≥ 95%
- ✅ pylint ≥ 9.50/10, mypy: 0 错误, ruff: 0 错误

## v0.4.0 工程完善版

v0.4.0 聚焦工程化完善：熔断器、健康检查、指标收集、DuckDB 持久化、CLI 增强、ETF/CB 基础支持。

### v0.4.0 新增模块
- `datacore/breaker.py` — 带状态熔断器（CLOSED/OPEN/HALF_OPEN）
- `datacore/metrics.py` — 指标收集框架（调用次数/成功率/延迟/缓存命中率）
- `datacore/store/duckdb.py` — DuckDB 加密持久化（store/load 方法，按类型存取）

### v0.4.0 增强模块
- `datacore/api.py` — 新增 get_health() 健康检查接口
- `datacore/cli.py` — status 命令显示真实数据源状态（替代"待探测"占位符）
- `datacore/models/enums.py` — ETF/CB/REIT 基础数据获取支持

### v0.4.0 新增测试
| 测试文件 | 用例数 | 说明 |
|:---------|:-------|:-----|
| `tests/test_breaker.py` | 30 | 熔断器状态转换/超时/半开探测 |
| `tests/test_health.py` | 20 | 健康检查接口及各数据源状态 |
| `tests/test_metrics.py` | 30 | 指标收集/成功率/延迟/缓存命中率 |

**新增 80 个测试用例，总计 184 个测试用例**

### v0.4.0 产出物清单

- ✅ Breaker 熔断器（CLOSED/OPEN/HALF_OPEN 三种状态）
- ✅ MetricsCollector 指标收集框架
- ✅ DuckDB 加密持久化（store/load + 按类型存取）
- ✅ get_health() 健康检查接口
- ✅ CLI status 命令真实数据源状态
- ✅ ETF/CB/REIT 基础数据获取
- ✅ 80 个新增测试用例

## v0.3.0 产出物清单

### 新增模块
- `datacore/processing/` — 数据加工层（7个文件）
  - `base.py` — ProcessingStage 抽象基类
  - `models.py` — SentimentItem/SentimentData/MarketStateData/MarketRegime
  - `sentiment/sentiment_rule.py` — 规则情绪基线（词典法）
  - `sentiment/sentiment_llm.py` — LLM 情绪打分（含降级）
  - `sentiment/sentiment_aggregator.py` — 情绪聚合器（时间衰减+置信度加权）
  - `market_regime.py` — 市场制度检测（bull/bear/sideways）

### 增强模块
- `datacore/models/enums.py` — 新增 SENTIMENT/MARKET_STATE DataType
- `datacore/api.py` — 接入 SENTIMENT/MARKET_STATE/NEWS/MACRO 路由

### 新增测试
- `tests/test_processing.py` — 36 个用例

### 数据加工层能力
- ✅ 规则情绪基线（词典法，零成本，含否定词和程度副词处理）
- ✅ LLM 情绪打分骨架（含降级到规则基线）
- ✅ 情绪聚合器（时间衰减加权 + 置信度加权 + 按日聚合）
- ✅ 市场制度检测（趋势强度 + 波动率 + 成交量趋势综合判断）
- ✅ SENTIMENT/MARKET_STATE 接入 UnifiedDataProvider
