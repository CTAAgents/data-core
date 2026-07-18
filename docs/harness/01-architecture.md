# Data-Core Architecture

Version: v1.0.0 | Updated: 2026-07-19

## 1. System Positioning

Data-Core is an independent data infrastructure module providing unified data interfaces for FTS (Factor Trading System) and other research tools. All data sources are self-contained with zero external MCP/Skill/Agent dependencies.

Data-Core is responsible for data collection and processing (including LLM-based sentiment scoring and market regime detection), while FTS is responsible for factor evolution and strategy generation.

**v0.3.0 边界更新**: SENTIMENT/MARKET_STATE 由 Data-Core 数据加工层产出（含LLM打分+聚合），FTS 直接消费。

**v0.4.0 边界更新**: 新增 Breaker 熔断层、MetricsCollector 指标收集框架、DuckDB 持久化数据流。

**v0.5.0 边界更新**: 新增 5 个数据源（国家统计局/央行/交易所/生意社/国信），DuckDB 接入 api.py 作为 L2 缓存层，多源降级链全面扩展。

**v0.6.0 边界更新**: 新增 LLM 情绪打分端到端验证，基本面 LLM 加工模块（研报摘要 + 财报提取）。

**v1.0.0 边界更新**: 新增 WebSocket 实时行情管理、告警引擎、性能基准测试框架、安全审计清单。

## 2. Layered Architecture

```
UnifiedDataProvider (api.py)
  ├── Breaker (熔断层, v0.4.0 新增)
  │   └── 包裹所有数据源调用（CLOSED/OPEN/HALF_OPEN）
  ├── MetricsCollector (指标收集, v0.4.0 新增)
  │   └── 统计调用次数/成功率/延迟/缓存命中率
  ├── Cache Layer (v0.5.0: MemoryCache → DuckDB)
  │   ├── L1: MemoryCache（内存缓存）
  │   └── L2: DuckDB（持久化缓存，仅 OHLCV）
  ├── futures/          # 期货数据模块
  │   ├── futures_provider.py    # 期货统一入口（4 源降级链）
  │   └── providers/             # 多源降级链
  │       ├── tdx_lc.py          # TQ-Local (P0)
  │       ├── eastmoney.py       # 东方财富 (P1)
  │       ├── exchange_api.py    # 交易所官方（上期所/郑商所/大商所）(P2, v0.5.0)
  │       └── shengyishe.py      # 生意社现货/基差 (P2, v0.5.0)
  ├── equity/           # 股票数据模块
  │   ├── equity_provider.py     # 股票统一入口（3 源降级链）
  │   ├── financial.py           # 财务数据
  │   └── providers/             # 多源降级链
  │       ├── tencent.py         # 腾讯财经 (P0)
  │       ├── eastmoney.py       # 东方财富 (P1)
  │       └── guosen.py          # 国信证券 (P2, v0.5.0)
  ├── news/             # 新闻资讯模块（v0.2.0）
  │   ├── news_provider.py       # 新闻统一入口
  │   ├── classifier.py          # 新闻分类器
  │   └── providers/             # 多源降级链
  ├── macro/            # 宏观数据模块（v0.2.0）
  │   ├── macro_provider.py      # 宏观统一入口（3 源降级链, v0.5.0 新增）
  │   └── providers/             # 多源降级链
  │       ├── eastmoney_macro.py # 东方财富宏观 (P2)
  │       ├── national_bureau.py # 国家统计局 (P0, v0.5.0)
  │       └── pboc.py            # 央行 (P1, v0.5.0)
  ├── processing/       # 数据加工层（v0.3.0 新增）
  │   ├── base.py                # ProcessingStage 抽象基类
  │   ├── models.py              # SentimentItem/SentimentData/MarketStateData
  │   ├── sentiment/             # 情绪加工管线
  │   │   ├── sentiment_rule.py  # 规则情绪基线（词典法，零成本）
  │   │   ├── sentiment_llm.py   # LLM 情绪打分（高质量，v0.6.0 端到端验证）
  │   │   └── sentiment_aggregator.py  # 情绪聚合器
  │   ├── market_regime.py       # 市场制度检测（bull/bear/sideways）
  │   └── fundamental/           # 基本面 LLM 加工（v0.6.0 新增）
  │       ├── fundamental_llm.py # 研报摘要 + 财报提取
  │       └── models.py          # 基本面加工数据模型
  ├── stream/           # WebSocket 实时行情（v1.0.0 新增）
  │   └── stream.py             # StreamQuote + WebSocketManager
  ├── alert/            # 告警引擎（v1.0.0 新增）
  │   └── alert.py              # AlertEngine + 预置规则 + 3 通知渠道
  ├── store/            # 存储层（缓存+持久化）
  │   ├── cache.py               # MemoryCache 内存缓存
  │   └── duckdb.py              # DuckDB 持久化（v0.4.0 新增加密存读，v0.5.0 接入缓存层）
  ├── models/           # 数据模型与枚举
  │   └── enums.py               # DataType/MarketType/SourceGrade
  ├── registry/         # 品种注册表
  └── config.py         # 统一配置系统

# 数据持久化流（v0.4.0）
api.py → store/duckdb.py → DuckDB 数据库
  - store(key, value): 加密持久化写入
  - load(key): 加密持久化读取
  - 按类型（kline/quote/macro 等）提供具体存读方法

# 缓存层数据流（v0.5.0）
请求 → MemoryCache (L1) → DuckDB (L2, 仅 OHLCV) → HTTP 数据源
  - L1 命中: 直接返回 CACHED 数据，无网络开销
  - L1 未命中 L2 命中: 从 DuckDB 加载 K 线，写回 MemoryCache
  - L1/L2 均未命中: 走降级链获取 HTTP 数据，写回 L1 + L2

# WebSocket 实时数据流（v1.0.0）
WebSocketManager → 行情订阅 → 数据回调 → 告警引擎
  - 连接管理：自动重连 + 心跳保活
  - 订阅管理：按品种/类型分发行情
  - 告警触发：预置规则检测 → 渠道通知（日志/文件/Webhook）

# 告警引擎数据流（v1.0.0）
AlertEngine → 规则匹配 → 渠道分发
  - 预置规则：价格突破/波动率异常/数据延迟/熔断触发
  - 通知渠道：日志记录 / 文件写入 / Webhook 回调
```

## 3. DataType 体系（v0.4.0 更新）

### 通用类型（全市场）
- `OHLCV`, `QUOTE`, `TECHNICAL`, `FINANCIAL`, `FUNDAMENTAL`
- `MACRO`, `NEWS`, `ANNOUNCEMENT`
- `SENTIMENT` (v0.3.0): 情绪数据，Data-Core 数据加工层产出
- `MARKET_STATE` (v0.3.0): 市场制度，Data-Core 数据加工层产出

### 期货特异类型
- `FUTURES_CONTRACT_CHAIN`, `FUTURES_TERM_STRUCTURE`, `FUTURES_SPREAD`
- `FUTURES_BASIS`, `FUTURES_POSITION`, `FUTURES_WAREHOUSE_RECEIPT`

### ETF/可转债/REIT 特异类型（v0.4.0 已实现基础获取）
- `ETF_NAV`, `ETF_PREMIUM`, `ETF_FUND_FLOW`
- `CB_CONVERSION`, `CB_TERMS`, `CB_PURE_BOND`

## 4. v1.0.0 新增组件

| 组件 | 文件 | 说明 |
|:-----|:-----|:-----|
| WebSocket 实时行情 | datacore/stream.py | WebSocket 连接管理、自动重连、心跳保活、行情订阅分发 |
| 告警引擎 | datacore/alert.py | AlertEngine + 预置规则 + 3 个通知渠道（日志/文件/Webhook） |
| 性能基准测试 | tests/benchmark_test.py | 8 个基准测试（数据获取/缓存/加工/并发） |
| 安全审计清单 | docs/SECURITY_CHECKLIST.md | 7 项安全检查全部通过（认证/加密/注入/配置/依赖/日志/通信） |

### WebSocket 实时行情（v1.0.0）

```
StreamQuote (数据模型)
  ├── symbol: str              # 品种代码
  ├── price: float             # 最新价
  ├── volume: float            # 成交量
  ├── timestamp: datetime      # 时间戳
  └── exchange: str            # 交易所

WebSocketManager (连接管理)
  ├── connect(url)             # 建立 WebSocket 连接
  ├── subscribe(symbols)       # 订阅品种行情
  ├── on_quote(callback)       # 行情回调注册
  ├── auto_reconnect           # 自动重连（指数退避）
  └── heartbeat                # 心跳保活
```

### 告警引擎（v1.0.0）

```
AlertEngine (告警引擎)
  ├── 预置规则
  │   ├── price_breakout       # 价格突破（涨跌幅超阈值）
  │   ├── volatility_anomaly   # 波动率异常
  │   ├── data_stale           # 数据延迟告警
  │   └── breaker_trip         # 熔断触发告警
  ├── 通知渠道
  │   ├── log_channel          # 日志记录
  │   ├── file_channel         # 文件写入
  │   └── webhook_channel      # Webhook 回调
  └── 规则可配置（阈值/渠道/启用状态）
```

## 5. 数据加工层（v0.3.0 新增，v0.6.0 扩展）

### 情绪加工管线
```
NEWS (Data-Core 采集+分类)
  → SentimentLLMStage (P0, LLM打分, v0.6.0 端到端验证)
  → SentimentRuleStage (P1, 词典法降级)
  → SentimentAggregator (按品种/时间聚合)
  → SENTIMENT (FTS 直接消费)
```

### 基本面 LLM 加工管线（v0.6.0 新增）
```
研报/财报 (Data-Core 采集)
  → FundamentalLLMStage (LLM 摘要提取)
  → 结构化输出
  → FUNDAMENTAL (FTS 直接消费)
```

### 市场制度检测
```
OHLCV (Data-Core 采集)
  → MarketRegimeDetector (趋势/波动率/成交量综合判断)
  → MARKET_STATE (bull/bear/sideways, FTS 直接消费)
```

## 6. Data Source Fallback Chain

### 期货行情降级链（v0.5.0 扩展）
- TQ-Local (P0) → 东方财富 (P1) → 交易所官方 (P2) → 生意社 (P2)

### 期货基本面降级链（v0.5.0 新增）
| 数据类型 | P0 | P1 |
|:---------|:---|:---|
| 基差 | 生意社 | 东方财富（近似算法） |
| 持仓排名 | 交易所官方 | 东方财富 |
| 仓单 | 交易所官方 | 东方财富 |

### A 股降级链（v0.5.0 扩展）
- 腾讯财经 (P0) → 东方财富 (P1) → 国信证券 (P2)

### 宏观数据降级链（v0.5.0 新增）
- 国家统计局 (P0) → 央行 (P1) → 东方财富 (P2)

### 新闻资讯降级链
- 财联社 (P0) → 华尔街见闻 (P1) → 东方财富研报 (P2)

### 情绪数据降级链（v0.3.0 新增，v0.6.0 验证）
- LLM 情绪打分 (P0, PRIMARY) → 规则基线 (P1, DAILY) → Cached (P2)

### WebSocket 降级链（v1.0.0 新增）
- WebSocket 实时行情 (P0) → HTTP 轮询行情 (P1) → 缓存行情 (P2)

### 告警降级链（v1.0.0 新增）
- Webhook 通知 (P0) → 文件写入 (P1) → 日志记录 (P2)

## 7. 核心边界原则

| 原则 | 说明 |
|:-----|:-----|
| **能力导向** | LLM 是 AI 原生项目的基本工具，边界按"能力与职责"划分 |
| **数据归 Data-Core** | 采集 + 加工（含LLM） + 存储 + 服务 + 实时行情 + 告警 |
| **因子归 FTS** | 因子发现 + 评估 + 组合 + 演化 |
| **决策归 FDT** | 辩论 + 风控 + 信号 + 执行 |
| **上下游不可逆** | Data-Core ← FTS ← FDT |
