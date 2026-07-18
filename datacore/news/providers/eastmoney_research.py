"""东方财富研报数据源 — 新闻源 P2。"""

from __future__ import annotations
from typing import Optional
import httpx
from datacore.news.providers.base import NewsDataSource
from datacore.news.models import NewsData, NewsItem


class EastMoneyResearchProvider(NewsDataSource):
    """东方财富研报数据源。"""
    name = "eastmoney_research"
    priority = 2

    def fetch_news(self, symbol: Optional[str] = None,
                   days: int = 7, limit: int = 50) -> Optional[NewsData]:
        """从东方财富获取研报数据。"""
        try:
            with httpx.Client(timeout=10) as c:
                resp = c.get(
                    "https://reportapi.eastmoney.com/report/list",
                    params={
                        "cb": "",
                        "pageSize": limit,
                        "pageNo": 1,
                        "qType": 0,
                        "orgCode": "",
                        "industryCode": "*",
                        "title": "",
                        "fields": "",
                        "beginTime": "",
                        "endTime": "",
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": "https://data.eastmoney.com/report/",
                    },
                )
                data = resp.json().get("data", [])
        except Exception:
            return None
        if not data:
            return None
        items = []
        for item in data[:limit]:
            try:
                items.append(NewsItem(
                    title=str(item.get("title", "") or ""),
                    content=str(item.get("content", "") or item.get("s3", "") or ""),
                    published_at=str(item.get("publishDate", "") or ""),
                    source=f"eastmoney_{item.get('orgSName', '')}",
                    url=f"https://data.eastmoney.com/report/zw_macresearch.jshtml?encodeUrl={item.get('encodeUrl', '')}",
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
                r = c.head("https://data.eastmoney.com")
                return r.status_code < 500
        except Exception:
            return False
