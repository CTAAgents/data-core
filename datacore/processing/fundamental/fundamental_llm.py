"""基本面 LLM 加工 — 研报/财报结构化摘要。

研报加工流程:
  研报全文 → LLM prompt → 结构化摘要 ReportSummary

财报加工流程:
  财报文本 → LLM prompt → 关键指标 EarningSummary

依赖: openai SDK
配置: DATACORE_LLM_API_KEY / DATACORE_LLM_MODEL
"""
from __future__ import annotations
import json
import os
import time
from typing import Any, Optional

from datacore.processing.base import ProcessingStage
from .models import FundamentalSummary, ReportSummary, EarningSummary


REPORT_PROMPT_TEMPLATE = """请对以下研报进行结构化分析，返回 JSON 格式。

研报标题: {title}
研报内容: {content}

请返回以下 JSON 格式（不要包含其他内容）:
{{
    "direction": "<看多/看空/中性>",
    "strength": "<强烈/一般/谨慎>",
    "time_horizon": "<短期/中期/长期>",
    "key_points": ["要点1", "要点2"],
    "risk_factors": ["风险1", "风险2"]
}}

要求:
- 仅返回有效 JSON
- 不要包含 markdown 代码块标记
"""


EARNING_PROMPT_TEMPLATE = """请从以下财报文本中提取关键财务指标，返回 JSON 格式。

财报文本: {content}

请返回以下 JSON 格式（不要包含其他内容）:
{{
    "period": "<报告期>",
    "revenue": <营收，单位亿元>,
    "revenue_yoy": <营收同比，百分比>,
    "revenue_qoq": <营收环比，百分比>,
    "profit": <净利润，单位亿元>,
    "profit_yoy": <净利润同比，百分比>,
    "profit_qoq": <净利润环比，百分比>,
    "roe": <净资产收益率，百分比>,
    "cash_flow": <现金流，单位亿元>,
    "summary": "<一句话总结>"
}}

要求:
- 无法提取的指标返回 null
- 仅返回有效 JSON
- 不要包含 markdown 代码块标记
"""


class FundamentalLLMStage(ProcessingStage):
    """研报结构化摘要。

    输入: 研报文本
    输出: FundamentalSummary（含 ReportSummary 列表）
    """

    input_type = "REPORT"
    output_type = "FUNDAMENTAL_SUMMARY"
    name = "fundamental_llm"
    priority = 0

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("DATACORE_LLM_API_KEY", "")
        self.model = model or os.environ.get("DATACORE_LLM_MODEL", "gpt-4o-mini")
        self._client = None

    def check_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import openai  # noqa: F401
            return True
        except ImportError:
            return False

    def process(self, input_data: Any, symbol: Optional[str] = None,
                params: Optional[dict] = None) -> FundamentalSummary:
        """加工研报/财报为结构化摘要。"""
        params = params or {}
        collected_at = time.time()

        if isinstance(input_data, dict):
            title = input_data.get("title", "")
            content = input_data.get("content", "")
        elif isinstance(input_data, str):
            title = ""
            content = input_data
        else:
            title = ""
            content = str(input_data)

        summary = FundamentalSummary(
            symbol=symbol or "",
            source="llm",
            collected_at=collected_at,
        )

        if not content and not title:
            return summary

        # 调用 LLM 加工研报
        if self.check_available():
            try:
                report_summary = self._process_report(title, content, symbol)
                if report_summary:
                    summary.reports.append(report_summary)
            except Exception:
                pass

        return summary

    def _process_report(self, title: str, content: str,
                        symbol: Optional[str]) -> Optional[ReportSummary]:
        """调用 LLM 提取研报结构化信息。"""
        try:
            if self._client is None:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)

            prompt = REPORT_PROMPT_TEMPLATE.format(
                title=title[:100], content=content[:1000]
            )
            assert self._client is not None
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )
            text = response.choices[0].message.content.strip()
            # 清理代码块
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            data = json.loads(text)
            return ReportSummary(
                title=title,
                symbol=symbol or "",
                direction=str(data.get("direction", "中性")),
                strength=str(data.get("strength", "一般")),
                time_horizon=str(data.get("time_horizon", "中期")),
                key_points=data.get("key_points", []),
                risk_factors=data.get("risk_factors", []),
                source="llm",
            )
        except Exception:
            return None


class EarningLLMStage(ProcessingStage):
    """财报关键信息抽取。

    输入: 财报文本
    输出: FundamentalSummary（含 EarningSummary 列表）
    """

    input_type = "EARNING"
    output_type = "FUNDAMENTAL_SUMMARY"
    name = "earning_llm"
    priority = 1

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("DATACORE_LLM_API_KEY", "")
        self.model = model or os.environ.get("DATACORE_LLM_MODEL", "gpt-4o-mini")
        self._client = None

    def check_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import openai  # noqa: F401
            return True
        except ImportError:
            return False

    def process(self, input_data: Any, symbol: Optional[str] = None,
                params: Optional[dict] = None) -> FundamentalSummary:
        """从财报文本提取关键财务指标。"""
        params = params or {}
        collected_at = time.time()

        content = ""
        if isinstance(input_data, dict):
            content = input_data.get("content", "") or input_data.get("text", "")
        elif isinstance(input_data, str):
            content = input_data
        else:
            content = str(input_data)

        summary = FundamentalSummary(
            symbol=symbol or "",
            source="llm",
            collected_at=collected_at,
        )

        if not content:
            return summary

        if self.check_available():
            try:
                earning = self._process_earning(content, symbol)
                if earning:
                    summary.earnings.append(earning)
                    summary.source = "llm"
            except Exception:
                pass

        return summary

    def _process_earning(self, content: str,
                         symbol: Optional[str]) -> Optional[EarningSummary]:
        """调用 LLM 提取财报关键指标。"""
        try:
            if self._client is None:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)

            prompt = EARNING_PROMPT_TEMPLATE.format(content=content[:1500])
            assert self._client is not None
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )
            text = response.choices[0].message.content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            data = json.loads(text)
            return EarningSummary(
                symbol=symbol or "",
                period=str(data.get("period", "")),
                revenue=self._safe_float(data.get("revenue")),
                revenue_yoy=self._safe_float(data.get("revenue_yoy")),
                revenue_qoq=self._safe_float(data.get("revenue_qoq")),
                profit=self._safe_float(data.get("profit")),
                profit_yoy=self._safe_float(data.get("profit_yoy")),
                profit_qoq=self._safe_float(data.get("profit_qoq")),
                roe=self._safe_float(data.get("roe")),
                cash_flow=self._safe_float(data.get("cash_flow")),
                source="llm",
                summary=str(data.get("summary", "")),
            )
        except Exception:
            return None

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
