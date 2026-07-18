# Data-Core Observability

Version: v0.3.0 | Updated: 2026-07-18

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

## 指标收集（规划中）

已登记差距: G05 [P2]

| 指标 | 说明 |
|:-----|:-----|
| 数据源成功率 | 每个源的成功/失败比率 |
| LLM 调用成功率 | LLM 情绪打分成功率 |
| 降级触发次数 | LLM→规则降级频率 |
| 响应延迟 P50/P95 | 各源响应时间分布 |
| 缓存命中率 | MemoryCache 命中比率 |

## TODO / Gaps

- [G05 P2] 指标收集框架
- [G04 P1] 健康检查接口
- [G01 P2] 熔断器状态可观测
