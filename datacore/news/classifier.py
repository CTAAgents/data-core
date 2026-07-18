"""新闻分类器 — Data-Core 数据加工层。

给 NEWS 打分类标签（宏观/产业/公司/政策），
属数据加工，不是因子计算。
"""

from __future__ import annotations
from typing import Optional


NEWS_CATEGORIES = {
    "macro": [
        "宏观", "经济", "GDP", "CPI", "PPI", "PMI", "M2", "LPR", "利率",
        "央行", "美联储", "货币政策", "财政", "通胀", "通缩", "衰退",
        "就业", "失业率", "消费", "投资", "出口", "进口", "贸易",
    ],
    "policy": [
        "政策", "监管", "新规", "通知", "办法", "条例", "规定", "意见",
        "证监会", "银保监会", "发改委", "财政部", "国务院", "国资委",
        "上调", "下调", "批准", "禁止", "限制", "鼓励", "支持",
    ],
    "industry": [
        "产业", "行业", "产能", "产量", "开工率", "库存", "需求",
        "供应", "供需", "减产", "增产", "停产", "复产", "检修",
        "进口量", "出口量", "到港", "出库", "入库", "厂库", "社库",
    ],
    "company": [
        "公司", "企业", "上市公司", "业绩", "财报", "营收", "利润",
        "亏损", "盈利", "分红", "配股", "增发", "回购", "减持",
        "增持", "并购", "重组", "董事长", "总经理", "高管",
    ],
}


class NewsClassifier:
    """基于关键词的新闻分类器。

    给新闻打分类标签，属于数据加工层，
    不涉及情绪打分（情绪由 FTS 负责）。
    """

    def __init__(self, custom_keywords: Optional[dict[str, list[str]]] = None):
        self.keywords = dict(NEWS_CATEGORIES)
        if custom_keywords:
            for cat, words in custom_keywords.items():
                if cat in self.keywords:
                    self.keywords[cat].extend(words)
                else:
                    self.keywords[cat] = words

    def classify(self, text: str) -> list[str]:
        """对文本进行分类，返回匹配的分类标签列表。"""
        if not text:
            return []
        matched = []
        text_lower = text.lower()
        for category, keywords in self.keywords.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    matched.append(category)
                    break
        return matched

    def classify_item(self, title: str, content: str = "") -> list[str]:
        """对单条新闻（标题+正文）分类。"""
        return self.classify(f"{title}\n{content}")

    def extract_symbols(self, text: str, symbol_list: list[str]) -> list[str]:
        """从文本中提取相关品种符号。"""
        if not text or not symbol_list:
            return []
        found = []
        text_upper = text.upper()
        for sym in symbol_list:
            sym_upper = sym.upper()
            if sym_upper in text_upper:
                found.append(sym_upper)
        return found
