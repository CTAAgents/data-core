# Data-Core Lifecycle

Version: v0.3.1 | Updated: 2026-07-18

## Module Phases

| Phase | Module | Status | Description |
|:------|:-------|:-------|:------------|
| Phase 1 | models/registry/store | COMPLETED | 数据模型、品种注册、存储层基础 |
| Phase 2 | futures providers | COMPLETED | 期货多源数据源 |
| Phase 3 | equity providers | COMPLETED | 股票多源数据源 |
| Phase 4 | equity/financial + guosen | BASIC | 股票财务数据 + 国信骨架 |
| Phase 5 | futures enhancement | COMPLETED | 期货合约链/期限结构/价差/基差 |
| Phase 6 | news module | COMPLETED | 新闻采集 + 分类器 |
| Phase 7 | macro module | COMPLETED | 宏观数据模块 |
| Phase 8 | processing layer | COMPLETED | 数据加工层：情绪管线 + 市场制度 |
| Phase 9 | Engineering (docs/tests) | IN PROGRESS | 工程化完善 |

## v0.3.0 产出物清单

### 新增模块
- `datacore/processing/` — 数据加工层（7个文件）
  - `base.py` — ProcessingStage 抽象基类
  - `models.py` — SentimentItem/SentimentData/MarketStateData/MarketRegime
  - `sentiment/sentiment_rule.py` — 规则情绪基线（词典法）
  - `sentiment/sentiment_llm.py` — LLM 情绪打分（含降级）
  - `sentiment/sentiment_aggregator.py` — 情绪聚合器（时间衰减+置信度加权）
  - `market_regime.py` — 市场制度检测（bull/bear/sideways）

### 增强模块
- `datacore/models/enums.py` — 新增 SENTIMENT/MARKET_STATE DataType
- `datacore/api.py` — 接入 SENTIMENT/MARKET_STATE/NEWS/MACRO 路由

### 新增测试
- `tests/test_processing.py` — 36 个用例

### 数据加工层能力
- ✅ 规则情绪基线（词典法，零成本，含否定词和程度副词处理）
- ✅ LLM 情绪打分骨架（含降级到规则基线）
- ✅ 情绪聚合器（时间衰减加权 + 置信度加权 + 按日聚合）
- ✅ 市场制度检测（趋势强度 + 波动率 + 成交量趋势综合判断）
- ✅ SENTIMENT/MARKET_STATE 接入 UnifiedDataProvider
