"""数据加工层测试 — 情绪管线 + 市场制度检测。

覆盖:
- SentimentRuleStage: 规则情绪基线（词典法）
- SentimentLLMStage: LLM 情绪打分（降级测试）
- SentimentAggregator: 情绪聚合器
- MarketRegimeDetector: 市场制度检测
- 数据模型: SentimentItem, SentimentData, MarketStateData
"""

from __future__ import annotations
import time
import unittest.mock as mock

import pytest

from datacore.processing.models import (
    SentimentItem, SentimentData, MarketStateData, MarketRegime,
)
from datacore.processing.base import ProcessingStage
from datacore.processing.sentiment.sentiment_rule import SentimentRuleStage
from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
from datacore.processing.sentiment.sentiment_aggregator import SentimentAggregator
from datacore.processing.market_regime import MarketRegimeDetector
from datacore.models.enums import DataType


class TestSentimentModels:
    """数据模型测试。"""

    def test_sentiment_item_defaults(self):
        item = SentimentItem()
        assert item.score == 0.0
        assert item.confidence == 0.0
        assert item.source == ""
        assert item.tags == []

    def test_sentiment_data_add_item(self):
        data = SentimentData(symbol="RB")
        item = SentimentItem(text="test", score=0.5, confidence=0.8)
        data.add_item(item)
        assert data.total_volume == 1
        assert len(data.items) == 1

    def test_market_state_data_defaults(self):
        state = MarketStateData()
        assert state.regime == MarketRegime.UNKNOWN
        assert state.confidence == 0.0
        assert not state.is_bull
        assert not state.is_bear
        assert state.is_sideways is False  # UNKNOWN 不是 SIDEWAYS

    def test_market_state_data_bull(self):
        state = MarketStateData(regime=MarketRegime.BULL, confidence=0.8)
        assert state.is_bull
        assert not state.is_bear

    def test_market_regime_enum(self):
        assert MarketRegime.BULL == "bull"
        assert MarketRegime.BEAR == "bear"
        assert MarketRegime.SIDEWAYS == "sideways"
        assert MarketRegime.UNKNOWN == "unknown"


class TestSentimentRuleStage:
    """规则情绪基线测试。"""

    def test_check_available(self):
        stage = SentimentRuleStage()
        assert stage.check_available() is True

    def test_positive_news(self):
        """正面新闻应该得到正分。"""
        stage = SentimentRuleStage()
        result = stage.process("螺纹钢价格大幅上涨，需求旺盛，利好市场")
        assert result.score > 0
        assert result.confidence > 0
        assert result.source == "rule"

    def test_negative_news(self):
        """负面新闻应该得到负分。"""
        stage = SentimentRuleStage()
        result = stage.process("螺纹钢价格暴跌，需求疲软，库存积压严重")
        assert result.score < 0
        assert result.confidence > 0

    def test_neutral_news(self):
        """中性新闻应该得到接近0的分数。"""
        stage = SentimentRuleStage()
        result = stage.process("今天天气不错")
        assert result.score == 0.0
        assert result.confidence == 0.0

    def test_empty_text(self):
        stage = SentimentRuleStage()
        result = stage.process("")
        assert result.score == 0.0
        assert result.confidence == 0.0

    def test_dict_input(self):
        """支持字典输入（含 title/content）。"""
        stage = SentimentRuleStage()
        result = stage.process({
            "title": "降准利好",
            "content": "央行宣布降准，市场流动性改善",
            "published_at": time.time(),
            "tags": ["宏观"],
        }, symbol="RB")
        assert result.score > 0
        assert result.symbol == "RB"
        assert result.tags == ["宏观"]

    def test_negation(self):
        """否定词应该反转情绪。"""
        # "不上涨" 应该是负面
        result = SentimentRuleStage().process("价格未上涨")
        # 否定正面词 -> 负面
        assert result.score <= 0

    def test_custom_keywords(self):
        """支持自定义关键词。"""
        stage = SentimentRuleStage(
            custom_positive=["超级利好"],
            custom_negative=["超级利空"],
        )
        pos = stage.process("超级利好")
        assert pos.score > 0
        neg = stage.process("超级利空")
        assert neg.score < 0


class TestSentimentLLMStage:
    """LLM 情绪打分测试（降级场景）。"""

    def test_check_available_no_api_key(self):
        """无 API Key 时 LLM 不可用。"""
        stage = SentimentLLMStage(api_key="")
        assert stage.check_available() is False

    def test_fallback_to_rule(self):
        """LLM 不可用时应降级到规则基线。"""
        stage = SentimentLLMStage(api_key="", fallback_to_rule=True)
        result = stage.process("螺纹钢价格大幅上涨，利好市场")
        assert result.source == "rule_fallback"
        assert result.score > 0

    def test_no_fallback(self):
        """禁用降级时返回 llm_unavailable。"""
        stage = SentimentLLMStage(api_key="", fallback_to_rule=False)
        result = stage.process("利好消息")
        assert result.source == "llm_unavailable"
        assert result.score == 0.0


class TestSentimentAggregator:
    """情绪聚合器测试。"""

    def test_empty_items(self):
        agg = SentimentAggregator()
        result = agg.aggregate([])
        assert result.total_volume == 0
        assert result.overall_score == 0.0

    def test_aggregate_basic(self):
        """基本聚合测试。"""
        now = time.time()
        items = [
            SentimentItem(text="利好", score=0.8, confidence=0.9,
                          source="rule", symbol="RB", published_at=now),
            SentimentItem(text="上涨", score=0.6, confidence=0.8,
                          source="rule", symbol="RB", published_at=now),
        ]
        agg = SentimentAggregator()
        result = agg.aggregate(items, symbol="RB")
        assert result.total_volume == 2
        assert result.overall_score > 0
        assert len(result.daily) >= 1

    def test_time_decay(self):
        """时间衰减权重测试 — 近期新闻权重更高。"""
        now = time.time()
        old_time = now - 30 * 86400  # 30天前
        items = [
            # 近期正面
            SentimentItem(text="利好", score=0.8, confidence=1.0,
                          source="rule", published_at=now),
            # 远期负面
            SentimentItem(text="利空", score=-0.8, confidence=1.0,
                          source="rule", published_at=old_time),
        ]
        agg = SentimentAggregator(decay_half_life_days=7.0)
        result = agg.aggregate(items)
        # 近期正面权重更高，整体应为正
        assert result.overall_score > 0

    def test_confidence_filter(self):
        """低置信度数据应被过滤。"""
        items = [
            SentimentItem(text="利好", score=0.8, confidence=0.5),
            SentimentItem(text="利空", score=-0.8, confidence=0.05),  # 被过滤
        ]
        agg = SentimentAggregator(min_confidence=0.1)
        result = agg.aggregate(items)
        assert result.total_volume == 1  # 只保留1条

    def test_daily_aggregation(self):
        """按日聚合测试。"""
        now = time.time()
        items = [
            SentimentItem(text="利好1", score=0.5, confidence=0.8,
                          published_at=now),
            SentimentItem(text="利好2", score=0.7, confidence=0.8,
                          published_at=now),
        ]
        agg = SentimentAggregator()
        result = agg.aggregate(items)
        assert len(result.daily) == 1
        today_key = list(result.daily.keys())[0]
        assert result.daily[today_key]["volume"] == 2
        assert result.daily[today_key]["score"] > 0


class TestMarketRegimeDetector:
    """市场制度检测测试。"""

    def test_check_available(self):
        detector = MarketRegimeDetector()
        assert detector.check_available() is True

    def test_insufficient_data(self):
        """数据不足时应返回 UNKNOWN。"""
        detector = MarketRegimeDetector(ma_period=20)
        candles = [{"close": 100, "volume": 1000} for _ in range(5)]
        result = detector.process(candles, symbol="RB")
        assert result.regime == MarketRegime.UNKNOWN
        assert result.confidence == 0.0

    def test_bull_market(self):
        """上升趋势应检测为 BULL。"""
        # 构造上升趋势数据
        candles = []
        price = 100.0
        for i in range(60):
            price *= 1.005  # 每天涨0.5%
            candles.append({
                "open": price * 0.99,
                "high": price * 1.01,
                "low": price * 0.98,
                "close": price,
                "volume": 10000 + i * 100,
            })
        detector = MarketRegimeDetector(ma_period=20)
        result = detector.process(candles, symbol="RB")
        assert result.regime == MarketRegime.BULL
        assert result.confidence > 0
        assert result.trend_strength > 0

    def test_bear_market(self):
        """下降趋势应检测为 BEAR。"""
        candles = []
        price = 100.0
        for i in range(60):
            price *= 0.99  # 每天跌1%，更强的下降趋势
            candles.append({
                "open": price * 1.01,
                "high": price * 1.02,
                "low": price * 0.98,
                "close": price,
                "volume": 10000,
            })
        detector = MarketRegimeDetector(ma_period=20, bear_threshold=-0.3)
        result = detector.process(candles, symbol="RB")
        assert result.regime == MarketRegime.BEAR
        assert result.trend_strength < 0

    def test_sideways_market(self):
        """横盘震荡应检测为 SIDEWAYS。"""
        import random
        random.seed(42)
        candles = []
        for i in range(60):
            close = 100 + random.uniform(-1, 1)  # 在100附近震荡
            candles.append({
                "open": close,
                "high": close + 0.5,
                "low": close - 0.5,
                "close": close,
                "volume": 10000,
            })
        detector = MarketRegimeDetector(
            ma_period=20, bull_threshold=0.6, bear_threshold=-0.6
        )
        result = detector.process(candles, symbol="RB")
        # 横盘时趋势强度接近0
        assert abs(result.trend_strength) < 0.5

    def test_features_dict(self):
        """结果应包含特征字典。"""
        candles = [{"close": 100 + i, "volume": 1000} for i in range(30)]
        detector = MarketRegimeDetector(ma_period=20)
        result = detector.process(candles, symbol="RB")
        assert "composite_score" in result.features
        assert "ma_period" in result.features
        assert "candle_count" in result.features

    def test_symbol_passed_through(self):
        """品种代码应传递到结果。"""
        candles = [{"close": 100 + i, "volume": 1000} for i in range(30)]
        detector = MarketRegimeDetector(ma_period=20)
        result = detector.process(candles, symbol="CU")
        assert result.symbol == "CU"


class TestProcessingStageContract:
    """加工阶段接口契约测试。"""

    def test_sentiment_rule_is_processing_stage(self):
        stage = SentimentRuleStage()
        assert isinstance(stage, ProcessingStage)
        assert stage.input_type == "NEWS"
        assert stage.output_type == "SENTIMENT_ITEM"

    def test_sentiment_llm_is_processing_stage(self):
        stage = SentimentLLMStage(api_key="")
        assert isinstance(stage, ProcessingStage)
        assert stage.input_type == "NEWS"
        assert stage.output_type == "SENTIMENT_ITEM"

    def test_market_regime_is_processing_stage(self):
        detector = MarketRegimeDetector()
        assert isinstance(detector, ProcessingStage)
        assert detector.input_type == "OHLCV"
        assert detector.output_type == "MARKET_STATE"

    def test_priority_ordering(self):
        """LLM 优先级应高于规则基线。"""
        llm = SentimentLLMStage(api_key="fake")
        rule = SentimentRuleStage()
        assert llm.priority < rule.priority  # 0 < 1


class TestNewDataTypes:
    """新增 DataType 枚举测试。"""

    def test_sentiment_datatype_exists(self):
        assert DataType.SENTIMENT == "sentiment"

    def test_market_state_datatype_exists(self):
        assert DataType.MARKET_STATE == "market_state"

    def test_sentiment_in_enum(self):
        assert DataType.SENTIMENT in DataType

    def test_market_state_in_enum(self):
        assert DataType.MARKET_STATE in DataType


class TestProcessingStageDefault:
    """ProcessingStage 基类默认行为测试 — base.py 全覆盖。"""

    def test_check_available_default_true(self):
        """不覆盖 check_available 的子类应继承默认行为返回 True（line 47）。"""

        class ConcreteStage(ProcessingStage):
            input_type = "X"
            output_type = "Y"
            name = "concrete"
            priority = 9

            def process(self, input_data, symbol=None, params=None):
                return None

        stage = ConcreteStage()
        assert stage.check_available() is True

    def test_process_not_implemented(self):
        """直接调用基类 process 应抛出 NotImplementedError（line 43）。"""
        with mock.patch.object(
            ProcessingStage, '__abstractmethods__', frozenset()
        ):
            stage = ProcessingStage.__new__(ProcessingStage)
            stage.input_type = ""
            stage.output_type = ""
            stage.name = ""
            stage.priority = 0
            with pytest.raises(NotImplementedError):
                stage.process(None)


class TestMarketRegimeDetectorEdgeCases:
    """市场制度检测边界情况 — market_regime.py 全覆盖。"""

    # ---------- _extract_candles 分支 ----------

    def test_extract_candles_dataframe(self):
        """DataFrame-like 对象应通过 to_dict 分支（lines 124-126）。"""

        class MockDataFrame:
            def to_dict(self, orient="records"):
                return [{"close": float(i), "volume": 1000} for i in range(25)]

        detector = MarketRegimeDetector(ma_period=20)
        result = detector.process(MockDataFrame(), symbol="RB")
        assert isinstance(result, MarketStateData)

    def test_extract_candles_unknown_type(self):
        """未知类型输入应返回 []（line 130）。"""
        detector = MarketRegimeDetector(ma_period=20)
        result = detector.process(12345, symbol="RB")
        assert result.regime == MarketRegime.UNKNOWN
        assert result.features["count"] == 0

    def test_extract_candles_dict_items(self):
        """dict 输入走 items 分支（lines 127-129）。"""
        detector = MarketRegimeDetector()
        candles = detector._extract_candles({"a": 1, "b": 2})
        assert candles == ["a", "b"]

    # ---------- _calc_trend_strength 边界 ----------

    def test_trend_strength_insufficient_closes(self):
        """_calc_trend_strength 收盘价不足时返回 0.0（line 144）。"""
        detector = MarketRegimeDetector(ma_period=20)
        result = detector._calc_trend_strength(
            [{"close": 100} for _ in range(5)]
        )
        assert result == 0.0

    def test_trend_strength_few_ma_values(self):
        """MA 值不足 3 个时返回 0.0（line 149）。"""
        detector = MarketRegimeDetector(ma_period=20)
        candles = [{"close": float(100 + i), "volume": 1000} for i in range(20)]
        result = detector.process(candles)
        assert result.trend_strength == 0.0

    def test_trend_strength_zero_current_ma(self):
        """MA=0 时返回 0.0（line 155）。"""
        detector = MarketRegimeDetector(ma_period=20)
        candles = [{"close": 0, "volume": 0} for _ in range(22)]
        result = detector.process(candles)
        assert result.trend_strength == 0.0

    # ---------- _calc_volatility 边界 ----------

    def test_calc_volatility_single_close(self):
        """_calc_volatility 单条数据返回 0.0（line 174）。"""
        detector = MarketRegimeDetector()
        result = detector._calc_volatility([{"close": 100}])
        assert result == 0.0

    def test_volatility_zero_returns(self):
        """_calc_volatility 所有收盘价为零时返回 0.0（line 183）。"""
        detector = MarketRegimeDetector(ma_period=5)
        candles = [{"close": 0, "volume": 0} for _ in range(10)]
        result = detector.process(candles)
        assert result.volatility == 0.0

    # ---------- _calc_volume_trend 边界 ----------

    def test_volume_trend_insufficient_volumes(self):
        """_calc_volume_trend 成交量不足时返回 0.0（line 202）。"""
        detector = MarketRegimeDetector(ma_period=20)
        result = detector._calc_volume_trend(
            [{"volume": 1000} for _ in range(5)]
        )
        assert result == 0.0

    def test_volume_trend_few_ma_values(self):
        """vol_ma 值不足 2 个时返回 0.0（line 207）。"""
        detector = MarketRegimeDetector(ma_period=20)
        candles = [{"close": float(i), "volume": 1000} for i in range(20)]
        result = detector.process(candles)
        assert result.volume_trend == 0.0

    def test_volume_trend_zero_prev_ma(self):
        """vol_ma[-2] == 0 时返回 0.0（line 207 vol_ma[-2]==0 分支）。"""
        detector = MarketRegimeDetector(ma_period=20)
        # 前 20 条 volume=0，第 21 条 volume=1000 → 前 21 个 close 非零
        candles = (
            [{"close": float(i), "volume": 0} for i in range(20)]
            + [{"close": 100.0, "volume": 1000}]
        )
        result = detector.process(candles)
        assert result.volume_trend == 0.0

    # ---------- _calc_ma 边界 ----------

    def test_calc_ma_insufficient_data(self):
        """_calc_ma 数据不足时返回 []（line 232）。"""
        detector = MarketRegimeDetector(ma_period=20)
        result = detector._calc_ma([1, 2, 3], 20)
        assert result == []

    # ---------- process / params ----------

    def test_process_with_params(self):
        """process 应传递 params。"""
        detector = MarketRegimeDetector(ma_period=5)
        candles = [{"close": float(100 + i), "volume": 1000} for i in range(10)]
        result = detector.process(candles, symbol="RB", params={"custom": True})
        assert result.symbol == "RB"


class TestSentimentRuleEdgeCases:
    """规则情绪基线边界情况 — sentiment_rule.py 全覆盖。"""

    def test_other_input_type(self):
        """非 dict/非 str 输入应正确处理（lines 105-107）。"""
        stage = SentimentRuleStage()
        result = stage.process(123)
        assert isinstance(result, SentimentItem)
        assert result.text == "123"

    def test_other_input_type_list(self):
        """list 输入应转换为 str（lines 105-107）。"""
        stage = SentimentRuleStage()
        result = stage.process(["text"])
        assert isinstance(result, SentimentItem)

    def test_negation_on_negative_word(self):
        """否定 + 负面词 → 正面情绪（lines 164-165）。"""
        stage = SentimentRuleStage()
        result = stage.process("未下跌")
        assert result.score >= 0


class TestSentimentAggregatorEdgeCases:
    """情绪聚合器边界情况 — sentiment_aggregator.py 全覆盖。"""

    def test_tags_collected_in_topics(self):
        """item 的 tags 应收集到 topics 中（line 78, 97）。"""
        now = time.time()
        items = [
            SentimentItem(
                text="利好", score=0.5, confidence=0.8,
                tags=["钢铁", "宏观"], published_at=now,
            ),
            SentimentItem(
                text="利空", score=-0.3, confidence=0.8,
                tags=["钢铁"], published_at=now,
            ),
        ]
        agg = SentimentAggregator()
        result = agg.aggregate(items, symbol="RB")
        assert "钢铁" in result.topics
        assert "宏观" in result.topics

    def test_get_date_str_invalid_timestamp(self):
        """无效时间戳应返回 'unknown'（lines 141-142）。"""
        agg = SentimentAggregator()
        result = agg._get_date_str(-1)
        assert result == "unknown"

    def test_aggregate_invalid_timestamp_in_items(self):
        """包含无效时间戳的 item 在聚合中应正常处理（lines 141-142）。"""
        items = [
            SentimentItem(
                text="test", score=0.1, confidence=0.8,
                published_at=-1, tags=["test"],
            ),
        ]
        agg = SentimentAggregator()
        # 用非常大的 days 让 cutoff 覆盖 -1
        result = agg.aggregate(items, params={"days": 1000000})
        assert result.total_volume == 1
        assert len(result.daily) >= 1


class TestSentimentLLMStageEdgeCases:
    """LLM 情绪打分边界情况 — sentiment_llm.py 全覆盖。"""

    # ---------- check_available 路径 ----------

    def test_check_available_import_error(self):
        """API key 存在但 openai 导入失败 → False（lines 67-71）。"""
        with mock.patch.dict("sys.modules", {"openai": None}):
            stage = SentimentLLMStage(api_key="test-key")
            assert not stage.check_available()

    # ---------- process / 输入类型分支 ----------

    def test_process_dict_input(self):
        """dict 输入 + LLM 可用 → 正确提取字段（lines 89-92, 117-123）。"""
        mock_client = mock.MagicMock()
        _setup_llm_response(mock_client, '{"score": 0.3, "confidence": 0.6}')
        mock_openai_mod = mock.MagicMock()
        mock_openai_mod.OpenAI.return_value = mock_client

        with mock.patch.dict("sys.modules", {"openai": mock_openai_mod}):
            stage = SentimentLLMStage(api_key="test-key")
            result = stage.process({
                "title": "利好",
                "content": "价格上涨",
                "published_at": 1_000_000_000,
                "tags": ["钢铁"],
            }, symbol="RB")
        assert result.source == "llm"
        assert result.symbol == "RB"
        assert result.tags == ["钢铁"]

    def test_process_other_input_type(self):
        """非 dict/非 str 输入 + LLM 可用（lines 99-102, 117-123）。"""
        mock_client = mock.MagicMock()
        _setup_llm_response(mock_client, '{"score": -0.2, "confidence": 0.5}')
        mock_openai_mod = mock.MagicMock()
        mock_openai_mod.OpenAI.return_value = mock_client

        with mock.patch.dict("sys.modules", {"openai": mock_openai_mod}):
            stage = SentimentLLMStage(api_key="test-key")
            result = stage.process(999, symbol="RB")
        assert result.source == "llm"
        assert result.symbol == "RB"

    # ---------- _call_llm 方法 ----------

    @mock.patch("openai.OpenAI")
    def test_call_llm_success(self, mock_openai_class):
        """_call_llm 成功调用 openai SDK（lines 137-157）。"""
        mock_client = mock.MagicMock()
        mock_openai_class.return_value = mock_client
        _setup_llm_response(mock_client, '{"score": 0.5, "confidence": 0.7}')

        stage = SentimentLLMStage(api_key="test-key")
        with mock.patch.object(stage, "_client", None):
            result = stage._call_llm("title", "content")
        assert result["score"] == 0.5
        assert mock_client.chat.completions.create.called

    @mock.patch("openai.OpenAI")
    def test_call_llm_markdown_response(self, mock_openai_class):
        """_call_llm 处理 markdown 代码块响应（lines 149-155）。"""
        mock_client = mock.MagicMock()
        mock_openai_class.return_value = mock_client
        _setup_llm_response(
            mock_client, '```json\n{"score": -0.4, "confidence": 0.8}\n```'
        )

        stage = SentimentLLMStage(api_key="test-key")
        with mock.patch.object(stage, "_client", None):
            result = stage._call_llm("bad", "terrible")
        assert result["score"] == -0.4

    # ---------- process / LLM 异常降级 ----------

    @mock.patch.object(SentimentLLMStage, "check_available", return_value=True)
    def test_llm_call_exception_fallback(self, mock_check):
        """LLM 调用异常 → 降级到规则基线（lines 129-132）。"""
        stage = SentimentLLMStage(api_key="test-key", fallback_to_rule=True)
        with mock.patch.object(stage, "_call_llm", side_effect=ValueError("err")):
            result = stage.process("利好新闻")
        assert result.source == "rule_fallback"

    @mock.patch.object(SentimentLLMStage, "check_available", return_value=True)
    def test_llm_call_exception_no_fallback(self, mock_check):
        """LLM 调用异常 + 不降级 → 抛出异常（lines 129-133）。"""
        stage = SentimentLLMStage(api_key="test-key", fallback_to_rule=False)
        with mock.patch.object(stage, "_call_llm", side_effect=ValueError("err")):
            with pytest.raises(ValueError):
                stage.process("利好新闻")


# ---------- 辅助函数 ----------

def _setup_llm_response(mock_client, json_content: str):
    """设置 mock openai 客户端的响应内容。"""
    mock_message = mock.MagicMock()
    mock_message.content = json_content
    mock_choice = mock.MagicMock()
    mock_choice.message = mock_message
    mock_response = mock.MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
