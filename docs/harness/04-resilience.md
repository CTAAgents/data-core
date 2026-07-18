# Data-Core Resilience

Version: v0.4.0 | Updated: 2026-07-18

## Degradation Strategy

### 通用降级原则
- 每个数据类型维护独立的降级链
- 按优先级从高到低依次尝试
- 单个源失败不影响其他源
- 所有源不可用则返回 `UNAVAILABLE` grade
- 网络超时：3s 快速失败，立即尝试下一个源

### 熔断器降级（v0.4.0 新增，第 0 级前置保护）

在多层降级链之前，所有数据源调用先经过 Breaker 熔断器：

```
调用方 → Breaker（CLOSED） → 数据源（P0）
         Breaker（OPEN）   → 直接快速失败 → 降级到下一源
         Breaker（HALF_OPEN）→ 允许探测请求
```

| 状态 | 说明 | 行为 |
|:-----|:-----|:-----|
| `CLOSED` | 正常工作 | 请求正常通过，统计失败次数 |
| `OPEN` | 熔断开启 | 请求直接快速失败，不调用实际源 |
| `HALF_OPEN` | 半开探测 | 允许有限请求通过，成功则恢复 CLOSED，失败则回到 OPEN |

**状态转换**: CLOSED → (连续失败 ≥ max_failures) → OPEN → (recovery_timeout 后) → HALF_OPEN → (探测成功) → CLOSED / (探测失败) → OPEN

### 期货行情降级链
| 数据类型 | P0 | P1 | P2 |
|:---------|:---|:---|:---|
| OHLCV/QUOTE | TQ-Local | EastMoney | MemoryCache |
| 合约链/期限结构/价差 | TQ-Local | EastMoney | MemoryCache |

### 新闻资讯降级链
| 数据类型 | P0 | P1 | P2 | P3 |
|:---------|:---|:---|:---|:---|
| 快讯 | 财联社 | 华尔街见闻 | 东方财富研报 | 交易所公告 |

### 情绪数据降级链（v0.3.0 新增）
| 数据类型 | P0 (PRIMARY) | P1 (DAILY) | P2 (CACHED) |
|:---------|:-------------|:-----------|:------------|
| 情绪打分 | LLM 情绪打分 | 规则基线（词典法） | MemoryCache |

> **降级保证**: LLM 不可用时自动降级到规则基线（零成本模式），确保情绪数据始终可用。

### 市场制度检测
| 数据类型 | P0 | 说明 |
|:---------|:---|:-----|
| MARKET_STATE | MarketRegimeDetector | 纯计算，无外部依赖，始终可用 |

## 超时与重试

| 配置项 | 默认值 | 说明 |
|:-------|:-------|:-----|
| HTTP timeout | 3s | 单次请求超时 |
| LLM timeout | 30s | LLM 调用超时（隐含在 SDK 中） |
| 熔断器超时 | 5s | Breaker 包裹的调用超时（v0.4.0） |
| 熔断器恢复超时 | 30s | OPEN → HALF_OPEN 等待时间（v0.4.0） |
| Retry count | 0 | 不重试，直接降级 |

## 降级日志

每次降级触发时，在 DataPayload 的 `errors` 字段中记录失败原因。
情绪打分的 source 字段标识实际使用的打分方式：
- `llm`: LLM 打分成功
- `rule_fallback`: LLM 不可用，降级到规则基线
- `rule`: 直接使用规则基线
