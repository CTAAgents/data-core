"""新闻资讯模块 — 新闻采集 + 分类加工。"""
from .news_provider import NewsDataProvider
from .classifier import NewsClassifier

__all__ = ["NewsDataProvider", "NewsClassifier"]
