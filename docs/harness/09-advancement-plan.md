# Data-Core Advancement Plan

Version: v0.3.0 | Updated: 2026-07-18

## Milestones

| 里程碑 | 版本 | 日期 | 状态 | 说明 |
|:-------|:-----|:-----|:-----|:-----|
| **M1** | **v0.1.0** | **2026-07-18** | ✅ **COMPLETED** | 基础可用版 |
| **M2** | **v0.2.0** | **2026-07-18** | ✅ **COMPLETED** | 能力增强版（期货深度+新闻+宏观） |
| **M3** | **v0.3.0** | **2026-07-18** | ✅ **COMPLETED** | 数据加工层（情绪管线+市场制度） |
| M4 | v0.4.0 | TBD | PLANNED | 工程完善版（健康检查+熔断+指标+ETF/CB） |
| M5 | v1.0.0 | TBD | PLANNED | 生产就绪版（DuckDB+调度器+监控） |

## M3 (v0.3.0) 交付清单 ✅

### 数据加工层
- ✅ `processing/` 模块（7个文件）
- ✅ ProcessingStage 抽象基类（统一接口契约）
- ✅ SentimentItem / SentimentData / MarketStateData 数据模型
- ✅ MarketRegime 枚举（bull/bear/sideways/unknown）

### 情绪加工管线
- ✅ SentimentRuleStage — 规则情绪基线（词典法，零成本）
  - 中文金融情感词典（正面/负面词各30+）
  - 程度副词权重调整
  - 否定词反转处理
- ✅ SentimentLLMStage — LLM 情绪打分骨架
  - OpenAI SDK 集成
  - 自动降级到规则基线
  - 环境变量配置（DATACORE_LLM_API_KEY）
- ✅ SentimentAggregator — 情绪聚合器
  - 时间衰减加权（半衰期可配）
  - 置信度加权
  - 按日聚合 + 整体摘要

### 市场制度检测
- ✅ MarketRegimeDetector — 基于 OHLCV 的 regime 检测
  - 趋势强度（MA 斜率 + 价格偏离度）
  - 波动率（年化标准差）
  - 成交量趋势
  - 综合打分判断 bull/bear/sideways

### 统一 API 接入
- ✅ SENTIMENT 路由（NEWS → 打分 → 聚合）
- ✅ MARKET_STATE 路由（OHLCV → 检测）
- ✅ NEWS 路由
- ✅ MACRO 路由

### 测试
- ✅ 36 个新增测试用例（总计 104 个）
- ✅ 覆盖：模型/规则打分/LLM降级/聚合/regime检测/契约

## M4 (v0.4.0) 规划

### 工程化增强（P1）
- [ ] 健康检查接口（get_health()）
- [ ] ETF/CB/REIT 市场代码支持完善
- [ ] LLM 情绪打分实际接入测试

### 可靠性增强（P2）
- [ ] 带状态的熔断器
- [ ] 指标收集框架

### 数据源完善（P2）
- [ ] 国信 HTTP 数据源正式接入
- [ ] 新闻数据源实际 HTTP 抓取
- [ ] 期货基本面数据实际抓取

## 晋级标准

### M2 → M3 晋级标准 ✅
- [x] SENTIMENT/MARKET_STATE DataType 定义
- [x] 情绪加工管线可用（规则基线+LLM骨架）
- [x] 市场制度检测可用
- [x] 接入 UnifiedDataProvider
- [x] 测试用例覆盖新增功能

### M3 → M4 晋级标准
- [ ] 健康检查接口可用
- [ ] 熔断器实现并测试
- [ ] 指标收集框架就绪
- [ ] ETF/CB 基础功能可用
- [ ] 所有 P1 差距关闭
