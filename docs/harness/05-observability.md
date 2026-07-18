# Data-Core Observability

Version: v1.0.0 | Updated: 2026-07-19

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
- `guosen` — 国信证券（v0.5.0 新增）
- `national_bureau` — 国家统计局（v0.5.0 新增）
- `pboc` — 央行（v0.5.0 新增）
- `exchange_api` — 交易所官方（v0.5.0 新增）
- `shengyishe` — 生意社（v0.5.0 新增）
- `memory_cache` — 内存缓存状态（v0.5.0 新增）
- `duckdb_cache` — DuckDB 缓存状态（v0.5.0 新增）
- `websocket` — WebSocket 连接状态（v1.0.0 新增）
- `alert_engine` — 告警引擎状态（v1.0.0 新增）

## 缓存层可观测性（v0.5.0 新增）

### 缓存命中流
```
请求 → MemoryCache 检查 → DuckDB 检查 → HTTP 源
        ↓ 命中           ↓ 命中
    返回 CACHED      返回 CACHED
```

### 缓存状态字段
每个 DataPayload 的 `source` 字段标识数据来源：
- `memory_cache`: 来自 L1 内存缓存
- `duckdb_cache`: 来自 L2 DuckDB 持久化缓存
- `tdx_lc`, `eastmoney`, etc.: 来自 HTTP 实时数据源

### 健康检查中的缓存状态
`get_health()` 新增缓存层状态：
- `memory_cache.available`: 始终 true
- `memory_cache.grade`: "active"
- `duckdb_cache.available`: DuckDB 是否可用
- `duckdb_cache.grade`: "active" / "unavailable"

## WebSocket 可观测性（v1.0.0 新增）

### WebSocket 状态
| 指标 | 说明 |
|:-----|:-----|
| `ws_connected` | 连接状态 (bool) |
| `ws_reconnect_count` | 累计重连次数 |
| `ws_last_heartbeat` | 最后一次心跳时间 |
| `ws_subscribed_symbols` | 当前订阅品种数 |

### 健康检查中的 WebSocket 状态
`get_health()` 新增：
- `websocket.available`: WebSocket 是否连接
- `websocket.grade`: "active" / "disconnected"
- `websocket.reconnect_count`: 重连次数

## 告警系统可观测性（v1.0.0 新增）

### 告警指标
| 指标名称 | 类型 | 说明 |
|:---------|:-----|:-----|
| `alerts_triggered_total` | Counter | 告警触发总数 |
| `alerts_by_rule` | Counter | 按规则分类的告警数（price_breakout/volatility_anomaly/data_stale/breaker_trip） |
| `alerts_by_channel` | Counter | 按渠道分类的告警数（webhook/file/log） |
| `alerts_channel_fallback` | Counter | 渠道降级次数 |
| `alerts_success_rate` | Gauge | 告警通知成功率 |

### 健康检查中的告警状态
`get_health()` 新增：
- `alert_engine.available`: 告警引擎是否运行
- `alert_engine.grade`: "active" / "degraded"

## 指标收集（v0.4.0 已实现，v1.0.0 扩展）

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
| `ws_reconnect_count` | Counter | WebSocket 重连次数（v1.0.0 新增） |
| `alerts_triggered_total` | Counter | 告警触发总数（v1.0.0 新增） |

> 指标数据可通过 `MetricsCollector.report()` 获取完整快照。

## 安全审计可观测性（v1.0.0 新增）

已通过的安全审计检查（docs/SECURITY_CHECKLIST.md）：
| 检查项 | 说明 | 状态 |
|:-------|:-----|:-----|
| 认证安全 | API Key 通过环境变量传输，不硬编码 | ✅ |
| 数据加密 | DuckDB 存储加密，敏感字段脱敏 | ✅ |
| 注入防护 | SQL 参数化查询，HTTP 输入校验 | ✅ |
| 配置安全 | 敏感配置仅环境变量，默认值安全 | ✅ |
| 依赖安全 | 依赖版本锁定，无已知漏洞 | ✅ |
| 日志安全 | 不记录敏感信息（API Key/密码） | ✅ |
| 通信安全 | HTTPS/WS 加密传输 | ✅ |
