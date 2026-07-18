# Data-Core Observability

Version: v0.4.0 | Updated: 2026-07-18

## Data Quality Grades

每个 `DataPayload` 都携带 `grade` 字段：

| Grade | 说明 | 使用建议 |
|:------|:-----|:---------|
| `PRIMARY` | 官方数据源/LLM打分 | 可用于交易决策 |
| `DAILY` | 第三方数据/规则基线 | 可用于因子计算 |
| `CACHED` | 缓存数据 | 可用于分析，需标注 |
| `STALE` | 过期数据 | 低权重使用 |
| `UNAVAILABLE` | 所有源不可用 | 因子降级或跳过 |

## 数据加工层可观测性（v0.3.0 新增）

### 情绪数据元数据
每个 `SentimentItem` 携带完整的可观测信息：

| 字段 | 说明 |
|:-----|:-----|
| `score` | 情绪分数 (-1.0 ~ +1.0) |
| `confidence` | 置信度 (0.0 ~ 1.0) |
| `source` | 打分来源 (llm / rule / rule_fallback) |
| `tags` | 新闻分类标签 |
| `published_at` | 新闻发布时间 |
| `collected_at` | 打分时间 |

### 市场制度元数据
`MarketStateData` 携带检测特征：

| 字段 | 说明 |
|:-----|:-----|
| `regime` | 市场制度 (bull/bear/sideways/unknown) |
| `confidence` | 检测置信度 |
| `trend_strength` | 趋势强度 |
| `volatility` | 波动率（年化） |
| `volume_trend` | 成交量趋势 |
| `features` | 原始特征字典 |

## 健康检查接口（v0.4.0 新增）

`UnifiedDataProvider.get_health()` 返回各数据源实时可用状态：

| 返回字段 | 类型 | 说明 |
|:---------|:-----|:-----|
| `status` | str | 整体状态：healthy / degraded / unavailable |
| `sources` | dict | 各数据源状态详情 |
| `sources.{name}.available` | bool | 该源是否可用 |
| `sources.{name}.latency_ms` | float | 健康检查延迟（毫秒） |
| `sources.{name}.grade` | str | 数据质量等级 |
| `sources.{name}.last_error` | str | 最近错误信息（如有） |
| `sources.{name}.breaker_state` | str | 熔断器状态（CLOSED/OPEN/HALF_OPEN） |
| `timestamp` | str | 检查时间戳 |

健康检查覆盖的数据源列表：
- `tdx_local` — TQ-Local 通达信本地服务
- `eastmoney` — 东方财富 HTTP
- `tencent` — 腾讯财经
- `cls` — 财联社新闻
- `wallstreet` — 华尔街见闻
- `llm` — LLM 情绪打分服务

## 指标收集（v0.4.0 已实现）

已关闭差距: G05 [P2]

MetricsCollector 统计以下指标：

| 指标名称 | 类型 | 说明 |
|:---------|:-----|:-----|
| `calls_total` | Counter | 总调用次数（按数据源/方法维度） |
| `calls_success` | Counter | 成功调用次数 |
| `calls_failed` | Counter | 失败调用次数 |
| `success_rate` | Gauge | 成功率百分比（实时） |
| `latency_p50` | Gauge | 响应延迟 P50（毫秒） |
| `latency_p95` | Gauge | 响应延迟 P95（毫秒） |
| `latency_p99` | Gauge | 响应延迟 P99（毫秒） |
| `cache_hit_rate` | Gauge | 缓存命中率 |
| `cache_hits` | Counter | 缓存命中次数 |
| `cache_misses` | Counter | 缓存未命中次数 |
| `breaker_open_count` | Counter | 熔断器开启次数 |
| `breaker_half_open_count` | Counter | 熔断器半开探测次数 |

> 指标数据可通过 `MetricsCollector.report()` 获取完整快照。

## TODO / Gaps

- [G03 P2] 国信 HTTP 数据源正式接入（v0.5.0 规划）
- [G07 P2] 新闻数据源实际接入
- [G08 P2] 国家统计局/央行宏观源
- [G09 P2] 期货基本面数据抓取
- [G11 P2] LLM 情绪打分实际接入
- [G12 P2] 基本面LLM加工（研报摘要）
