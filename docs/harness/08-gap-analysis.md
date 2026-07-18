# Data-Core Gap Analysis

Version: v0.4.0 | Updated: 2026-07-18

## Registered Gaps

| ID | 优先级 | 标题 | 状态 | 计划版本 | 说明 |
|:---|:-------|:-----|:-----|:---------|:-----|
| G03 | P2 | 国信 HTTP 数据源 | OPEN | v0.5.0 | 骨架存在，API 未集成 |
| G07 | P2 | 新闻数据源实际接入 | OPEN | v0.5.0 | provider 骨架已建，HTTP 抓取未实现 |
| G08 | P2 | 国家统计局/央行宏观源 | OPEN | v0.5.0 | 仅接入东方财富 |
| G09 | P2 | 期货基本面数据抓取 | OPEN | v0.5.0 | 模型已建，实际抓取未实现 |
| G11 | P2 | LLM 情绪打分实际接入 | OPEN | v0.5.0 | 骨架已建，需配置 API Key 后测试 |
| G12 | P2 | 基本面LLM加工（研报摘要） | OPEN | v0.5.0 | Phase 7 远期规划 |

## v0.4.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G01 | 熔断器 | v0.4.0 | 实现 Breaker 类（CLOSED/OPEN/HALF_OPEN） |
| G02 | DuckDB 集成 | v0.4.0 | store/duckdb.py 新增加密持久化 store/load 方法 |
| G04 | 健康检查接口 | v0.4.0 | UnifiedDataProvider 新增 get_health() 方法 |
| G05 | 指标收集 | v0.4.0 | 新增 MetricsCollector（成功率/延迟/缓存命中率） |
| G06 | ETF/CB/REIT 支持 | v0.4.0 | DataType 已定义，基础数据获取已实现 |

## v0.3.0 已关闭差距

| 标题 | 关闭版本 | 说明 |
|:-----|:---------|:-----|
| SENTIMENT DataType 缺失 | v0.3.0 | 新增 SENTIMENT 枚举 + 情绪加工管线 |
| MARKET_STATE DataType 缺失 | v0.3.0 | 新增 MARKET_STATE 枚举 + 市场制度检测 |
| 情绪打分能力缺失 | v0.3.0 | 实现规则基线 + LLM 骨架（含降级） |
| 情绪聚合能力缺失 | v0.3.0 | 实现时间衰减+置信度加权聚合 |
| 市场制度检测缺失 | v0.3.0 | 实现 bull/bear/sideways 检测 |
| NEWS/MACRO 未接入统一API | v0.3.0 | 已接入 UnifiedDataProvider |

## v0.2.0 已关闭差距

| 标题 | 关闭版本 | 说明 |
|:-----|:---------|:-----|
| 期货特异 DataType 缺失 | v0.2.0 | 新增 6 个期货特异类型 |
| ETF/可转债 DataType 缺失 | v0.2.0 | 新增 6 个 ETF/CB 类型 |
| 新闻资讯模块缺失 | v0.2.0 | 新增 news/ 模块 + 分类器 |
| 宏观数据模块缺失 | v0.2.0 | 新增 macro/ 模块 |
