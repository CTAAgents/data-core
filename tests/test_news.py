import pytest
from datacore.news.classifier import NewsClassifier
from datacore.news.models import NewsItem, NewsData


class TestNewsClassifier:
    def test_classify_macro(self):
        clf = NewsClassifier()
        tags = clf.classify("央行宣布下调LPR利率，CPI同比上涨0.5%")
        assert "macro" in tags

    def test_classify_policy(self):
        clf = NewsClassifier()
        tags = clf.classify("证监会发布新规，加强上市公司监管")
        assert "policy" in tags

    def test_classify_industry(self):
        clf = NewsClassifier()
        tags = clf.classify("螺纹钢库存大幅下降，钢厂开工率回升")
        assert "industry" in tags

    def test_classify_company(self):
        clf = NewsClassifier()
        tags = clf.classify("某上市公司发布业绩预告，净利润同比增长50%")
        assert "company" in tags

    def test_classify_empty(self):
        clf = NewsClassifier()
        tags = clf.classify("")
        assert tags == []

    def test_classify_item(self):
        clf = NewsClassifier()
        tags = clf.classify_item("GDP增速超预期", "国家统计局发布数据")
        assert "macro" in tags

    def test_extract_symbols(self):
        clf = NewsClassifier()
        symbols = clf.extract_symbols("RB螺纹钢价格上涨，HC热卷跟涨", ["RB", "HC", "CU"])
        assert "RB" in symbols
        assert "HC" in symbols

    def test_custom_keywords(self):
        clf = NewsClassifier(custom_keywords={"weather": ["天气", "降雨", "干旱"]})
        tags = clf.classify("南方持续降雨影响运输")
        assert "weather" in tags


class TestNewsModels:
    def test_news_item(self):
        item = NewsItem(title="测试新闻", content="测试内容")
        assert item.title == "测试新闻"
        assert item.tags == []

    def test_news_data_filter_by_tag(self):
        nd = NewsData(items=[
            NewsItem(title="新闻1", tags=["macro"]),
            NewsItem(title="新闻2", tags=["policy"]),
            NewsItem(title="新闻3", tags=["macro", "industry"]),
        ])
        macro_news = nd.filter_by_tag("macro")
        assert len(macro_news) == 2

    def test_news_data_filter_by_symbol(self):
        nd = NewsData(items=[
            NewsItem(title="新闻1", related_symbols=["RB"]),
            NewsItem(title="新闻2", related_symbols=["CU"]),
        ])
        rb_news = nd.filter_by_symbol("RB")
        assert len(rb_news) == 1
        assert rb_news[0].title == "新闻1"
