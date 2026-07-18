# Data-Core Testing

Version: v0.3.1 | Updated: 2026-07-18

## Test Files

| 测试文件 | 用例数 | 覆盖模块 |
|:---------|:-------|:---------|
| `tests/test_models.py` | 7 | 枚举/Payload/OHLCV 模型 |
| `tests/test_registry.py` | 5 | SymbolRegistry 品种注册表 |
| `tests/test_store.py` | 5 | MemoryCache 内存缓存 |
| `tests/test_futures_mock.py` | 11 | 期货数据源 mock 测试 |
| `tests/test_futures_models.py` | 18 | 期货数据模型 |
| `tests/test_equity_mock.py` | 4 | 股票数据源 mock 测试 |
| `tests/test_api.py` | 4 | UnifiedDataProvider 路由测试 |
| `tests/test_news.py` | 11 | 新闻分类器 + 新闻模型 |
| `tests/test_macro.py` | 3 | 宏观数据模型 |
| `tests/test_processing.py` | 36 | 数据加工层（情绪管线 + 市场制度） |

**总计: 10 个测试文件，104 个测试用例**

## v0.3.0 新增测试

| 测试类 | 用例数 | 说明 |
|:-------|:-------|:-----|
| TestSentimentModels | 5 | SentimentItem/SentimentData/MarketStateData 模型 |
| TestSentimentRuleStage | 8 | 规则情绪基线（正面/负面/中性/否定词/自定义） |
| TestSentimentLLMStage | 3 | LLM 降级测试（无API Key/降级/禁用降级） |
| TestSentimentAggregator | 5 | 聚合器（空/基本/时间衰减/置信度过滤/按日） |
| TestMarketRegimeDetector | 7 | 市场制度（数据不足/牛/熊/横盘/特征/品种传递） |
| TestProcessingStageContract | 4 | 接口契约（继承/输入输出类型/优先级） |
| TestNewDataTypes | 4 | SENTIMENT/MARKET_STATE 枚举验证 |

## Run Tests

```bash
cd d:\Programs\data-core
python -m pytest tests/ -v
```

## 测试覆盖原则

1. **模型测试**: 所有数据模型必须有完整的字段验证测试
2. **降级测试**: LLM→规则降级、数据源降级链必须有测试
3. **边界测试**: 空输入、数据不足、异常输入必须有对应用例
4. **契约测试**: ProcessingStage 接口契约必须验证
5. **市场场景测试**: 牛市/熊市/横盘三种 regime 必须覆盖
6. **Mock 测试**: 外部数据源（HTTP/Socket）必须通过 mock 测试覆盖所有异常路径
7. **覆盖率目标**: 整体 ≥ 95%，核心模块（models/processing/api）≥ 100%
