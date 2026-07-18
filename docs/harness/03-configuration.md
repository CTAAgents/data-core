# Data-Core Configuration

Version: v1.0.0 | Updated: 2026-07-19

## Config Sources (priority high to low)

- P0: Environment variables (`DATACORE_*` prefix)
- P1: `config/settings.yaml`
- P2: Code defaults

## Key Config Items

### 通用配置
| 环境变量 | 默认值 | 说明 |
|:---------|:-------|:-----|
| `DATACORE_LOG_LEVEL` | `INFO` | 日志级别 |
| `DATACORE_TIMEOUT` | `3` | HTTP 请求超时时间（秒） |
| `DATACORE_CACHE_TTL` | `3600` | 内存缓存 TTL（秒） |

### TQ-Local 配置
| 环境变量 | 默认值 | 说明 |
|:---------|:-------|:-----|
| `DATACORE_TDX_URL` | `http://127.0.0.1:17709/` | TQ-Local 服务地址 |
| `DATACORE_TDX_TIMEOUT` | `3` | TQ-Local 请求超时 |

### 存储配置
| 环境变量 | 默认值 | 说明 |
|:---------|:-------|:-----|
| `DATACORE_DB_PATH` | `~/.datacore/datacore.db` | DuckDB 数据库路径 |
| `DATACORE_REDIS_URL` | `redis://localhost:6379/0` | Redis 连接地址（可选） |
| `DATACORE_PG_URL` | 空 | PostgreSQL 连接地址（可选） |

### 熔断器配置（v0.4.0 新增）
| 环境变量 | 默认值 | 说明 |
|:---------|:-------|:-----|
| `DATACORE_CB_TIMEOUT` | `5` | 熔断器调用超时（秒） |
| `DATACORE_CB_MAX_FAILURES` | `5` | 连续失败次数触发 OPEN |
| `DATACORE_CB_RECOVERY_TIMEOUT` | `30` | HALF_OPEN 探测间隔（秒） |

### 指标收集配置（v0.4.0 新增）
| 环境变量 | 默认值 | 说明 |
|:---------|:-------|:-----|
| `DATACORE_METRICS_ENABLED` | `true` | 是否启用指标收集 |
| `DATACORE_METRICS_MAX_ENTRIES` | `10000` | 指标最大记录条数 |

### 国信证券配置
| 环境变量 | 默认值 | 说明 |
|:---------|:-------|:-----|
| `DATACORE_GUOSEN_API_KEY` | 空 | 国信证券 API Key |

### LLM 配置（v0.3.0 新增）
| 环境变量 | 默认值 | 说明 |
|:---------|:-------|:-----|
| `DATACORE_LLM_API_KEY` | 空 | LLM API Key（用于情绪打分） |
| `DATACORE_LLM_MODEL` | `gpt-4o-mini` | LLM 模型名称 |

> **降级策略**: 未配置 LLM API Key 时，情绪打分自动降级到规则基线（词典法）。

### 新闻/宏观模块配置
| 环境变量 | 默认值 | 说明 |
|:---------|:-------|:-----|
| `DATACORE_NEWS_SOURCES` | `cls,wallstreet,eastmoney` | 启用的新闻源 |
| `DATACORE_NEWS_CACHE_TTL` | `1800` | 新闻缓存 TTL（秒） |
| `DATACORE_MACRO_SOURCES` | `national_bureau,pboc,eastmoney` | 启用的宏观数据源（v0.5.0 更新） |
| `DATACORE_MACRO_CACHE_TTL` | `86400` | 宏观数据缓存 TTL（秒） |

### WebSocket 配置（v1.0.0 新增）
| 环境变量 | 默认值 | 说明 |
|:---------|:-------|:-----|
| `DATACORE_WS_URL` | `wss://example.com/market` | WebSocket 服务地址 |
| `DATACORE_WS_RECONNECT_INTERVAL` | `5` | 重连间隔（秒） |
| `DATACORE_WS_MAX_RECONNECT` | `10` | 最大重连次数 |
| `DATACORE_WS_HEARTBEAT_INTERVAL` | `30` | 心跳间隔（秒） |
| `DATACORE_WS_SUBSCRIBE_SYMBOLS` | 空 | 默认订阅品种列表（逗号分隔） |

### 告警配置（v1.0.0 新增）
| 环境变量 | 默认值 | 说明 |
|:---------|:-------|:-----|
| `DATACORE_ALERT_FILE_PATH` | `~/.datacore/alerts.log` | 告警日志文件路径 |
| `DATACORE_ALERT_WEBHOOK_URL` | 空 | 告警 Webhook 回调地址 |
| `DATACORE_ALERT_PRICE_THRESHOLD` | `0.05` | 价格突破阈值（5%） |
| `DATACORE_ALERT_VOLATILITY_THRESHOLD` | `0.03` | 波动率异常阈值（3%） |
| `DATACORE_ALERT_STALE_SECONDS` | `300` | 数据延迟告警阈值（秒） |

### 基准测试配置（v1.0.0 新增）
| 环境变量 | 默认值 | 说明 |
|:---------|:-------|:-----|
| `DATACORE_BENCHMARK_ITERATIONS` | `100` | 基准测试迭代次数 |
| `DATACORE_BENCHMARK_WARMUP` | `10` | 预热迭代次数 |

> **安全提示**: API Key 等敏感信息请通过环境变量配置，**禁止硬编码到代码中**。
