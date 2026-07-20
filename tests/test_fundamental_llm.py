"""基本面 LLM 加工测试。"""
import json


class TestFundamentalModels:
    """基本面数据模型测试。"""

    def test_report_summary_defaults(self):
        from datacore.processing.fundamental.models import ReportSummary
        r = ReportSummary()
        assert r.direction == ""
        assert r.key_points == []
        assert r.risk_factors == []

    def test_earning_summary_defaults(self):
        from datacore.processing.fundamental.models import EarningSummary
        e = EarningSummary()
        assert e.revenue is None
        assert e.profit is None

    def test_fundamental_summary_defaults(self):
        from datacore.processing.fundamental.models import FundamentalSummary
        f = FundamentalSummary()
        assert f.composite_score == 0.0
        assert f.reports == []
        assert f.earnings == []


class TestFundamentalLLMStage:
    """研报 LLM 加工测试。"""

    def test_process_dict_input_no_key(self):
        from datacore.processing.fundamental.fundamental_llm import FundamentalLLMStage
        stage = FundamentalLLMStage()
        result = stage.process(
            {"title": "螺纹钢走势分析", "content": "需求回暖，看多后市"},
            symbol="RB",
        )
        assert result is not None
        assert result.symbol == "RB"
        assert result.source == "llm"
        assert len(result.reports) == 0  # 无 API Key

    def test_process_string_input_no_key(self):
        from datacore.processing.fundamental.fundamental_llm import FundamentalLLMStage
        stage = FundamentalLLMStage()
        result = stage.process("看多螺纹钢后市", symbol="RB")
        assert result is not None
        assert result.symbol == "RB"

    def test_process_empty_input(self):
        from datacore.processing.fundamental.fundamental_llm import FundamentalLLMStage
        stage = FundamentalLLMStage()
        result = stage.process("", symbol="RB")
        assert result is not None
        assert len(result.reports) == 0

    def test_check_available_no_key(self):
        from datacore.processing.fundamental.fundamental_llm import FundamentalLLMStage
        stage = FundamentalLLMStage()
        assert stage.check_available() is False

    def test_check_available_with_key(self, mocker):
        from datacore.processing.fundamental.fundamental_llm import FundamentalLLMStage
        stage = FundamentalLLMStage(api_key="test_key")
        mocker.patch("openai.OpenAI")
        assert stage.check_available() is True

    def test_llm_response_parsing(self, mocker):
        from datacore.processing.fundamental.fundamental_llm import FundamentalLLMStage
        stage = FundamentalLLMStage(api_key="test_key")
        mocker.patch.object(stage, 'check_available', return_value=True)

        mock_client = mocker.MagicMock()
        mock_choice = mocker.MagicMock()
        mock_choice.message.content = json.dumps({
            "direction": "看多",
            "strength": "强烈",
            "time_horizon": "中期",
            "key_points": ["需求复苏", "库存下降"],
            "risk_factors": ["政策风险"],
        })
        mock_response = mocker.MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        stage._client = mock_client

        result = stage.process(
            {"title": "研报", "content": "内容"},
            symbol="RB",
        )
        assert result is not None
        assert len(result.reports) == 1
        report = result.reports[0]
        assert report.direction == "看多"
        assert report.strength == "强烈"
        assert len(report.key_points) == 2


class TestEarningLLMStage:
    """财报 LLM 加工测试。"""

    def test_process_dict_no_key(self):
        from datacore.processing.fundamental.fundamental_llm import EarningLLMStage
        stage = EarningLLMStage()
        result = stage.process(
            {"content": "营收100亿，利润20亿"},
            symbol="600519",
        )
        assert result is not None
        assert result.symbol == "600519"
        assert len(result.earnings) == 0  # 无 API Key

    def test_process_empty_input(self):
        from datacore.processing.fundamental.fundamental_llm import EarningLLMStage
        stage = EarningLLMStage()
        result = stage.process("", symbol="600519")
        assert result is not None
        assert len(result.earnings) == 0

    def test_check_available_no_key(self):
        from datacore.processing.fundamental.fundamental_llm import EarningLLMStage
        stage = EarningLLMStage()
        assert stage.check_available() is False

    def test_llm_response_parsing(self, mocker):
        from datacore.processing.fundamental.fundamental_llm import EarningLLMStage
        stage = EarningLLMStage(api_key="test_key")
        mocker.patch.object(stage, 'check_available', return_value=True)

        mock_client = mocker.MagicMock()
        mock_choice = mocker.MagicMock()
        mock_choice.message.content = json.dumps({
            "period": "2026Q1",
            "revenue": 100.0,
            "revenue_yoy": 15.0,
            "profit": 20.0,
            "profit_yoy": 25.0,
            "roe": 18.5,
            "cash_flow": 30.0,
            "summary": "业绩超预期",
        })
        mock_response = mocker.MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        stage._client = mock_client

        result = stage.process(
            {"content": "营收100亿，利润20亿"},
            symbol="600519",
        )
        assert result is not None
        assert len(result.earnings) == 1
        earning = result.earnings[0]
        assert earning.revenue == 100.0
        assert earning.profit == 20.0
        assert earning.roe == 18.5

    def test_safe_float_null(self):
        from datacore.processing.fundamental.fundamental_llm import EarningLLMStage
        assert EarningLLMStage._safe_float(None) is None

    def test_safe_float_str(self):
        from datacore.processing.fundamental.fundamental_llm import EarningLLMStage
        assert EarningLLMStage._safe_float("invalid") is None

    def test_safe_float_valid(self):
        from datacore.processing.fundamental.fundamental_llm import EarningLLMStage
        assert EarningLLMStage._safe_float("15.5") == 15.5
        assert EarningLLMStage._safe_float(100) == 100.0

    def test_llm_failure_graceful(self, mocker):
        """LLM 调用失败时静默返回空摘要。"""
        from datacore.processing.fundamental.fundamental_llm import EarningLLMStage
        stage = EarningLLMStage(api_key="test_key")
        mocker.patch.object(stage, 'check_available', return_value=True)

        mock_client = mocker.MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        stage._client = mock_client

        result = stage.process(
            {"content": "营收100亿"},
            symbol="600519",
        )
        assert result is not None
        assert len(result.earnings) == 0
