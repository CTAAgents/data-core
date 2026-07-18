"""新闻数据模型。"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NewsItem:
    """单条新闻。"""
    title: str
    content: str = ""
    published_at: str = ""
    source: str = ""
    url: str = ""
    tags: list[str] = field(default_factory=list)
    related_symbols: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class NewsData:
    """新闻数据集。"""
    symbol: Optional[str] = None
    total: int = 0
    items: list[NewsItem] = field(default_factory=list)

    def filter_by_tag(self, tag: str) -> list[NewsItem]:
        return [item for item in self.items if tag in item.tags]

    def filter_by_symbol(self, symbol: str) -> list[NewsItem]:
        return [item for item in self.items if symbol.upper() in item.related_symbols]
