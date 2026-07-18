"""LLM 情绪打分 — Data-Core 数据加工层。

使用 LLM 对新闻进行高质量情绪打分。
当 LLM 不可用时，降级到规则基线（SentimentRuleStage）。

依赖: 需要安装 LLM SDK（如 openai / anthropic 等）
配置: 通过环境变量 DATACORE_LLM_API_KEY / DATACORE_LLM_MODEL 设置
"""

from __future__ import annotations
import os
import time
import json
from typing import Any, Optional

from datacore.processing.base import ProcessingStage
from datacore.processing.models import SentimentItem


# LLM 情绪打分的 prompt 模板
SENTIMENT_PROMPT_TEMPLATE = """请对以下金融新闻进行情绪分析，返回 JSON 格式。

新闻标题: {title}
新闻内容: {content}

请返回以下 JSON 格式（不要包含其他内容）:
{{
    "score": <情绪分数，-1.0 到 1.0 之间，-1.0=极度悲观，0.0=中性，1.0=极度乐观>,
    "confidence": <置信度，0.0 到 1.0 之间>,
    "reasoning": "<简要理由，不超过50字>"
}}

注意:
- 基于新闻对相关品种/市场的影响判断情绪
- 利好新闻给正分，利空新闻给负分，中性新闻给接近0的分数
- 仅返回 JSON，不要包含 markdown 代码块标记
"""


class SentimentLLMStage(ProcessingStage):
    """LLM 情绪打分 — 高质量模式。

    使用 LLM 对新闻进行情绪打分，质量优于规则基线。
    需要 LLM SDK 和 API Key 配置。

    降级策略:
    - LLM 不可用 -> 降级到 SentimentRuleStage
    - LLM 调用失败 -> 降级到 SentimentRuleStage
    """

    input_type = "NEWS"
    output_type = "SENTIMENT_ITEM"
    name = "sentiment_llm"
    priority = 0  # 最高优先级

    def __init__(self, model: str | None = None, api_key: str | None = None,
                 fallback_to_rule: bool = True):
        self.model = model or os.environ.get("DATACORE_LLM_MODEL", "gpt-4o-mini")
        self.api_key = api_key or os.environ.get("DATACORE_LLM_API_KEY", "")
        self.fallback_to_rule = fallback_to_rule
        self._client = None

    def check_available(self) -> bool:
        """检查 LLM 是否可用。"""
        if not self.api_key:
            return False
        try:
            import openai  # noqa: F401
            return True
        except ImportError:
            return False

    def process(self, input_data: Any, symbol: Optional[str] = None,
                params: Optional[dict] = None) -> SentimentItem:
        """对新闻文本进行 LLM 情绪打分。

        Args:
            input_data: 可以是字符串（文本）或字典（含 title/content）
            symbol: 品种代码
            params: 可选参数

        Returns:
            SentimentItem: 情绪打分结果
        """
        params = params or {}

        # 提取文本
        if isinstance(input_data, dict):
            title = input_data.get("title", "")
            content = input_data.get("content", "")
            published_at = input_data.get("published_at", 0.0)
            tags = input_data.get("tags", [])
        elif isinstance(input_data, str):
            title = input_data
            content = ""
            published_at = 0.0
            tags = []
        else:
            title = str(input_data)
            content = ""
            published_at = 0.0
            tags = []

        # LLM 不可用时降级到规则基线
        if not self.check_available():
            if self.fallback_to_rule:
                return self._fallback_to_rule(input_data, symbol, tags, published_at)
            return SentimentItem(
                text=f"{title}\n{content}", score=0.0, confidence=0.0,
                source="llm_unavailable", symbol=symbol or "",
                tags=tags, published_at=published_at,
                collected_at=time.time(),
            )

        try:
            result = self._call_llm(title, content)
            score = float(result.get("score", 0.0))
            confidence = float(result.get("confidence", 0.5))
            # 限制范围
            score = max(-1.0, min(1.0, score))
            confidence = max(0.0, min(1.0, confidence))

            return SentimentItem(
                text=f"{title}\n{content}", score=score, confidence=confidence,
                source="llm", symbol=symbol or "",
                tags=tags, published_at=published_at,
                collected_at=time.time(),
            )
        except Exception:
            # LLM 调用失败，降级到规则基线
            if self.fallback_to_rule:
                return self._fallback_to_rule(input_data, symbol, tags, published_at)
            raise

    def _call_llm(self, title: str, content: str) -> dict:
        """调用 LLM 进行情绪打分。"""
        if self._client is None:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)

        prompt = SENTIMENT_PROMPT_TEMPLATE.format(title=title, content=content[:500])
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        # 清理可能的 markdown 代码块标记
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        return json.loads(text)

    def _fallback_to_rule(self, input_data: Any, symbol: Optional[str],
                          tags: list[str], published_at: float) -> SentimentItem:
        """降级到规则基线。"""
        from datacore.processing.sentiment.sentiment_rule import SentimentRuleStage
        rule_stage = SentimentRuleStage()
        result = rule_stage.process(input_data, symbol)
        # 标记来源为降级
        result.source = "rule_fallback"
        return result
