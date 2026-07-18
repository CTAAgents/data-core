"""LLM 情绪打分端到端测试（Mock 模式）。

验证 SentimentLLMStage 的：
1. prompt 模板和响应解析的正确性
2. LLM→规则降级的逻辑
3. 集成到 UnifiedDataProvider 的路由
"""

import json
import time
import builtins
import pytest


class TestSentimentLLMStage:
    """SentimentLLMStage 完整测试。"""

    def test_process_dict_with_title_content(self):
        """测试输入为字典（含 title/content）的正常路径。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(fallback_to_rule=True)
        input_data = {
            "title": "利好新闻",
            "content": "公司业绩大幅增长",
            "published_at": time.time(),
            "tags": ["company"],
        }
        result = stage.process(input_data, symbol="RB")
        assert result is not None
        assert isinstance(result.score, float)
        assert -1.0 <= result.score <= 1.0
        # 无 API Key 时降级到规则
        assert result.source == "rule_fallback"

    def test_process_string_input(self):
        """测试输入为字符串文本。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(fallback_to_rule=True)
        result = stage.process("利好: 央行降息刺激经济", symbol="RB")
        assert result is not None
        assert result.source == "rule_fallback"

    def test_process_empty_text(self):
        """测试空文本输入。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(fallback_to_rule=True)
        result = stage.process("", symbol="RB")
        assert result is not None
        assert result.score == 0.0

    def test_check_available_no_key(self):
        """无 API Key 时不可用。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(api_key="")
        assert stage.check_available() is False

    def test_check_available_no_openai(self, mocker):
        """有 API Key 但 openai 包不可用时不可用。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(api_key="test_key")

        # 模拟 import openai 抛出 ImportError
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "openai":
                raise ImportError(f"No module named '{name}'")
            return real_import(name, *args, **kwargs)

        mocker.patch("builtins.__import__", side_effect=mock_import)
        assert stage.check_available() is False

    def test_fallback_disabled_no_key(self):
        """无 API Key 且 fallback 关闭时返回默认值。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(fallback_to_rule=False)
        result = stage.process("利好新闻", symbol="RB")
        assert result is not None
        assert result.score == 0.0
        assert result.source == "llm_unavailable"

    def test_prompt_template_format(self):
        """验证 prompt 模板格式正确。"""
        from datacore.processing.sentiment.sentiment_llm import SENTIMENT_PROMPT_TEMPLATE
        prompt = SENTIMENT_PROMPT_TEMPLATE.format(title="测试标题", content="测试内容")
        assert "测试标题" in prompt
        assert "测试内容" in prompt
        assert "score" in prompt or "情绪分数" in prompt

    def test_llm_response_parsing(self, mocker):
        """测试 LLM 返回 JSON 的解析逻辑。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(api_key="test_key", fallback_to_rule=False)

        # Mock check_available 返回 True
        mocker.patch.object(stage, "check_available", return_value=True)

        # Mock OpenAI SDK
        mock_client = mocker.MagicMock()
        mock_choice = mocker.MagicMock()
        mock_choice.message.content = json.dumps({
            "score": 0.8, "confidence": 0.9, "reasoning": "利好"
        })
        mock_response = mocker.MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        stage._client = mock_client

        result = stage.process({"title": "利好", "content": "大涨"}, symbol="RB")
        assert result is not None
        assert result.score == 0.8
        assert result.confidence == 0.9
        assert result.source == "llm"

    def test_llm_response_with_codeblock(self, mocker):
        """测试 LLM 返回 markdown 代码块时的清理逻辑。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(api_key="test_key", fallback_to_rule=False)

        mocker.patch.object(stage, "check_available", return_value=True)

        mock_client = mocker.MagicMock()
        mock_choice = mocker.MagicMock()
        mock_choice.message.content = (
            "```json\n"
            '{"score": -0.5, "confidence": 0.7, "reasoning": "利空"}\n'
            "```"
        )
        mock_response = mocker.MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        stage._client = mock_client

        result = stage.process({"title": "利空", "content": "下跌"}, symbol="RB")
        assert result is not None
        assert result.score == -0.5
        assert result.confidence == 0.7
        assert result.source == "llm"

    def test_llm_failure_fallback(self, mocker):
        """LLM 调用失败时降级到规则基线。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(api_key="test_key", fallback_to_rule=True)

        mocker.patch.object(stage, "check_available", return_value=True)

        mock_client = mocker.MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        stage._client = mock_client

        result = stage.process({"title": "利好", "content": "经济数据好转"}, symbol="RB")
        assert result is not None
        assert result.source == "rule_fallback"

    def test_llm_failure_no_fallback(self, mocker):
        """LLM 调用失败且 fallback 关闭时抛出异常。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(api_key="test_key", fallback_to_rule=False)

        mocker.patch.object(stage, "check_available", return_value=True)

        mock_client = mocker.MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        stage._client = mock_client

        with pytest.raises(Exception):
            stage.process({"title": "利好", "content": "数据"}, symbol="RB")

    def test_score_clamping(self, mocker):
        """验证分数被限制在 [-1, 1] 范围内。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(api_key="test_key", fallback_to_rule=False)

        mocker.patch.object(stage, "check_available", return_value=True)

        for extreme_score in [5.0, -5.0, 100.0]:
            mock_client = mocker.MagicMock()
            mock_choice = mocker.MagicMock()
            mock_choice.message.content = json.dumps({
                "score": extreme_score, "confidence": 0.8, "reasoning": "test",
            })
            mock_response = mocker.MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            stage._client = mock_client

            result = stage.process({"title": "test", "content": "test"}, symbol="RB")
            assert -1.0 <= result.score <= 1.0

    def test_confidence_clamping(self, mocker):
        """验证置信度被限制在 [0, 1] 范围内。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(api_key="test_key", fallback_to_rule=False)

        mocker.patch.object(stage, "check_available", return_value=True)

        for extreme_conf in [5.0, -1.0]:
            mock_client = mocker.MagicMock()
            mock_choice = mocker.MagicMock()
            mock_choice.message.content = json.dumps({
                "score": 0.5, "confidence": extreme_conf, "reasoning": "test",
            })
            mock_response = mocker.MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            stage._client = mock_client

            result = stage.process({"title": "test", "content": "test"}, symbol="RB")
            assert 0.0 <= result.confidence <= 1.0

    def test_invalid_json_fallback(self, mocker):
        """LLM 返回无效 JSON 时降级。"""
        from datacore.processing.sentiment.sentiment_llm import SentimentLLMStage
        stage = SentimentLLMStage(api_key="test_key", fallback_to_rule=True)

        mocker.patch.object(stage, "check_available", return_value=True)

        mock_client = mocker.MagicMock()
        mock_choice = mocker.MagicMock()
        mock_choice.message.content = "这不是 JSON 格式的响应"
        mock_response = mocker.MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        stage._client = mock_client

        result = stage.process({"title": "test", "content": "test"}, symbol="RB")
        assert result is not None
        assert result.source == "rule_fallback"

    def test_sentiment_in_unified_api(self, mocker):
        """测试情绪数据在 UnifiedDataProvider 中的路由。"""
        from datacore.api import UnifiedDataProvider
        from datacore.models.enums import DataType

        dp = UnifiedDataProvider()

        # Mock 所有依赖
        mocker.patch("datacore.api._get_cache")
        mocker.patch("datacore.api._get_duckdb")

        mock_news = mocker.patch("datacore.api._get_news")
        mock_news_instance = mocker.MagicMock()
        mock_news_instance.get.return_value = mocker.MagicMock(
            available=True,
            data=[{
                "title": "利好",
                "content": "上涨",
                "published_at": time.time(),
                "tags": ["macro"],
            }],
        )
        mock_news.return_value = mock_news_instance

        mock_sentiment = mocker.patch("datacore.api._get_sentiment_llm")
        mock_sentiment_instance = mocker.MagicMock()
        mock_sentiment_instance.check_available.return_value = False
        mock_sentiment.return_value = mock_sentiment_instance

        mock_aggregator = mocker.patch("datacore.api._get_sentiment_aggregator")
        mock_aggregator_instance = mocker.MagicMock()
        from datacore.processing.models import SentimentData
        mock_aggregator_instance.aggregate.return_value = SentimentData(
            symbol="RB", overall_score=0.5
        )
        mock_aggregator.return_value = mock_aggregator_instance

        result = dp.get("RB", DataType.SENTIMENT, {"days": 30})
        assert result is not None
        assert result.data_type == DataType.SENTIMENT
