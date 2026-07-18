"""华尔街见闻数据源 — 新闻源 P1。"""

from __future__ import annotations
from typing import Optional
import httpx
from datacore.news.providers.base import NewsDataSource
from datacore.news.models import NewsData, NewsItem


class WallStreetCnProvider(NewsDataSource):
    """华尔街见闻数据源。"""
    name = "wallstreet_cn"
    priority = 1

    def fetch_news(self, symbol: Optional[str] = None,
                   days: int = 7, limit: int = 50) -> Optional[NewsData]:
        """从华尔街见闻获取新闻。"""
        try:
            with httpx.Client(timeout=10) as c:
                resp = c.get(
                    "https://api-one.wallstreetcn.com/apiv1/news/live-news",
                    params={
                        "limit": limit,
                        "channel": "global",
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    },
                )
                data = resp.json().get("data", {})
                items_list = data.get("items", []) if data else []
        except Exception:
            return None
        if not items_list:
            return None
        items = []
        for item in items_list[:limit]:
            try:
                content = item.get("content_text", "") or item.get("title", "")
                items.append(NewsItem(
                    title=str(item.get("title", "") or ""),
                    content=str(content or ""),
                    published_at=str(item.get("display_time", "") or ""),
                    source="wallstreet_cn",
                    url=str(item.get("uri", "") or ""),
                    tags=[],
                    related_symbols=[],
                ))
            except Exception:
                continue
        if not items:
            return None
        return NewsData(symbol=symbol, total=len(items), items=items)

    def check_available(self) -> bool:
        try:
            with httpx.Client(timeout=5) as c:
                r = c.head("https://wallstreetcn.com")
                return r.status_code < 500
        except Exception:
            return False
