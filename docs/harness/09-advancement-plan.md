# Data-Core Advancement Plan

Version: v1.0.0 | Updated: 2026-07-19

## Milestones

| 里程碑 | 版本 | 日期 | 状态 | 说明 |
|:-------|:-----|:-----|:-----|:-----|
| **M1** | **v0.1.0** | **2026-07-18** | ✅ **COMPLETED** | 基础可用版 |
| **M2** | **v0.2.0** | **2026-07-18** | ✅ **COMPLETED** | 能力增强版（期货深度+新闻+宏观） |
| **M3** | **v0.3.0** | **2026-07-18** | ✅ **COMPLETED** | 数据加工层（情绪管线+市场制度） |
| **M4** | **v0.4.0** | **2026-07-18** | ✅ **COMPLETED** | 工程完善版（健康检查+熔断+指标+ETF/CB） |
| **M5** | **v0.5.0** | **2026-07-19** | ✅ **COMPLETED** | 数据源完善版（宏观/期货/A股扩展 + DuckDB缓存） |
| **M6** | **v0.6.0** | **2026-07-19** | ✅ **COMPLETED** | LLM 与智能加工版（情绪端到端 + 基本面LLM + Docker） |
| **M7** | **v1.0.0** | **2026-07-19** | ✅ **COMPLETED** | 生产就绪版（WebSocket + 告警 + 基准 + 安全审计） |

## M7 (v1.0.0) 交付清单 ✅

### WebSocket 实时行情
- ✅ StreamQuote 数据模型（symbol/price/volume/timestamp/exchange）
- ✅ WebSocketManager 连接管理（connect/subscribe/on_quote）
- ✅ 自动重连策略（指数退避）
- ✅ 心跳保活机制

### 告警引擎
- ✅ AlertEngine 告警引擎
- ✅ 预置告警规则（price_breakout/volatility_anomaly/data_stale/breaker_trip）
- ✅ 3 个通知渠道（日志/文件/Webhook）
- ✅ 渠道降级策略（Webhook → 文件 → 日志）

### 性能基准
- ✅ 数据获取性能基准
- ✅ 缓存层性能基准
- ✅ 数据加工性能基准
- ✅ 并发处理性能基准
- ✅ 8 个基准测试

### 安全审计
- ✅ 认证安全（API Key 环境变量）
- ✅ 数据加密（DuckDB 加密存储）
- ✅ 注入防护（SQL 参数化）
- ✅ 配置安全（默认值安全）
- ✅ 依赖安全（版本锁定）
- ✅ 日志安全（无敏感信息）
- ✅ 通信安全（HTTPS/WS 加密）
- ✅ docs/SECURITY_CHECKLIST.md

### 测试与质量
- ✅ 3 个新测试文件，41 个新测试用例
- ✅ 总计 26 个测试文件，724+ 个测试用例
- ✅ 代码覆盖率 ≥ 95%
- ✅ pylint ≥ 9.50/10, mypy: 0 错误, ruff: 0 错误

## M6 (v0.6.0) 交付清单 ✅

### LLM 情绪打分
- ✅ LLM 情绪打分端到端验证（15 个测试）
- ✅ 真实 API 调用路径验证

### 基本面 LLM 加工
- ✅ fundamental_llm.py 研报摘要提取
- ✅ fundamental_llm.py 财报提取
- ✅ 基本面加工数据模型

### Docker 部署
- ✅ Dockerfile（应用容器化）
- ✅ docker-compose.yml（开发环境）
- ✅ docker-compose.prod.yml（生产环境）
- ✅ docs/DEPLOYMENT.md（部署文档）

### 测试
- ✅ 2 个新测试文件，27 个新测试用例

## M5 (v0.5.0) 交付清单 ✅

### 数据源完善（P1→P2）
- ✅ 国信 HTTP 数据源正式接入（GuosenProvider，7 个 mock 测试）
- ✅ 新闻数据源实际 HTTP 抓取（财联社/华尔街见闻/东方财富研报，19 个 mock 测试）
- ✅ 国家统计局/央行宏观源接入（3 源降级链，28 个 mock 测试）
- ✅ 期货基本面数据实际抓取（交易所官方/生意社，6 个 mock 测试）

### 缓存层
- ✅ DuckDB 接入 api.py 作为 L2 缓存（MemoryCache → DuckDB → HTTP）
- ✅ 12 个缓存层测试用例

### 降级链
- ✅ 宏观 3 源降级链: 统计局→央行→东方财富
- ✅ 期货 4 源降级链: TQ-Local→东方财富→交易所→生意社
- ✅ A 股 3 源降级链: 腾讯→东方财富→国信

### 技术债修复
- ✅ D01: 基差近似算法通过生意社真实数据源修复
- ✅ D03: news provider 异常处理通过 mock 覆盖
- ✅ D05: DuckDB 接入 api.py 缓存层

### 测试
- ✅ 新增 5 个测试文件，72 个测试用例
- ✅ 总计 20 个测试文件，656 个测试用例

## M4 (v0.4.0) 交付清单 ✅

### 熔断器
- ✅ Breaker 类（CLOSED/OPEN/HALF_OPEN 三种状态）
- ✅ 超时触发熔断
- ✅ 半开探测恢复
- ✅ 可配置 max_failures / recovery_timeout
- ✅ 30 个测试用例

### 健康检查
- ✅ UnifiedDataProvider.get_health() 方法
- ✅ 各数据源实时可用状态探测
- ✅ 整体 healthy/degraded/unavailable 状态汇总
- ✅ 20 个测试用例

### 指标收集
- ✅ MetricsCollector 框架
- ✅ 调用次数/成功率/延迟（P50/P95/P99）/缓存命中率
- ✅ MetricsCollector.report() 快照
- ✅ 30 个测试用例

### DuckDB 持久化
- ✅ store/duckdb.py 加密持久化
- ✅ store(key, value) / load(key)
- ✅ 按类型（kline/quote/macro 等）具体存读方法

### CLI 增强
- ✅ status 命令显示真实数据源状态

### ETF/CB/REIT
- ✅ DataType 已定义
- ✅ 基础数据获取

### 测试
- ✅ 80 个新增测试用例（总计 184 个）
- ✅ test_breaker.py / test_health.py / test_metrics.py

## 晋级标准

### M2 → M3 晋级标准 ✅
- [x] SENTIMENT/MARKET_STATE DataType 定义
- [x] 情绪加工管线可用（规则基线+LLM骨架）
- [x] 市场制度检测可用
- [x] 接入 UnifiedDataProvider
- [x] 测试用例覆盖新增功能

### M3 → M4 晋级标准 ✅
- [x] 健康检查接口可用
- [x] 熔断器实现并测试
- [x] 指标收集框架就绪
- [x] ETF/CB 基础功能可用
- [x] 所有 P1 差距关闭
- [x] 80 个新增测试用例

### M4 → M5 晋级标准 ✅
- [x] 国信 HTTP 数据源正式接入
- [x] 新闻数据源实际 HTTP 抓取
- [x] 国家统计局/央行宏观源接入
- [x] 期货基本面数据实际抓取
- [x] DuckDB 集成到 api.py 缓存层
- [x] 72 个新增测试用例

### M5 → M6 晋级标准 ✅
- [x] LLM 情绪打分端到端验证（15 个测试）
- [x] 基本面 LLM 加工模块（研报摘要 + 财报提取）
- [x] 部署文档
- [x] 27 个新增测试用例

### M6 → M7 晋级标准 ✅
- [x] WebSocket 实时行情支持
- [x] 告警系统（预置规则 + 3 通知渠道）
- [x] 性能基准测试（8 个基准测试）
- [x] 安全审计（7 项检查全部通过）
- [x] 全链路 trace_id 贯穿
- [x] P0/P1 级差距全部关闭
- [x] 整体测试覆盖率 ≥ 95%
- [x] pylint ≥ 9.50/10, mypy: 0 错误, ruff: 0 错误
- [x] 41 个新增测试用例

## 项目最终状态

| 维度 | v1.0.0 |
|:-----|:-------|
| 版本 | v1.0.0 生产就绪 |
| 源文件 | 64 个 .py |
| 测试文件 | 26 个 |
| 测试用例 | 724+ |
| 代码覆盖率 | ≥ 95% |
| pylint | ≥ 9.50/10 |
| mypy | 0 错误 |
| ruff | 0 错误 |
| 差距关闭 | 25 个全部关闭 |
| 安全审计 | 7 项全部通过 |
| 部署 | 裸机部署（推荐），可选容器化 |
