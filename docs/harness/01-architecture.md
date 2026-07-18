# Data-Core Architecture

Version: v0.3.1 | Updated: 2026-07-18

## 1. System Positioning

Data-Core is an independent data infrastructure module providing unified data interfaces for FTS (Factor Trading System) and other research tools. All data sources are self-contained with zero external MCP/Skill/Agent dependencies.

Data-Core is responsible for data collection and processing (including LLM-based sentiment scoring and market regime detection), while FTS is responsible for factor evolution and strategy generation.

**v0.3.0 边界更新**: SENTIMENT/MARKET_STATE 由 Data-Core 数据加工层产出（含LLM打分+聚合），FTS 直接消费。

## 2. Layered Architecture

```
UnifiedDataProvider (api.py)
  ├── futures/          # 期货数据模块
  │   ├── futures_provider.py    # 期货统一入口
  │   └── providers/             # 多源降级链
  │       ├── tdx_lc.py          # TQ-Local (P0)
  │       └── eastmoney.py       # 东方财富 (P1)
  ├── equity/           # 股票数据模块
  │   ├── equity_provider.py     # 股票统一入口
  │   ├── financial.py           # 财务数据
  │   └── providers/             # 多源降级链
  │       ├── tencent.py         # 腾讯财经 (P0)
  │       └── eastmoney.py       # 东方财富 (P1)
  ├── news/             # 新闻资讯模块（v0.2.0）
  │   ├── news_provider.py       # 新闻统一入口
  │   ├── classifier.py          # 新闻分类器
  │   └── providers/             # 多源降级链
  ├── macro/            # 宏观数据模块（v0.2.0）
  │   └── macro_provider.py      # 宏观统一入口
  ├── processing/       # 数据加工层（v0.3.0 新增）
  │   ├── base.py                # ProcessingStage 抽象基类
  │   ├── models.py              # SentimentItem/SentimentData/MarketStateData
  │   ├── sentiment/             # 情绪加工管线
  │   │   ├── sentiment_rule.py  # 规则情绪基线（词典法，零成本）
  │   │   ├── sentiment_llm.py   # LLM 情绪打分（高质量）
  │   │   └── sentiment_aggregator.py  # 情绪聚合器
  │   └── market_regime.py       # 市场制度检测（bull/bear/sideways）
  ├── models/           # 数据模型与枚举
  │   └── enums.py               # DataType/MarketType/SourceGrade
  ├── registry/         # 品种注册表
  ├── store/            # 存储层（缓存+持久化）
  └── config.py         # 统一配置系统
```

## 3. DataType 体系（v0.3.0 更新）

### 通用类型（全市场）
- `OHLCV`, `QUOTE`, `TECHNICAL`, `FINANCIAL`, `FUNDAMENTAL`
- `MACRO`, `NEWS`, `ANNOUNCEMENT`
- `SENTIMENT` (v0.3.0): 情绪数据，Data-Core 数据加工层产出
- `MARKET_STATE` (v0.3.0): 市场制度，Data-Core 数据加工层产出

### 期货特异类型
- `FUTURES_CONTRACT_CHAIN`, `FUTURES_TERM_STRUCTURE`, `FUTURES_SPREAD`
- `FUTURES_BASIS`, `FUTURES_POSITION`, `FUTURES_WAREHOUSE_RECEIPT`

### ETF/可转债特异类型
- `ETF_NAV`, `ETF_PREMIUM`, `ETF_FUND_FLOW`
- `CB_CONVERSION`, `CB_TERMS`, `CB_PURE_BOND`

## 4. 数据加工层（v0.3.0 新增）

### 情绪加工管线
```
NEWS (Data-Core 采集+分类)
  → SentimentLLMStage (P0, LLM打分)
  → SentimentRuleStage (P1, 词典法降级)
  → SentimentAggregator (按品种/时间聚合)
  → SENTIMENT (FTS 直接消费)
```

### 市场制度检测
```
OHLCV (Data-Core 采集)
  → MarketRegimeDetector (趋势/波动率/成交量综合判断)
  → MARKET_STATE (bull/bear/sideways, FTS 直接消费)
```

## 5. Data Source Fallback Chain

### 期货行情降级链
- TQ-Local (P0) → EastMoney HTTP (P1) → MemoryCache (P2)

### 新闻资讯降级链
- 财联社 (P0) → 华尔街见闻 (P1) → 东方财富研报 (P2)

### 情绪数据降级链（v0.3.0 新增）
- LLM 情绪打分 (P0, PRIMARY) → 规则基线 (P1, DAILY) → Cached (P2)

## 6. 核心边界原则

| 原则 | 说明 |
|:-----|:-----|
| **能力导向** | LLM 是 AI 原生项目的基本工具，边界按"能力与职责"划分 |
| **数据归 Data-Core** | 采集 + 加工（含LLM） + 存储 + 服务 |
| **因子归 FTS** | 因子发现 + 评估 + 组合 + 演化 |
| **决策归 FDT** | 辩论 + 风控 + 信号 + 执行 |
| **上下游不可逆** | Data-Core ← FTS ← FDT |
