"""财联社快讯数据源 — 新闻源 P0。"""

from __future__ import annotations
from typing import Optional
import httpx
from datacore.news.providers.base import NewsDataSource
from datacore.news.models import NewsData, NewsItem


class ClsProvider(NewsDataSource):
    """财联社快讯数据源。"""
    name = "cls"
    priority = 0

    def fetch_news(self, symbol: Optional[str] = None,
                   days: int = 7, limit: int = 50) -> Optional[NewsData]:
        """从财联社获取快讯新闻。"""
        try:
            with httpx.Client(timeout=10) as c:
                resp = c.get(
                    "https://www.cls.cn/nodeapi/telegraphList",
                    params={
                        "app": "CailianpressWeb",
                        "category": "",
                        "lastTime": "",
                        "os": "web",
                        "rn": limit,
                        "sv": "8.4.6",
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": "https://www.cls.cn/telegraph",
                    },
                )
                data = resp.json().get("data", {})
                roll_data = data.get("roll_data", []) if data else []
        except Exception:
            return None
        if not roll_data:
            return None
        items = []
        for item in roll_data[:limit]:
            try:
                items.append(NewsItem(
                    title=str(item.get("title", "") or ""),
                    content=str(item.get("content", "") or ""),
                    published_at=str(item.get("ctime", "") or ""),
                    source="cls",
                    url=f"https://www.cls.cn/detail/{item.get('id', '')}",
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
                r = c.head("https://www.cls.cn")
                return r.status_code < 500
        except Exception:
            return False
