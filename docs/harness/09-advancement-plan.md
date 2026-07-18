# Data-Core Advancement Plan

Version: v0.4.0 | Updated: 2026-07-18

## Milestones

| 里程碑 | 版本 | 日期 | 状态 | 说明 |
|:-------|:-----|:-----|:-----|:-----|
| **M1** | **v0.1.0** | **2026-07-18** | ✅ **COMPLETED** | 基础可用版 |
| **M2** | **v0.2.0** | **2026-07-18** | ✅ **COMPLETED** | 能力增强版（期货深度+新闻+宏观） |
| **M3** | **v0.3.0** | **2026-07-18** | ✅ **COMPLETED** | 数据加工层（情绪管线+市场制度） |
| **M4** | **v0.4.0** | **2026-07-18** | ✅ **COMPLETED** | 工程完善版（健康检查+熔断+指标+ETF/CB） |
| M5 | v0.5.0 | TBD | PLANNED | 数据源完善版（国信 HTTP + 新闻抓取 + 宏观扩展） |
| M6 | v1.0.0 | TBD | PLANNED | 生产就绪版（DuckDB+调度器+监控） |

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

## M5 (v0.5.0) 规划

### 数据源完善（P1）
- [ ] 国信 HTTP 数据源正式接入
- [ ] 新闻数据源实际 HTTP 抓取
- [ ] 国家统计局/央行宏观源接入

### 期货基本面（P2）
- [ ] 期货基本面数据实际抓取

### LLM 能力增强（P2）
- [ ] LLM 情绪打分实际接入测试
- [ ] 基本面 LLM 加工（研报摘要）

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

### M4 → M5 晋级标准
- [ ] 国信 HTTP 数据源正式接入
- [ ] 新闻数据源实际 HTTP 抓取
- [ ] 国家统计局/央行宏观源接入
- [ ] 期货基本面数据实际抓取
- [ ] LLM 情绪打分实际接入测试
