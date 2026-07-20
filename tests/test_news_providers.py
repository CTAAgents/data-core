"""新闻数据源的 mock 测试。
覆盖正常路径、异常路径、边界情况。
"""


class TestClsProvider:
    """财联社新闻源测试。"""

    def test_fetch_news_success(self, mocker):
        from datacore.news.providers.cls import ClsProvider
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {
            "data": {
                "roll_data": [
                    {"id": "1", "title": "新闻标题1", "content": "内容1", "ctime": "2026-01-01"},
                    {"id": "2", "title": "新闻标题2", "content": "内容2", "ctime": "2026-01-02"},
                ]
            }
        }
        mocker.patch("httpx.Client.get", return_value=mock_resp)
        provider = ClsProvider()
        result = provider.fetch_news(symbol="RB", limit=5)
        assert result is not None
        assert result.total == 2
        assert len(result.items) == 2

    def test_fetch_news_empty(self, mocker):
        from datacore.news.providers.cls import ClsProvider
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"data": {"roll_data": []}}
        mocker.patch("httpx.Client.get", return_value=mock_resp)
        provider = ClsProvider()
        result = provider.fetch_news(symbol="RB", limit=5)
        assert result is None

    def test_fetch_news_http_fail(self, mocker):
        from datacore.news.providers.cls import ClsProvider
        mocker.patch("httpx.Client.get", side_effect=Exception("timeout"))
        provider = ClsProvider()
        result = provider.fetch_news(symbol="RB", limit=5)
        assert result is None

    def test_check_available(self, mocker):
        from datacore.news.providers.cls import ClsProvider
        mock_resp = mocker.Mock()
        mock_resp.status_code = 200
        mocker.patch("httpx.Client.head", return_value=mock_resp)
        provider = ClsProvider()
        assert provider.check_available() is True

    def test_check_available_fail(self, mocker):
        from datacore.news.providers.cls import ClsProvider
        mocker.patch("httpx.Client.head", side_effect=Exception("fail"))
        provider = ClsProvider()
        assert provider.check_available() is False

    def test_fetch_news_partial_fail(self, mocker):
        """部分新闻条目解析失败不应影响其他条目。"""
        from datacore.news.providers.cls import ClsProvider
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {
            "data": {
                "roll_data": [
                    {"id": "1", "title": "有效新闻", "content": "内容", "ctime": "2026-01-01"},
                    None,  # 非法条目，应跳过
                ]
            }
        }
        mocker.patch("httpx.Client.get", return_value=mock_resp)
        provider = ClsProvider()
        result = provider.fetch_news(symbol="RB", limit=5)
        assert result is not None
        assert result.total == 1


class TestWallStreetCnProvider:
    """华尔街见闻新闻源测试。"""

    def test_fetch_news_success(self, mocker):
        from datacore.news.providers.wallstreet_cn import WallStreetCnProvider
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {
            "data": {
                "items": [
                    {"id": 1, "title": "标题", "content_text": "内容1", "display_time": "2026-01-01", "uri": "/detail/1"},
                ]
            }
        }
        mocker.patch("httpx.Client.get", return_value=mock_resp)
        provider = WallStreetCnProvider()
        result = provider.fetch_news(symbol="RB", limit=5)
        assert result is not None
        assert result.total == 1

    def test_fetch_news_empty(self, mocker):
        from datacore.news.providers.wallstreet_cn import WallStreetCnProvider
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"data": {"items": []}}
        mocker.patch("httpx.Client.get", return_value=mock_resp)
        provider = WallStreetCnProvider()
        result = provider.fetch_news(symbol="RB", limit=5)
        assert result is None

    def test_fetch_news_http_fail(self, mocker):
        from datacore.news.providers.wallstreet_cn import WallStreetCnProvider
        mocker.patch("httpx.Client.get", side_effect=Exception("timeout"))
        provider = WallStreetCnProvider()
        result = provider.fetch_news(symbol="RB", limit=5)
        assert result is None

    def test_check_available(self, mocker):
        from datacore.news.providers.wallstreet_cn import WallStreetCnProvider
        mock_resp = mocker.Mock()
        mock_resp.status_code = 200
        mocker.patch("httpx.Client.head", return_value=mock_resp)
        provider = WallStreetCnProvider()
        assert provider.check_available() is True

    def test_fallback_to_title(self, mocker):
        """当 content_text 不存在时，应回退到 title。"""
        from datacore.news.providers.wallstreet_cn import WallStreetCnProvider
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {
            "data": {
                "items": [
                    {"id": 1, "title": "回退标题", "display_time": "2026-01-01", "uri": "/detail/1"},
                ]
            }
        }
        mocker.patch("httpx.Client.get", return_value=mock_resp)
        provider = WallStreetCnProvider()
        result = provider.fetch_news(symbol="RB", limit=5)
        assert result is not None
        assert result.items[0].title == "回退标题"


class TestEastMoneyResearchProvider:
    """东方财富研报源测试。"""

    def test_fetch_news_success(self, mocker):
        from datacore.news.providers.eastmoney_research import EastMoneyResearchProvider
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {
            "data": [
                {"title": "研报标题", "content": "研报内容", "publishDate": "2026-01-01",
                 "orgSName": "中信证券", "encodeUrl": "abc123"},
            ]
        }
        mocker.patch("httpx.Client.get", return_value=mock_resp)
        provider = EastMoneyResearchProvider()
        result = provider.fetch_news(symbol="RB", limit=5)
        assert result is not None
        assert result.total == 1
        assert "中信" in result.items[0].source

    def test_fetch_news_empty(self, mocker):
        from datacore.news.providers.eastmoney_research import EastMoneyResearchProvider
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"data": []}
        mocker.patch("httpx.Client.get", return_value=mock_resp)
        provider = EastMoneyResearchProvider()
        result = provider.fetch_news(symbol="RB", limit=5)
        assert result is None

    def test_fetch_news_http_fail(self, mocker):
        from datacore.news.providers.eastmoney_research import EastMoneyResearchProvider
        mocker.patch("httpx.Client.get", side_effect=Exception("timeout"))
        provider = EastMoneyResearchProvider()
        result = provider.fetch_news(symbol="RB", limit=5)
        assert result is None

    def test_check_available(self, mocker):
        from datacore.news.providers.eastmoney_research import EastMoneyResearchProvider
        mock_resp = mocker.Mock()
        mock_resp.status_code = 200
        mocker.patch("httpx.Client.head", return_value=mock_resp)
        provider = EastMoneyResearchProvider()
        assert provider.check_available() is True

    def test_fallback_to_s3(self, mocker):
        """当 content 不存在时，回退到 s3 字段。"""
        from datacore.news.providers.eastmoney_research import EastMoneyResearchProvider
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {
            "data": [
                {"title": "标题", "s3": "s3内容", "publishDate": "2026-01-01",
                 "orgSName": "华泰证券", "encodeUrl": "abc"},
            ]
        }
        mocker.patch("httpx.Client.get", return_value=mock_resp)
        provider = EastMoneyResearchProvider()
        result = provider.fetch_news(symbol="RB", limit=5)
        assert result is not None
        assert len(result.items) == 1


class TestNewsDataProvider:
    """新闻统一入口测试。"""

    def test_provider_init_sources(self):
        from datacore.news.news_provider import NewsDataProvider
        provider = NewsDataProvider()
        assert len(provider.sources) > 0

    def test_get_no_symbol(self, mocker):
        from datacore.news.news_provider import NewsDataProvider
        provider = NewsDataProvider()
        # Mock 所有源的 fetch_news 返回 None
        for src in provider.sources:
            src.fetch_news = mocker.Mock(return_value=None)
            src.check_available = mocker.Mock(return_value=True)
        result = provider.get(symbol=None, params={"days": 1})
        assert result is not None
        assert result.grade == "unavailable"

    def test_classifier_tags_applied(self, mocker):
        from datacore.news.news_provider import NewsDataProvider
        from datacore.news.models import NewsData, NewsItem
        provider = NewsDataProvider()
        # 模拟一个返回数据的源
        mock_news = NewsData(symbol="RB", total=1, items=[
            NewsItem(title="央行下调LPR利率", content="宏观政策", source="cls",
                    published_at="2026-01-01", tags=[], related_symbols=[]),
        ])
        for src in provider.sources:
            src.fetch_news = mocker.Mock(return_value=mock_news)
            src.check_available = mocker.Mock(return_value=True)
        result = provider.get(symbol="RB", params={"days": 1})
        assert result is not None
        assert result.available
        assert len(result.data.items) > 0
