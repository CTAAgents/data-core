"""规则情绪基线 — 词典法，零成本模式。

当 LLM 不可用时的兜底方案，基于情感词典进行打分。
无需任何外部依赖，纯 Python 实现。
"""

from __future__ import annotations
import time
from typing import Any, Optional

from datacore.processing.base import ProcessingStage
from datacore.processing.models import SentimentItem


# 中文金融情感词典（简化版）
POSITIVE_WORDS = [
    # 通用正面
    "利好", "上涨", "上涨", "涨停", "大涨", "飙升", "强势", "突破", "创新高",
    "增长", "增加", "提升", "改善", "优化", "复苏", "回暖", "反弹", "回升",
    "盈利", "超预期", "利好", "支持", "鼓励", "刺激", "推动", "促进",
    # 政策正面
    "降准", "降息", "减税", "补贴", "扶持", "宽松", "刺激", "扩内需",
    # 产业正面
    "增产", "扩产", "投产", "达产", "满产", "复工", "复产", "需求旺盛",
    "供不应求", "紧平衡", "去库", "降库", "库存下降", "订单增加",
]

NEGATIVE_WORDS = [
    # 通用负面
    "利空", "下跌", "跌停", "大跌", "暴跌", "跳水", "弱势", "破位", "创新低",
    "下降", "减少", "下滑", "恶化", "衰退", "低迷", "疲软", "走弱", "回落",
    "亏损", "低于预期", "利空", "限制", "禁止", "打击", "压制", "拖累",
    # 政策负面
    "加息", "加准", "收紧", "调控", "限产", "限电", "环保督查", "整改",
    # 产业负面
    "减产", "停产", "检修", "事故", "故障", "中断", "受阻", "累库", "高库存",
    "库存积压", "需求疲软", "供过于求", "订单下降", "取消订单",
]

# 程度副词权重
DEGREE_WORDS = {
    "大幅": 1.5, "暴涨": 2.0, "暴跌": -2.0, "急剧": 1.5, "大幅增长": 1.5,
    "大幅下降": -1.5, "显著": 1.3, "明显": 1.2, "轻微": 0.7, "小幅": 0.8,
    "略有": 0.6, "微幅": 0.5, "持续": 1.2, "连续": 1.1,
}

# 否定词
NEGATION_WORDS = {"不", "未", "没有", "无", "非", "莫", "勿", "难以"}


class SentimentRuleStage(ProcessingStage):
    """规则情绪基线 — 词典法打分。

    零成本模式，无需 LLM 调用。
    基于中文金融情感词典进行情绪打分。

    输入: 新闻文本（标题+正文）
    输出: SentimentItem（含 score 和 confidence）
    """

    input_type = "NEWS"
    output_type = "SENTIMENT_ITEM"
    name = "sentiment_rule"
    priority = 1  # 低于 LLM（priority=0）

    def __init__(self, custom_positive: list[str] | None = None,
                 custom_negative: list[str] | None = None):
        self.positive_words = list(POSITIVE_WORDS)
        self.negative_words = list(NEGATIVE_WORDS)
        if custom_positive:
            self.positive_words.extend(custom_positive)
        if custom_negative:
            self.negative_words.extend(custom_negative)

    def check_available(self) -> bool:
        """规则基线始终可用。"""
        return True

    def process(self, input_data: Any, symbol: Optional[str] = None,
                params: Optional[dict] = None) -> SentimentItem:
        """对新闻文本进行规则情绪打分。

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
            text = f"{title}\n{content}"
            published_at = input_data.get("published_at", 0.0)
            tags = input_data.get("tags", [])
        elif isinstance(input_data, str):
            text = input_data
            published_at = 0.0
            tags = []
        else:
            text = str(input_data)
            published_at = 0.0
            tags = []

        if not text.strip():
            return SentimentItem(
                text=text, score=0.0, confidence=0.0,
                source="rule", symbol=symbol or "",
                tags=tags, published_at=published_at,
                collected_at=time.time(),
            )

        score = self._score_text(text)
        # 规则基线的置信度：无匹配词时为0，有匹配时基于分数绝对值
        if score == 0.0:
            confidence = 0.0
        else:
            confidence = min(0.6, abs(score) * 0.8 + 0.2)

        return SentimentItem(
            text=text, score=score, confidence=confidence,
            source="rule", symbol=symbol or "",
            tags=tags, published_at=published_at,
            collected_at=time.time(),
        )

    def _score_text(self, text: str) -> float:
        """基于词典计算情绪分数。

        Returns:
            情绪分数 (-1.0 ~ +1.0)
        """
        pos_count = 0
        neg_count = 0
        pos_weight = 0.0
        neg_weight = 0.0

        text_lower = text.lower()

        # 统计正面词
        for word in self.positive_words:
            count = text_lower.count(word.lower())
            if count > 0:
                # 检查程度副词
                weight = self._get_degree_weight(text, word)
                # 检查否定词
                if self._has_negation(text, word):
                    neg_count += count
                    neg_weight += count * weight
                else:
                    pos_count += count
                    pos_weight += count * weight

        # 统计负面词
        for word in self.negative_words:
            count = text_lower.count(word.lower())
            if count > 0:
                weight = self._get_degree_weight(text, word)
                if self._has_negation(text, word):
                    pos_count += count
                    pos_weight += count * weight
                else:
                    neg_count += count
                    neg_weight += count * weight

        total = pos_count + neg_count
        if total == 0:
            return 0.0

        # 情绪分数 = (正面权重 - 负面权重) / 总权重
        raw_score = (pos_weight - neg_weight) / max(pos_weight + neg_weight, 1.0)
        # 限制在 [-1, 1] 范围
        return max(-1.0, min(1.0, raw_score))

    def _get_degree_weight(self, text: str, word: str) -> float:
        """检查词前面的程度副词，返回权重。"""
        idx = text.find(word)
        if idx < 2:
            return 1.0
        # 检查词前 4 个字符是否有程度副词
        prefix = text[max(0, idx - 4):idx]
        for degree_word, weight in DEGREE_WORDS.items():
            if degree_word in prefix:
                return abs(weight)
        return 1.0

    def _has_negation(self, text: str, word: str) -> bool:
        """检查词前是否有否定词。"""
        idx = text.find(word)
        if idx < 1:
            return False
        prefix = text[max(0, idx - 3):idx]
        for neg_word in NEGATION_WORDS:
            if neg_word in prefix:
                return True
        return False
