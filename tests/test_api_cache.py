"""UnifiedDataProvider 缓存层测试。"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from datacore.models.enums import DataType, MarketType, SourceGrade
from datacore.models.payload import DataPayload


class TestApiCacheLayer:
    def test_cache_params_key_empty(self):
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()
        assert dp._cache_params_key(None) == "default"
        assert dp._cache_params_key({}) == "default"

    def test_cache_params_key_with_params(self):
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()
        key = dp._cache_params_key({"period": "daily", "days": 120})
        assert "period=daily" in key
        assert "days=120" in key

    def test_health_has_cache_info(self):
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()
        health = dp.get_health()
        assert "memory_cache" in health.get("sources", {})
        assert "duckdb_cache" in health.get("sources", {})

    def test_l1_cache_hit(self):
        """测试 MemoryCache 命中路径。"""
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()

        cache_key = dp._cache_params_key({"period": "daily", "days": 120})
        full_key = f"RB:{DataType.OHLCV.value}:{cache_key}"

        # 模拟 MemoryCache 返回已缓存数据
        mock_cache = MagicMock()
        cached_payload = {
            "symbol": "RB",
            "data_type": "ohlcv",
            "market": "futures",
            "source": "cache",
            "grade": "cached",
            "collected_at": 0,
            "errors": [],
            "warnings": [],
            "meta": {},
            "data": None,
        }
        mock_cache.get.return_value = cached_payload
        with patch("datacore.api._get_cache", return_value=mock_cache):
            result = dp._check_cache(full_key)

        assert result is not None
        assert result.grade == SourceGrade.CACHED

    def test_l1_cache_miss_no_data(self):
        """测试 MemoryCache 未命中时返回 None。"""
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()

        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        with patch("datacore.api._get_cache", return_value=mock_cache), \
             patch("datacore.api._get_duckdb", return_value=None):
            result = dp._check_cache("RB:ohlcv:default")

        assert result is None

    def test_get_no_such_symbol(self):
        """未知 symbol 不经过缓存直接返回 UNAVAILABLE。"""
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()
        payload = dp.get("ZZZ", DataType.OHLCV)
        assert not payload.available
        assert payload.grade == SourceGrade.UNAVAILABLE

    def test_get_sentiment_not_cached(self):
        """SENTIMENT 类型不走缓存层。"""
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()
        mock_news = MagicMock()
        mock_news.get.return_value = DataPayload(
            symbol="RB",
            data_type=DataType.NEWS,
            market=MarketType.FUTURES,
            grade=SourceGrade.UNAVAILABLE,
        )

        with patch("datacore.api._get_news", return_value=mock_news):
            payload = dp.get("RB", DataType.SENTIMENT)

        assert not payload.available

    def test_get_market_state_not_cached(self):
        """MARKET_STATE 类型不走缓存层。"""
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()
        mock_futures = MagicMock()
        mock_futures.get.return_value = DataPayload(
            symbol="RB",
            data_type=DataType.OHLCV,
            market=MarketType.FUTURES,
            grade=SourceGrade.UNAVAILABLE,
        )

        with patch("datacore.api._get_futures", return_value=mock_futures), \
             patch("datacore.api._get_cache", return_value=MagicMock()), \
             patch("datacore.api._get_duckdb", return_value=None):
            payload = dp.get("RB", DataType.MARKET_STATE)

        assert not payload.available

    def test_get_news_not_cached(self):
        """NEWS 类型不走缓存层。"""
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()
        mock_news = MagicMock()
        mock_news.get.return_value = DataPayload(
            symbol="RB",
            data_type=DataType.NEWS,
            market=MarketType.FUTURES,
            grade=SourceGrade.UNAVAILABLE,
        )

        with patch("datacore.api._get_news", return_value=mock_news):
            payload = dp.get("RB", DataType.NEWS)

        assert not payload.available

    def test_get_macro_not_cached(self):
        """MACRO 类型不走缓存层。"""
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()
        mock_macro = MagicMock()
        mock_macro.get.return_value = DataPayload(
            symbol="GDP",
            data_type=DataType.MACRO,
            market=MarketType.FUTURES,
            grade=SourceGrade.UNAVAILABLE,
        )

        with patch("datacore.api._get_macro", return_value=mock_macro):
            payload = dp.get("GDP", DataType.MACRO)

        assert not payload.available

    def test_get_caches_result_on_success(self):
        """成功获取数据后写入缓存。"""
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()

        mock_futures = MagicMock()
        mock_futures.get.return_value = DataPayload(
            symbol="RB",
            data_type=DataType.OHLCV,
            market=MarketType.FUTURES,
            grade=SourceGrade.PRIMARY,
            data=[{"close": 4000}],
        )

        mock_cache = MagicMock()

        with (
            patch("datacore.api._get_futures", return_value=mock_futures),
            patch("datacore.api._get_cache", return_value=mock_cache),
            patch("datacore.api._get_duckdb", return_value=None),
        ):
            payload = dp.get("RB", DataType.OHLCV)

        assert payload.available
        assert payload.grade == SourceGrade.PRIMARY
        # 验证缓存被写入
        assert mock_cache.set.called
        args, _ = mock_cache.set.call_args
        assert args[0].startswith("RB:ohlcv:")

    def test_l2_duckdb_fallback(self):
        """测试 DuckDB L2 缓存回退路径（无数据时返回 None）。"""
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()

        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        mock_duckdb = MagicMock()
        mock_duckdb.load_kline.return_value = []

        with (
            patch("datacore.api._get_cache", return_value=mock_cache),
            patch("datacore.api._get_duckdb", return_value=mock_duckdb),
        ):
            result = dp._check_cache("RB:ohlcv:default")

        assert result is None
        mock_duckdb.load_kline.assert_called_once_with("RB", "daily", days=120)

    def test_write_cache_skips_unavailable(self):
        """不可用的 payload 不写入缓存。"""
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()
        mock_cache = MagicMock()

        unavailable = DataPayload(
            symbol="RB",
            data_type=DataType.OHLCV,
            market=MarketType.FUTURES,
            grade=SourceGrade.UNAVAILABLE,
        )

        with patch("datacore.api._get_cache", return_value=mock_cache):
            dp._write_cache("RB:ohlcv:default", unavailable)

        assert not mock_cache.set.called

    def test_check_cache_invalid_payload(self):
        """MemoryCache 返回无效 dict 时静默降级。"""
        from datacore.api import UnifiedDataProvider

        dp = UnifiedDataProvider()

        mock_cache = MagicMock()
        mock_cache.get.return_value = {"bad": "data"}  # 缺少必需字段

        with (
            patch("datacore.api._get_cache", return_value=mock_cache),
            patch("datacore.api._get_duckdb", return_value=None),
        ):
            result = dp._check_cache("RB:ohlcv:default")

        assert result is None
