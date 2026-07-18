# Data-Core 能力提升与完善计划

> 版本: v0.3.0 (规划中)
> 目的: 完善 Data-Core 的数据能力，满足 FTS 因子演化对期货基本面、技术指标、期限结构、新闻资讯等数据的需求
> 前置条件: FTS CODE_WIKI.md v2.2 已确认项目边界 — Data-Core 负责数据采集+数据加工（含LLM），FTS 负责因子演化+策略生成

---

## 目录

1. [当前能力评估](#1-当前能力评估)
2. [FTS 因子演化的数据需求分析](#2-fts-因子演化的数据需求分析)
3. [DataType 粒度设计原则](#3-datatype-粒度设计原则)
4. [数据能力提升方案](#4-数据能力提升方案)
5. [实施路线图](#5-实施路线图)
6. [数据源扩展](#6-数据源扩展)
7. [与 FTS 的接口契约](#7-与-fts-的接口契约)
8. [核心边界原则](#8-核心边界原则)

---

## 1. 当前能力评估

### 1.1 DataType 支持矩阵

| DataType | 期货模块 (FuturesDataProvider) | A股模块 (EquityDataProvider) | 说明 |
|:---------|:------------------------------|:----------------------------|:-----|
| `OHLCV` | ✅ TdxLc + EastMoney | ✅ Tencent + EastMoney | 主力合约 K线 |
| `QUOTE` | ✅ TdxLc | ✅ Tencent | 实时行情快照 |
| `TECHNICAL` | ⚠️ TdxLc 声明支持，未实现 | ❌ 未声明 | 技术指标 |
| `FUNDAMENTAL` | ❌ 未声明 | ✅ EastMoney (PE/PB) | 基本面数据 |
| `MACRO` | ❌ 未声明 | ✅ EastMoney | 宏观数据 |
| `NEWS` | ❌ 未声明（待新增） | ❌ 未声明（待新增） | 新闻资讯（含分类标签） |
| `ANNOUNCEMENT` | ❌ 未声明（待新增） | ❌ 未声明（待新增） | 公告 |
| `SENTIMENT` | ⚠️ 数据加工层产出（规划中） | ⚠️ 数据加工层产出（规划中） | 情绪数据（Data-Core 数据加工层产出，含LLM打分） |
| `MARKET_STATE` | ⚠️ 数据加工层产出（规划中） | ⚠️ 数据加工层产出（规划中） | 市场制度（Data-Core 数据加工层产出，含market_regime检测） |

> **边界说明（v0.3.0 更新）**:
> - `NEWS`/`ANNOUNCEMENT` 由 Data-Core 采集并加工（含分类标签）
> - `SENTIMENT`/`MARKET_STATE` 由 **Data-Core 数据加工层**产出（含 LLM 情绪打分、规则基线、情绪聚合、market_regime 检测），FTS 直接消费已加工好的情绪数据
> - LLM 是 AI 原生项目的基本能力，不作为边界划分标准

### 1.2 期货模块能力差距

| 数据类型 | 子类型 | 数据源 | 当前状态 | 优先级 |
|:---------|:-------|:-------|:---------|:-------|
| **仓单** | 交易所仓单数量/变化 | 上期所/郑商所/大商所官网 | ❌ 未实现 | P0 |
| **基差** | 现货价格-期货价格 | 生意社/我的钢铁网/卓创资讯 | ❌ 未实现 | P0 |
| **库存** | 社会库存/厂库/港口库存 | 生意社/我的钢铁网 | ❌ 未实现 | P1 |
| **持仓** | 持仓排名/增减仓 | 交易所官网 | ❌ 未实现 | P1 |
| **期限结构** | 多合约链/价差/展期收益 | TdxLc（已有多合约） | ❌ 未封装 | P0 |
| **技术指标** | ADX/ATR/MACD/布林带等 | TdxLc API | ⚠️ 未实现 | P1 |
| **宏观** | PMI/LPR/CPI/GDP/M2 | 国家统计局/央行 | ❌ 未实现 | P1 |

### 1.3 新闻资讯能力差距（v0.2.0 新增）

| 数据类型 | 子类型 | 数据源 | 当前状态 | 优先级 |
|:---------|:-------|:-------|:---------|:-------|
| **新闻采集** | 财联社/华尔街见闻/东方财富研报 | 各源 API/网页 | ❌ 未实现 | P1 |
| **公告采集** | 交易所公告 | 交易所官网 | ❌ 未实现 | P1 |
| **社交舆情** | 雪球/微博 | 平台 API | ❌ 未实现 | P2 |
| **新闻分类** | 宏观/产业/公司/政策 | Data-Core 数据加工层 | ❌ 未实现 | P1 |
| **结构化抽取** | 实体/品种/事件 | Data-Core 数据加工层 | ❌ 未实现 | P2 |

### 1.4 数据加工层能力差距（v0.3.0 新增）

> **背景**: AI 原生项目中 LLM 是基本能力，边界应基于"能力与职责"而非"是否纯Python代码"。
> Data-Core 负责从原始数据 → 可消费的结构化数据（含 LLM 加工），FTS 负责因子演化与策略。

| 数据加工能力 | 子类型 | 实现方式 | 当前状态 | 优先级 |
|:------------|:-------|:---------|:---------|:-------|
| **情绪打分（LLM）** | 新闻/公告情绪评分 | LLM 调用（Data-Core 数据加工层） | ❌ 未实现 | P1 |
| **情绪打分（规则）** | 词典法基线打分 | 规则引擎（零成本模式） | ❌ 未实现 | P1 |
| **情绪聚合** | 按品种/时间聚合情绪分数 | 加权聚合 + 衰减 | ❌ 未实现 | P1 |
| **市场制度检测** | bull/bear/neutral/sideways | market_regime 模块 | ❌ 未实现 | P1 |
| **基本面LLM加工** | 研报/财报结构化摘要 | LLM 调用 | ❌ 未实现 | P2 |

---

## 2. FTS 因子演化的数据需求分析

### 2.1 因子类型与数据依赖映射

根据 FTS CODE_WIKI.md v2.2 的因子体系设计：

```
FTS 因子库
├── 通用因子（全市场，OHLCV）
│   └── 依赖: OHLCV, QUOTE
│
├── 期货专用因子（FUTURES only）
│   ├── 期限结构类 → 依赖: FUTURES_CONTRACT_CHAIN, FUTURES_TERM_STRUCTURE
│   ├── 基差类 → 依赖: FUTURES_BASIS
│   ├── 跨期价差类 → 依赖: FUTURES_SPREAD
│   └── 持仓类 → 依赖: FUTURES_POSITION, FUNDAMENTAL(inventory)
│
├── 股票专用因子（STOCK only）
│   ├── 价值类 → 依赖: FINANCIAL(PE/PB)
│   ├── 质量类 → 依赖: FINANCIAL(ROE/ROIC)
│   └── 成长类 → 依赖: FINANCIAL(营收增长)
│
├── ETF/REITs 专用因子
│   ├── 折溢价类 → 依赖: ETF_NAV, ETF_PREMIUM
│   └── 资金流类 → 依赖: ETF_FUND_FLOW
│
├── 可转债专用因子（CB only）
│   └── 转股类 → 依赖: CB_CONVERSION
│
└── 情绪因子（全市场，Data-Core 加工层产出）
    └── 依赖: SENTIMENT (Data-Core 数据加工层产出) + MARKET_STATE (Data-Core 数据加工层产出)
    注: 情绪因子的原始数据采集和加工（含LLM打分）全部由 Data-Core 完成，FTS 直接消费 SENTIMENT 数据
```

### 2.2 期货数据需求优先级

| 优先级 | 数据类型 | 影响的因子 | 说明 |
|:-------|:---------|:-----------|:-----|
| **P0** | 期限结构/合约链 | 展期收益、期限结构斜率、跨期价差 | 期货最核心的 Alpha 来源 |
| **P0** | 基差 | 基差率、基差动量 | 期货特有因子 |
| **P1** | 仓单/库存 | 库存代理、供需平衡 | 基本面因子 |
| **P1** | 持仓排名 | 持仓集中度、主力动向 | 资金流因子 |
| **P1** | 宏观数据 | 宏观动量、政策因子 | 全市场通用 |
| **P1** | 情绪数据（SENTIMENT） | 情绪因子 | Data-Core 数据加工层产出（含LLM），FTS 直接消费 |
| **P1** | 市场制度（MARKET_STATE） | regime-aware 因子 | Data-Core 数据加工层产出 |
| **P2** | 技术指标 | 趋势强度、波动率 | 已有 OHLCV 可自行计算 |

---

## 3. DataType 粒度设计原则

### 3.1 设计准则

| 原则 | 说明 |
|:-----|:-----|
| **Data-Core 负责数据定义和获取** | DataType 的细粒度定义应在 Data-Core 中完成，确保数据标准化 |
| **FTS 负责消费和编排** | FTS 通过声明依赖的 DataType 获取数据，不关心数据来源 |
| **粒度适度细化** | 既要满足因子精确声明，又要避免过度细分导致管理复杂度 |
| **市场特异类型以市场前缀区分** | 如 `FUTURES_BASIS`, `ETF_NAV`，避免通用类型歧义 |
| **分层设计** | 通用类型（OHLCV/QUOTE）→ 市场特异类型（FUTURES_*/ETF_*）→ 子类型（通过 params 区分） |
| **数据加工归 Data-Core** | 新闻分类、结构化抽取、情绪打分、market_regime 等基础加工由 Data-Core 完成 |
| **LLM 是基本能力** | LLM 调用是 AI 原生项目的基本要求，不构成独立模块的边界划分依据 |

### 3.2 DataType 层级设计

```
DataType 层级结构
├── 通用类型（全市场）
│   ├── OHLCV          # K线数据
│   ├── QUOTE          # 实时行情
│   ├── TECHNICAL      # 技术指标
│   ├── FINANCIAL      # 财务指标（股票）
│   ├── MACRO          # 宏观数据
│   ├── NEWS           # 新闻资讯（Data-Core 采集+分类，携带 tags）
│   ├── ANNOUNCEMENT   # 公告（Data-Core 采集）
│   ├── FUNDAMENTAL    # 通用基本面
│   ├── SENTIMENT      # 情绪数据（Data-Core 数据加工层产出，含LLM打分+聚合）
│   └── MARKET_STATE   # 市场制度（Data-Core 数据加工层产出，market_regime）
│
├── 期货特异类型（FUTURES only）
│   ├── FUTURES_CONTRACT_CHAIN  # 合约链（多条合约的 OHLCV）
│   ├── FUTURES_TERM_STRUCTURE  # 期限结构（完整曲线）
│   ├── FUTURES_SPREAD          # 跨期价差
│   ├── FUTURES_BASIS           # 基差（现货-期货）
│   └── FUTURES_POSITION        # 持仓排名
│
├── ETF/REITs 特异类型
│   ├── ETF_NAV                 # 净值数据
│   ├── ETF_PREMIUM             # 折溢价率
│   └── ETF_FUND_FLOW           # 资金流
│
└── 可转债特异类型
    ├── CB_CONVERSION           # 转股数据（转股价/正股价）
    ├── CB_TERMS                # 转债条款（赎回/回售/下修）
    └── CB_PURE_BOND            # 纯债价值
```

---

## 4. 数据能力提升方案

### 4.1 新增 DataType 定义

```python
# datacore/models/enums.py

class DataType(str, Enum):
    """数据类型枚举 — 按数据结构特征和市场特异性划分。
    
    通用类型（无市场前缀）: 全市场通用
    市场特异类型（带市场前缀）: 特定市场专用
    v0.3.0 更新: SENTIMENT/MARKET_STATE 由 Data-Core 数据加工层产出（含LLM）
    """
    
    # ── 通用类型（全市场） ──
    OHLCV = "ohlcv"
    QUOTE = "quote"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    FUNDAMENTAL = "fundamental"
    MACRO = "macro"
    NEWS = "news"                         # Data-Core 采集+分类，携带 tags
    ANNOUNCEMENT = "announcement"
    SENTIMENT = "sentiment"               # v0.3.0: Data-Core 数据加工层产出（含LLM打分+聚合）
    MARKET_STATE = "market_state"         # v0.3.0: Data-Core 数据加工层产出（market_regime）
    
    # ── 期货特异类型 ──
    FUTURES_CONTRACT_CHAIN = "futures_contract_chain"   # 合约链数据
    FUTURES_TERM_STRUCTURE = "futures_term_structure"   # 期限结构
    FUTURES_SPREAD = "futures_spread"                   # 跨期价差
    FUTURES_BASIS = "futures_basis"                     # 基差
    FUTURES_POSITION = "futures_position"               # 持仓排名
    
    # ── ETF/REITs 特异类型 ──
    ETF_NAV = "etf_nav"                                 # 净值
    ETF_PREMIUM = "etf_premium"                         # 折溢价率
    ETF_FUND_FLOW = "etf_fund_flow"                     # 资金流
    
    # ── 可转债特异类型 ──
    CB_CONVERSION = "cb_conversion"                     # 转股数据
    CB_TERMS = "cb_terms"                               # 转债条款
    CB_PURE_BOND = "cb_pure_bond"                       # 纯债价值
```

### 4.2 期货模块能力扩展

#### 4.2.1 期限结构与合约链

```python
# datacore/futures/futures_provider.py

class FuturesDataProvider:
    def get(self, symbol, data_type, params=None):
        if data_type == DataType.FUTURES_CONTRACT_CHAIN:
            return self._get_contract_chain(symbol, params)
        elif data_type == DataType.FUTURES_TERM_STRUCTURE:
            return self._get_term_structure(symbol)
        elif data_type == DataType.FUTURES_SPREAD:
            return self._get_spread(symbol, params)
        elif data_type == DataType.FUTURES_BASIS:
            return self._get_basis(symbol)
        elif data_type == DataType.FUTURES_POSITION:
            return self._get_position_rank(symbol)
        # ... 现有 OHLCV/QUOTE 逻辑
    
    def _get_contract_chain(self, symbol, params):
        """获取合约链数据。
        
        Args:
            symbol: 品种代码（如 "RB"）
            params: {"num_contracts": 5, "period": "daily"}
        
        Returns:
            DataPayload: data=dict[contract_code, KlineData]
        """
    
    def _get_term_structure(self, symbol):
        """获取期限结构快照。
        
        Returns:
            DataPayload: data=dict[contract_month, dict["price", "yield"]]
        """
    
    def _get_spread(self, symbol, params):
        """获取跨期价差。
        
        Args:
            params: {"near_month": "RB2510", "far_month": "RB2601"}
        
        Returns:
            DataPayload: data=DataFrame 包含价差时间序列
        """
```

#### 4.2.2 基差数据获取

```python
class EastMoneyFuturesProvider(FuturesDataSource):
    def fetch_basis(self, symbol):
        """从东方财富/生意社获取基差数据。"""
        # 生意社 API: https://www.100ppi.com/
        # 我的钢铁网: https://www.mysteel.com/
```

#### 4.2.3 仓单与持仓数据获取

```python
class ExchangeApiProvider(FuturesDataSource):
    """交易所官网数据源 — 获取仓单、持仓排名等官方数据。"""
    
    def fetch_warehouse_receipts(self, symbol):
        """获取仓单数据。"""
    
    def fetch_position_rank(self, symbol):
        """获取持仓排名数据。"""
```

### 4.3 新闻资讯模块（v0.2.0 新增）

```python
# datacore/news/
#   __init__.py
#   news_provider.py           # 新闻资讯统一入口
#   classifier.py              # 新闻分类器（数据加工层）
#   providers/
#     cls.py                   # 财联社快讯
#     wallstreet_cn.py         # 华尔街见闻
#     eastmoney_research.py    # 东方财富研报
#     exchange_announcement.py # 交易所公告
#     social.py                # 雪球/微博

class NewsDataProvider:
    def get(self, symbol=None, params=None):
        """获取新闻资讯（已分类，携带 tags）。
        
        Args:
            symbol: 品种代码（如 "RB"），None 表示全市场
            params: {"days": 7, "categories": ["macro", "industry"]}
        
        Returns:
            DataPayload: data=list[dict], 每条新闻含:
                - title, content, published_at
                - tags: ["宏观", "产业", "公司", "政策"]
                - related_symbols: ["RB", "HC"]
        """

class NewsClassifier:
    """新闻分类器 — Data-Core 数据加工层。
    
    给 NEWS 打分类标签（宏观/产业/公司/政策），
    属数据加工，不是因子计算。
    """
    
    def classify(self, news_text: str) -> list[str]:
        """返回分类标签列表。"""
```

### 4.4 宏观数据模块

```python
# datacore/macro/
#   __init__.py
#   macro_provider.py        # 宏观数据统一入口
#   providers/
#     national_bureau.py     # 国家统计局（CPI/PPI/GDP）
#     pboc.py               # 央行（LPR/M2）
#     eastmoney_macro.py    # 东方财富（综合宏观）

class MacroDataProvider:
    def get(self, indicator=None, params=None):
        """获取宏观数据。
        
        Args:
            indicator: "pmi", "lpr", "cpi", "ppi", "gdp", "m2", "none"(全部)
        """
```

### 4.5 数据加工层（v0.3.0 新增）

> **核心原则**: Data-Core 数据加工层负责从"原始/半结构化数据"到"可直接消费的结构化数据"的转换。
> LLM 是数据加工的工具之一，与规则引擎、统计方法地位相同。
> FTS 的职责是因子演化（发现、评估、组合因子）和策略生成。

```python
# datacore/processing/                 # 数据加工层
#   __init__.py
#   base.py                             # ProcessingStage 抽象基类
#   sentiment/                          # 情绪加工管线
#     __init__.py
#     sentiment_llm.py                  # LLM 情绪打分（Data-Core 数据加工层）
#     sentiment_rule.py                 # 规则情绪基线（词典法，零成本模式）
#     sentiment_aggregator.py           # 情绪聚合器（按品种/时间聚合）
#   market_regime.py                    # 市场制度检测（bull/bear/sideways）
#   fundamental/
#     __init__.py
#     fundamental_llm.py                # 基本面LLM加工（研报摘要）

class SentimentLLMStage:
    """LLM 情绪打分 — Data-Core 数据加工层。
    
    输入: NEWS（Data-Core 已采集+分类）
    输出: 单条新闻的情绪分数（-1 ~ +1）+ 置信度
    这是数据加工，不是因子计算。FTS 直接消费 SENTIMENT 数据。
    """
    input_type = "NEWS"
    output_type = "SENTIMENT_ITEM"
    
    def process(self, input_data, symbol=None):
        # 调用 LLM 对新闻进行情绪打分
        pass

class SentimentRuleStage:
    """规则情绪基线 — 零成本模式（无 LLM 调用时的兜底）。
    
    输入: NEWS
    输出: 单条新闻的情绪分数（基于词典法）
    """
    input_type = "NEWS"
    output_type = "SENTIMENT_ITEM"
    
    def process(self, input_data, symbol=None):
        # 基于情感词典打分
        pass

class SentimentAggregator:
    """情绪聚合器 — 按品种/时间维度聚合情绪分数。
    
    输入: list[SENTIMENT_ITEM]
    输出: SENTIMENT（symbol → {date → {score, volume, topics}}）
    """
    
    def aggregate(self, items, symbol=None, params=None):
        # 加权聚合 + 时间衰减
        pass

class MarketRegimeDetector:
    """市场制度检测 — 识别当前市场处于 bull/bear/sideways。
    
    输入: OHLCV（指数/主力合约）
    output: MARKET_STATE（regime, confidence, regime_features）
    """
    
    def detect(self, ohlcv_data, params=None):
        # 基于趋势、波动率、成交量等综合判断
        pass
```

---

## 5. 实施路线图

### Phase 1 — 期货基础能力增强（v0.1.1）

| 任务 | 内容 | 工时 | 优先级 |
|:-----|:-----|:-----|:-------|
| T1.1 | 新增 DataType 枚举（期货特异类型） | 0.5d | P0 |
| T1.2 | 实现合约链获取（基于 TdxLc 多合约） | 1d | P0 |
| T1.3 | 实现期限结构计算（基于合约链） | 0.5d | P0 |
| T1.4 | 实现跨期价差计算 | 0.5d | P0 |
| T1.5 | 实现技术指标获取（TdxLc API） | 1d | P1 |

### Phase 2 — 期货基本面数据（v0.1.2）

| 任务 | 内容 | 工时 | 优先级 |
|:-----|:-----|:-----|:-------|
| T2.1 | 实现基差数据获取（生意社/东方财富） | 1d | P0 |
| T2.2 | 实现仓单数据获取（交易所官网） | 1d | P1 |
| T2.3 | 实现持仓排名获取（交易所官网） | 0.5d | P1 |
| T2.4 | 实现库存数据获取（生意社） | 0.5d | P1 |

### Phase 3 — 新闻资讯模块（v0.1.3）

| 任务 | 内容 | 工时 | 优先级 |
|:-----|:-----|:-----|:-------|
| T3.1 | 创建 news/ 模块 | 0.5d | P1 |
| T3.2 | 实现财联社快讯采集 | 1d | P1 |
| T3.3 | 实现华尔街见闻采集 | 0.5d | P1 |
| T3.4 | 实现东方财富研报采集 | 0.5d | P1 |
| T3.5 | 实现交易所公告采集 | 0.5d | P1 |
| T3.6 | 实现新闻分类器（宏观/产业/公司/政策） | 1d | P1 |

### Phase 4 — 宏观数据模块（v0.1.4）

| 任务 | 内容 | 工时 | 优先级 |
|:-----|:-----|:-----|:-------|
| T4.1 | 创建 macro/ 模块 | 0.5d | P1 |
| T4.2 | 实现国家统计局数据源 | 1d | P1 |
| T4.3 | 实现央行数据源 | 0.5d | P1 |
| T4.4 | 实现东方财富宏观数据源 | 0.5d | P1 |

### Phase 5 — ETF/可转债增强（v0.2.0）

| 任务 | 内容 | 工时 | 优先级 |
|:-----|:-----|:-----|:-------|
| T5.1 | 实现 ETF 净值获取 | 1d | P2 |
| T5.2 | 实现 ETF 折溢价计算 | 0.5d | P2 |
| T5.3 | 实现可转债转股数据 | 1d | P2 |

### Phase 6 — 数据加工层：情绪与市场制度（v0.3.0 新增）

| 任务 | 内容 | 工时 | 优先级 |
|:-----|:-----|:-----|:-------|
| T6.1 | 创建 processing/ 模块（base + 管线框架） | 0.5d | P1 |
| T6.2 | 实现 LLM 情绪打分（sentiment_llm.py） | 1d | P1 |
| T6.3 | 实现规则情绪基线（sentiment_rule.py，零成本模式） | 0.5d | P1 |
| T6.4 | 实现情绪聚合器（sentiment_aggregator.py） | 0.5d | P1 |
| T6.5 | 实现市场制度检测（market_regime.py） | 1d | P1 |
| T6.6 | SENTIMENT DataType 接入 UnifiedDataProvider | 0.5d | P1 |
| T6.7 | MARKET_STATE DataType 接入 UnifiedDataProvider | 0.5d | P1 |

### Phase 7 — 基本面LLM加工（v0.3.1 远期）

| 任务 | 内容 | 工时 | 优先级 |
|:-----|:-----|:-----|:-------|
| T7.1 | 研报结构化摘要（LLM） | 1d | P2 |
| T7.2 | 财报关键信息抽取（LLM） | 1d | P2 |

---

## 6. 数据源扩展

### 6.1 新增数据源列表

| 数据源 | 数据类型 | 优先级 | 说明 |
|:-------|:---------|:-------|:-----|
| **上期所官网** | 仓单/持仓排名 | P1 | http://www.shfe.com.cn/ |
| **郑商所官网** | 仓单/持仓排名 | P1 | http://www.czce.com.cn/ |
| **大商所官网** | 仓单/持仓排名 | P1 | http://www.dce.com.cn/ |
| **生意社** | 现货价格/基差/库存 | P0 | https://www.100ppi.com/ |
| **我的钢铁网** | 黑色系库存/产量 | P1 | https://www.mysteel.com/ |
| **财联社** | 快讯新闻 | P1 | https://www.cls.cn/ |
| **华尔街见闻** | 综合财经新闻 | P1 | https://wallstreetcn.com/ |
| **东方财富研报** | 研究报告 | P1 | https://data.eastmoney.com/ |
| **交易所公告** | 交易所公告 | P1 | 各交易所官网 |
| **雪球/微博** | 社交舆情 | P2 | 平台 API |
| **国家统计局** | CPI/PPI/GDP | P1 | http://www.stats.gov.cn/ |
| **央行** | LPR/M2/货币政策 | P1 | http://www.pbc.gov.cn/ |
| **Wind（可选）** | 全量数据 | P3 | 需要付费 API |

### 6.2 数据源降级链设计

```
期货基本面数据降级链:
├── P0: 交易所官网（仓单/持仓）
├── P1: 生意社/我的钢铁网（现货/库存）
└── P2: 东方财富综合（兜底）

新闻资讯降级链:
├── P0: 财联社（快讯，最及时）
├── P1: 华尔街见闻（综合财经）
├── P2: 东方财富研报（深度分析）
└── P3: 交易所公告（官方公告）

宏观数据降级链:
├── P0: 国家统计局/央行（官方）
├── P1: 东方财富（汇总）
└── P2: Cached（缓存数据）

情绪数据降级链（v0.3.0 新增）:
├── P0: LLM 情绪打分（高质量）
├── P1: 规则基线（零成本，兜底）
└── P2: Cached（缓存情绪数据）
```

---

## 7. 与 FTS 的接口契约

### 7.1 FTS 数据消费方式

```python
# FTS 因子引擎消费 Data-Core 数据
from datacore import UnifiedDataProvider
from datacore.models.enums import DataType

provider = UnifiedDataProvider()

# 获取期货合约链
chain = provider.get("RB", DataType.FUTURES_CONTRACT_CHAIN, {"num_contracts": 5})

# 获取基差
basis = provider.get("RB", DataType.FUTURES_BASIS)

# 获取期限结构
term_structure = provider.get("RB", DataType.FUTURES_TERM_STRUCTURE)

# 获取新闻（已分类，携带 tags）— Data-Core 数据采集层产出
news = provider.get("RB", DataType.NEWS, {"days": 7})
# news.data = [{"title": "...", "content": "...", "tags": ["宏观", "产业"], ...}]

# 获取情绪数据（已打分+聚合）— Data-Core 数据加工层产出（v0.3.0）
sentiment = provider.get("RB", DataType.SENTIMENT, {"days": 30})
# sentiment.data = {"2026-07-18": {"score": 0.35, "volume": 12, "topics": ["宏观", "黑色"]}, ...}

# 获取市场制度 — Data-Core 数据加工层产出（v0.3.0）
market_state = provider.get("RB", DataType.MARKET_STATE)
# market_state.data = {"regime": "bull", "confidence": 0.72, "features": {...}}

# 获取宏观数据
pmi = provider.get("*", DataType.MACRO, {"indicator": "pmi"})
```

### 7.2 因子声明数据依赖

```python
# FTS 因子声明依赖的 DataType
FACTOR_REGISTRY = {
    "term_structure_slope": {
        "markets": [MarketType.FUTURES],
        "data_types": [DataType.FUTURES_TERM_STRUCTURE],
    },
    "basis_momentum": {
        "markets": [MarketType.FUTURES],
        "data_types": [DataType.FUTURES_BASIS],
    },
    "spread_mean_reversion": {
        "markets": [MarketType.FUTURES],
        "data_types": [DataType.FUTURES_SPREAD],
    },
    # 情绪因子：直接消费 Data-Core 的 SENTIMENT（v0.3.0 更新）
    "news_sentiment": {
        "markets": "*",
        "data_types": [DataType.SENTIMENT],  # Data-Core 数据加工层产出
        # 注: 情绪的 LLM 打分和聚合全部在 Data-Core 完成，FTS 直接消费
    },
    # 市场制度因子：直接消费 Data-Core 的 MARKET_STATE
    "regime_aware_momentum": {
        "markets": "*",
        "data_types": [DataType.MARKET_STATE, DataType.OHLCV],
    },
}
```

### 7.3 数据质量约定

| SourceGrade | 说明 | FTS 使用策略 |
|:------------|:-----|:-------------|
| PRIMARY | 交易所官网/官方数据源 | 可用于交易决策 |
| DAILY | 生意社/东方财富等第三方 | 可用于因子计算 |
| CACHED | 缓存数据 | 可用于分析，需标注 |
| STALE | 过期数据（>7天） | 低权重使用或跳过 |
| UNAVAILABLE | 所有源不可用 | 因子降级或跳过 |

### 7.4 数据加工层接口契约（v0.3.0 新增）

```python
# Data-Core 数据加工层的对外接口（FTS 调用视角）

class UnifiedDataProvider:
    def get_sentiment(self, symbol: str, params: dict = None) -> DataPayload:
        """获取情绪数据（已打分+聚合）。
        
        注意: FTS 不需要关心情绪是 LLM 打分还是规则打分，
        只需要消费最终的 SENTIMENT 数据。
        LLM 是 Data-Core 数据加工层内部的实现细节。
        """
    
    def get_market_state(self, symbol: str, params: dict = None) -> DataPayload:
        """获取市场制度状态。"""
```

---

## 8. 核心边界原则（v0.3.0 新增）

### 8.1 三项目生态关系

```
Data-Core（数据基础设施）
    ↑
    │ 数据接口: UnifiedDataProvider.get(symbol, DataType, params)
    │ 数据契约: DataType 枚举 + DataPayload + SourceGrade
    │
FTS（因子智能系统）
    ↑
    │ 信号接口: SignalPayload + FactorCombo
    │
FDT（期货交易决策系统）
```

### 8.2 职责边界划分

| 能力 | Data-Core | FTS | FDT |
|:-----|:---------:|:---:|:---:|
| **数据采集**（K线/新闻/财报/宏观） | ✅ | ❌ | ❌ |
| **数据加工**（分类/结构化抽取/情绪LLM/规则基线/情绪聚合/market_regime） | ✅ 数据加工层（含LLM） | ❌ | ❌ |
| **数据加工**（基本面LLM摘要/研报结构化） | ✅ 数据加工层（含LLM） | ❌ | ❌ |
| **因子发现与演化**（L1/L2/L3 三层循环） | ❌ | ✅ | ❌ |
| **因子程序表示**（图灵完备代码+安全沙箱） | ❌ | ✅ | ❌ |
| **因子评估**（三级评估链+多重检验） | ❌ | ✅ | ❌ |
| **多因子策略**（加权/正交化/组合） | ❌ | ✅ | ❌ |
| **新闻情绪管线**（采集→分类→打分→聚合） | ✅ 全链路（数据加工层） | ❌ 消费SENTIMENT | ❌ |
| **辩论系统**（9-Agent 辩论+质量门禁） | ❌ | ❌ | ✅ |
| **交易决策**（LangGraph 编排+风控+信号输出） | ❌ | ❌ | ✅ |
| **CTP 交易执行** | ❌ | ❌ | ✅ |

### 8.3 边界原则总结

1. **能力导向，而非技术手段导向**：LLM 是 AI 原生项目的基本工具，不构成独立模块的边界。Data-Core 可以用 LLM 做数据加工，FTS 可以用 LLM 做因子演化，FDT 可以用 LLM 做辩论决策。边界按"能力与职责"划分。

2. **数据归 Data-Core，因子归 FTS，决策归 FDT**：
   - Data-Core = 数据基础设施（采集 + 加工 + 存储 + 服务）
   - FTS = 因子智能（发现 + 评估 + 组合 + 演化）
   - FDT = 交易决策（辩论 + 风控 + 信号 + 执行）

3. **上下游依赖关系不可逆转**：Data-Core ← FTS ← FDT，下游可以依赖上游，上游不能依赖下游。

4. **接口契约优先**：三项目之间通过明确的接口（DataType、DataPayload、SignalPayload）交互，内部实现互不干扰。

5. **独立可运行**：每个项目都可以独立运行，有自己的 CLI、配置、测试、文档。

---

## 附录：版本历史

| 版本 | 日期 | 变更说明 |
|:-----|:-----|:---------|
| v0.3.0 | 2026-07-18 | 数据加工层扩展：情绪管线（LLM+规则+聚合）、market_regime 检测从 FTS 迁移到 Data-Core；新增 SENTIMENT/MARKET_STATE DataType；新增核心边界原则章节；明确 LLM 是 AI 原生项目基本能力，边界基于能力与职责划分 |
| v0.2.0 | 2026-07-18 | 规划文档：期货基本面/技术指标/期限结构能力提升；新增新闻资讯模块（采集+分类）；明确项目边界（Data-Core 数据采集加工，FTS 因子计算） |
| v0.1.0 | 2026-07-18 | Initial AI-Native Quant Data Infrastructure |
