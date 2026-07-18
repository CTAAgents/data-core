# Data-Core Operations

Version: v1.0.0 | Updated: 2026-07-19

## Version History

| 版本 | 日期 | 变更说明 |
|:-----|:-----|:---------|
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

## File Structure

```
datacore/                    64 个 Python 源文件
├── __init__.py              模块初始化
├── api.py                   统一入口 API（含 get_health() + 缓存层）
├── config.py                统一配置
├── cli.py                   命令行工具（status 显示真实状态）
├── breaker.py               熔断器（v0.4.0 新增）
├── metrics.py               指标收集（v0.4.0 新增）
├── stream.py                WebSocket 实时行情（v1.0.0 新增）
├── alert.py                 告警引擎（v1.0.0 新增）
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
│   ├── providers/           多源降级链
│   │   ├── base.py / tdx_lc.py / eastmoney.py
│   │   ├── exchange_api.py  （v0.5.0 新增）
│   │   ├── shengyishe.py    （v0.5.0 新增）
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

tests/                       26 个测试文件，724+ 个测试用例
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

**总计: 64 个源文件 + 26 个测试文件 + 10 个工程/部署/安全文档**
