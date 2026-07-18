"""新闻数据源基类。"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from datacore.news.models import NewsData


class NewsDataSource(ABC):
    name: str = ""
    priority: int = 99

    @abstractmethod
    def fetch_news(self, symbol: Optional[str] = None,
                   days: int = 7, limit: int = 50) -> Optional[NewsData]:
        """获取新闻数据。"""

    def check_available(self) -> bool:
        return True
