from __future__ import annotations

import os
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd

from datacore import UnifiedDataProvider
from datacore.api import _get_breaker, _get_duckdb, _dataframe_to_bars, _kline_to_dataframe
from datacore.config import DataCoreConfig
from datacore.models.enums import DataType, MarketType, SourceGrade
from datacore.models.ohlcv import KBar, KlineData
from datacore.models.payload import DataPayload


class TestUnifiedDataProvider:
    def test_init(self):
        dc = UnifiedDataProvider()
        assert dc.registry is not None

    def test_list_symbols(self):
        dc = UnifiedDataProvider()
        assert len(dc.list_symbols()) > 0

    def test_unknown_symbol(self):
        dc = UnifiedDataProvider()
        p = dc.get('ZZZ', DataType.OHLCV)
        assert not p.available
        assert p.grade == SourceGrade.UNAVAILABLE

    def test_get_batch(self):
        dc = UnifiedDataProvider()
        r = dc.get_batch(['RB', 'CU'], DataType.OHLCV)
        assert len(r) == 2

    # ──────────── api.py 模块级懒加载函数测试 ────────────

    def test_get_futures_lazy_init(self):
        import datacore.api as api_module
        with patch('datacore.api._futures_provider', None), \
             patch('datacore.futures.FuturesDataProvider') as mock_cls:
            provider = api_module._get_futures()
            mock_cls.assert_called_once()
            assert provider == mock_cls.return_value

    def test_get_equity_lazy_init(self):
        import datacore.api as api_module
        with patch('datacore.api._equity_provider', None), \
             patch('datacore.equity.EquityDataProvider') as mock_cls:
            provider = api_module._get_equity()
            mock_cls.assert_called_once()
            assert provider == mock_cls.return_value

    def test_get_news_lazy_init(self):
        import datacore.api as api_module
        with patch('datacore.api._news_provider', None), \
             patch('datacore.news.NewsDataProvider') as mock_cls:
            provider = api_module._get_news()
            mock_cls.assert_called_once()
            assert provider == mock_cls.return_value

    def test_get_macro_lazy_init(self):
        import datacore.api as api_module
        with patch('datacore.api._macro_provider', None), \
             patch('datacore.macro.MacroDataProvider') as mock_cls:
            provider = api_module._get_macro()
            mock_cls.assert_called_once()
            assert provider == mock_cls.return_value

    def test_get_sentiment_llm_lazy_init(self):
        import datacore.api as api_module
        with patch('datacore.api._sentiment_llm', None), \
             patch('datacore.processing.sentiment.sentiment_llm.SentimentLLMStage') as mock_cls:
            provider = api_module._get_sentiment_llm()
            mock_cls.assert_called_once_with(fallback_to_rule=True)
            assert provider == mock_cls.return_value

    def test_get_sentiment_aggregator_lazy_init(self):
        import datacore.api as api_module
        with patch('datacore.api._sentiment_aggregator', None), \
             patch('datacore.processing.sentiment.sentiment_aggregator.SentimentAggregator') as mock_cls:
            provider = api_module._get_sentiment_aggregator()
            mock_cls.assert_called_once()
            assert provider == mock_cls.return_value

    def test_get_market_regime_lazy_init(self):
        import datacore.api as api_module
        with patch('datacore.api._market_regime', None), \
             patch('datacore.processing.market_regime.MarketRegimeDetector') as mock_cls:
            provider = api_module._get_market_regime()
            mock_cls.assert_called_once()
            assert provider == mock_cls.return_value

    # ──────────── 市场行情路由测试 ────────────

    def test_get_futures_route(self):
        """路由到期货市场时返回正确结果"""
        mock_futures = MagicMock()
        mock_futures.get.return_value = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=[{'close': 4000}],
        )
        with patch('datacore.api._get_futures', return_value=mock_futures):
            dc = UnifiedDataProvider()
            with patch.object(dc, '_check_cache', return_value=None):
                payload = dc.get('RB', DataType.OHLCV)
            assert payload.available
            assert payload.data == [{'close': 4000}]

    def test_get_equity_route(self):
        """路由到股票市场时返回正确结果"""
        mock_equity = MagicMock()
        mock_equity.get.return_value = DataPayload(
            symbol='600519', data_type=DataType.OHLCV,
            market=MarketType.STOCK, grade=SourceGrade.PRIMARY,
            data=[{'close': 1800}],
        )
        with patch('datacore.api._get_equity', return_value=mock_equity):
            dc = UnifiedDataProvider()
            with patch.object(dc.registry, 'resolve_market', return_value=MarketType.STOCK):
                payload = dc.get('600519', DataType.OHLCV)
            assert payload.available
            assert payload.data == [{'close': 1800}]

    def test_get_futures_payload_none(self):
        """provider 返回 None 时返回 UNAVAILABLE"""
        mock_futures = MagicMock()
        mock_futures.get.return_value = None
        with patch('datacore.api._get_futures', return_value=mock_futures), \
             patch('datacore.api._get_cache', return_value=MagicMock()), \
             patch('datacore.api._get_duckdb', return_value=None):
            dc = UnifiedDataProvider()
            payload = dc.get('RB', DataType.OHLCV)
            assert not payload.available
            assert 'does not support' in payload.errors[0]

    # ──────────── NEWS 路由测试 ────────────

    def test_get_news_data_success(self):
        mock_news = MagicMock()
        mock_news.get.return_value = DataPayload(
            symbol='RB', data_type=DataType.NEWS,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=[{'title': 'news1'}],
        )
        with patch('datacore.api._get_news', return_value=mock_news):
            dc = UnifiedDataProvider()
            payload = dc.get('RB', DataType.NEWS)
            assert payload.available
            assert payload.data == [{'title': 'news1'}]

    def test_get_news_data_none(self):
        mock_news = MagicMock()
        mock_news.get.return_value = None
        with patch('datacore.api._get_news', return_value=mock_news):
            dc = UnifiedDataProvider()
            payload = dc.get('RB', DataType.NEWS)
            assert not payload.available
            assert 'news provider returned None' in payload.errors[0]

    def test_get_news_data_exception(self):
        with patch('datacore.api._get_news', side_effect=Exception('http error')):
            dc = UnifiedDataProvider()
            payload = dc.get('RB', DataType.NEWS)
            assert not payload.available
            assert 'news fetch error' in payload.errors[0]

    # ──────────── MACRO 路由测试 ────────────

    def test_get_macro_data_success(self):
        mock_macro = MagicMock()
        mock_macro.get.return_value = DataPayload(
            symbol='GDP', data_type=DataType.MACRO,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data={'gdp': 5.5},
        )
        with patch('datacore.api._get_macro', return_value=mock_macro):
            dc = UnifiedDataProvider()
            payload = dc.get('GDP', DataType.MACRO, {'indicator': 'gdp'})
            assert payload.available
            assert payload.data == {'gdp': 5.5}
            mock_macro.get.assert_called_once_with(indicator='gdp', params={'indicator': 'gdp'})

    def test_get_macro_data_none(self):
        mock_macro = MagicMock()
        mock_macro.get.return_value = None
        with patch('datacore.api._get_macro', return_value=mock_macro):
            dc = UnifiedDataProvider()
            payload = dc.get('GDP', DataType.MACRO)
            assert not payload.available
            assert 'macro provider returned None' in payload.errors[0]

    def test_get_macro_data_exception(self):
        with patch('datacore.api._get_macro', side_effect=Exception('db error')):
            dc = UnifiedDataProvider()
            payload = dc.get('GDP', DataType.MACRO)
            assert not payload.available
            assert 'macro fetch error' in payload.errors[0]

    # ──────────── SENTIMENT 管线测试 ────────────

    def test_get_sentiment_full_llm(self):
        """LLM 打分 + 聚合 完整流程"""
        mock_news = MagicMock()
        mock_news.get.return_value = DataPayload(
            symbol='RB', data_type=DataType.NEWS,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=[{'title': 'n1', 'content': 'good'}, {'title': 'n2', 'content': 'bad'}],
        )

        mock_scorer = MagicMock()
        mock_scorer.process.side_effect = [
            {'score': 0.8, 'text': 'positive'},
            {'score': 0.2, 'text': 'negative'},
        ]
        mock_scorer.check_available.return_value = True

        mock_aggregator = MagicMock()
        mock_aggregator.aggregate.return_value = {'avg_score': 0.5, 'count': 2}

        with patch('datacore.api._get_news', return_value=mock_news), \
             patch('datacore.api._get_sentiment_llm', return_value=mock_scorer), \
             patch('datacore.api._get_sentiment_aggregator', return_value=mock_aggregator):

            dc = UnifiedDataProvider()
            payload = dc.get('RB', DataType.SENTIMENT)

            assert payload.available
            assert payload.data == {'avg_score': 0.5, 'count': 2}
            assert payload.source == 'llm'
            assert payload.grade == SourceGrade.PRIMARY
            assert mock_scorer.process.call_count == 2
            mock_aggregator.aggregate.assert_called_once()

    def test_get_sentiment_rule_fallback(self):
        """LLM 不可用时降级到规则基线"""
        mock_news = MagicMock()
        mock_news.get.return_value = DataPayload(
            symbol='RB', data_type=DataType.NEWS,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=[{'title': 'test'}],
        )

        mock_scorer = MagicMock()
        mock_scorer.process.return_value = {'score': 0.3}
        mock_scorer.check_available.return_value = False  # LLM 不可用

        mock_aggregator = MagicMock()
        mock_aggregator.aggregate.return_value = {'score': 0.3}

        with patch('datacore.api._get_news', return_value=mock_news), \
             patch('datacore.api._get_sentiment_llm', return_value=mock_scorer), \
             patch('datacore.api._get_sentiment_aggregator', return_value=mock_aggregator):

            dc = UnifiedDataProvider()
            payload = dc.get('RB', DataType.SENTIMENT)

            assert payload.available
            assert payload.source == 'rule_fallback'
            assert payload.grade == SourceGrade.DAILY

    def test_get_sentiment_no_news(self):
        """新闻不可用时返回 UNAVAILABLE"""
        mock_news = MagicMock()
        mock_news.get.return_value = DataPayload(
            symbol='RB', data_type=DataType.NEWS,
            market=MarketType.FUTURES, grade=SourceGrade.UNAVAILABLE,
        )

        with patch('datacore.api._get_news', return_value=mock_news):
            dc = UnifiedDataProvider()
            payload = dc.get('RB', DataType.SENTIMENT)

            assert not payload.available
            assert 'no news data for sentiment' in payload.errors[0]

    def test_get_sentiment_no_items(self):
        """新闻列表包含非 dict 元素时无情绪项产生"""
        mock_news = MagicMock()
        mock_news.get.return_value = DataPayload(
            symbol='RB', data_type=DataType.NEWS,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=['string_item'],  # 非 dict → isinstnace(dict) 为 False
        )

        with patch('datacore.api._get_news', return_value=mock_news), \
             patch('datacore.api._get_sentiment_llm', return_value=MagicMock()), \
             patch('datacore.api._get_sentiment_aggregator', return_value=MagicMock()):

            dc = UnifiedDataProvider()
            payload = dc.get('RB', DataType.SENTIMENT)

            assert not payload.available
            assert 'no sentiment items produced' in payload.errors[0]

    def test_get_sentiment_exception(self):
        """情感管道异常时返回 UNAVAILABLE"""
        with patch('datacore.api._get_news', side_effect=RuntimeError('unexpected')):
            dc = UnifiedDataProvider()
            payload = dc.get('RB', DataType.SENTIMENT)

            assert not payload.available
            assert 'sentiment error' in payload.errors[0]

    # ──────────── MARKET_STATE 管线测试 ────────────

    def test_get_market_state_full(self):
        """OHLCV → 市场制度检测 完整流程"""
        mock_futures = MagicMock()
        mock_futures.get.return_value = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=[{'close': 4000, 'high': 4050, 'low': 3950}],
        )

        mock_detector = MagicMock()
        mock_detector.process.return_value = {'regime': 'bull', 'confidence': 0.85}

        with patch('datacore.api._get_futures', return_value=mock_futures), \
             patch('datacore.api._get_market_regime', return_value=mock_detector):

            dc = UnifiedDataProvider()
            payload = dc.get('RB', DataType.MARKET_STATE)

            assert payload.available
            assert payload.data == {'regime': 'bull', 'confidence': 0.85}
            assert payload.source == 'market_regime'
            assert payload.grade == SourceGrade.PRIMARY
            mock_detector.process.assert_called_once()

    def test_get_market_state_no_ohlcv(self):
        """OHLCV 不可用时返回 UNAVAILABLE"""
        mock_futures = MagicMock()
        mock_futures.get.return_value = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.UNAVAILABLE,
        )

        with patch('datacore.api._get_futures', return_value=mock_futures), \
             patch('datacore.api._get_cache', return_value=MagicMock()), \
             patch('datacore.api._get_duckdb', return_value=None):
            dc = UnifiedDataProvider()
            payload = dc.get('RB', DataType.MARKET_STATE)

            assert not payload.available
            assert 'no OHLCV data for market regime' in payload.errors[0]

    def test_get_market_state_exception(self):
        """市场制度管道异常时返回 UNAVAILABLE"""
        with patch('datacore.api._get_futures', side_effect=ValueError('bad data')), \
             patch('datacore.api._get_cache', return_value=MagicMock()), \
             patch('datacore.api._get_duckdb', return_value=None):
            dc = UnifiedDataProvider()
            payload = dc.get('RB', DataType.MARKET_STATE)

            assert not payload.available
            assert 'market regime error' in payload.errors[0]

    # ──────────── get_batch / list_symbols ────────────

    def test_list_symbols_by_market(self):
        dc = UnifiedDataProvider()
        result = dc.list_symbols(market=MarketType.FUTURES)
        assert len(result) > 0
        assert all(item['market'] == 'futures' for item in result)

    def test_list_symbols_by_market_etf(self):
        dc = UnifiedDataProvider()
        result = dc.list_symbols(market=MarketType.ETF)
        assert isinstance(result, list)

    # ──────────── get_health 健康检查 ────────────

    def test_get_health(self):
        """基本健康检查返回格式正确。"""
        dc = UnifiedDataProvider()
        mock_source = MagicMock()
        mock_source.check_available.return_value = True
        mock_provider = MagicMock()
        mock_provider.sources = [mock_source]

        with (
            patch("datacore.api._get_futures", return_value=mock_provider),
            patch("datacore.api._get_equity", return_value=mock_provider),
            patch("datacore.api._get_news", return_value=mock_provider),
            patch("datacore.api._get_macro", return_value=mock_provider),
        ):
            result = dc.get_health()
            assert isinstance(result, dict)
            assert "status" in result
            assert "version" in result
            assert "sources" in result
            assert "timestamp" in result

    def test_get_health_sources(self):
        """健康检查包含各数据源探测结果。"""
        dc = UnifiedDataProvider()
        src_a = MagicMock()
        src_a.check_available.return_value = True
        src_a.name = "tdx_lc"
        src_b = MagicMock()
        src_b.check_available.return_value = False
        src_b.name = "guosen"

        futures_provider = MagicMock()
        futures_provider.sources = [src_a, src_b]
        others = MagicMock()
        others.sources = []

        with (
            patch("datacore.api._get_futures", return_value=futures_provider),
            patch("datacore.api._get_equity", return_value=others),
            patch("datacore.api._get_news", return_value=others),
            patch("datacore.api._get_macro", return_value=others),
        ):
            result = dc.get_health()
            sources = result["sources"]
            assert "tdx_lc" in sources
            assert "guosen" in sources
            assert sources["tdx_lc"]["available"] is True
            assert sources["guosen"]["available"] is False
            assert "latency_ms" in sources["tdx_lc"]

    def test_get_health_version(self):
        """健康检查包含版本信息。"""
        dc = UnifiedDataProvider()
        mock_source = MagicMock()
        mock_source.check_available.return_value = True
        mock_provider = MagicMock()
        mock_provider.sources = [mock_source]

        with (
            patch("datacore.api._get_futures", return_value=mock_provider),
            patch("datacore.api._get_equity", return_value=mock_provider),
            patch("datacore.api._get_news", return_value=mock_provider),
            patch("datacore.api._get_macro", return_value=mock_provider),
        ):
            result = dc.get_health()
            assert result["version"] == "2.3.0"

    def test_get_health_status(self):
        """全源可用时返回 healthy。"""
        dc = UnifiedDataProvider()
        src = MagicMock()
        src.check_available.return_value = True
        mock_provider = MagicMock()
        mock_provider.sources = [src]

        with (
            patch("datacore.api._get_futures", return_value=mock_provider),
            patch("datacore.api._get_equity", return_value=mock_provider),
            patch("datacore.api._get_news", return_value=mock_provider),
            patch("datacore.api._get_macro", return_value=mock_provider),
        ):
            result = dc.get_health()
            assert result["status"] == "healthy"

    def test_get_health_degraded(self):
        """部分源不可用时返回 healthy（任一源可用即算健康）。"""
        dc = UnifiedDataProvider()
        good_src = MagicMock()
        good_src.check_available.return_value = True
        bad_src = MagicMock()
        bad_src.check_available.return_value = False

        futures_provider = MagicMock()
        futures_provider.sources = [bad_src]
        equity_provider = MagicMock()
        equity_provider.sources = [good_src]
        empty = MagicMock()
        empty.sources = []

        with (
            patch("datacore.api._get_futures", return_value=futures_provider),
            patch("datacore.api._get_equity", return_value=equity_provider),
            patch("datacore.api._get_news", return_value=empty),
            patch("datacore.api._get_macro", return_value=empty),
        ):
            result = dc.get_health()
            assert result["status"] == "healthy"
            # 仅 equity 模块返回 available=True
            assert any(v["available"] for v in result["sources"].values())


    # ──────────── 模块级懒加载与降级 ────────────

    def test_get_breaker_lazy_init(self):
        """_get_breaker 懒加载创建 Breaker 并缓存"""
        with patch('datacore.api._breaker_pool', {}), \
             patch('datacore.breaker.Breaker') as mock_cls:
            breaker = _get_breaker('test_breaker')
            mock_cls.assert_called_once_with('test_breaker')
            assert breaker == mock_cls.return_value

    def test_get_breaker_reuse(self):
        """_get_breaker 对同一 name 复用已有实例"""
        existing = MagicMock()
        with patch('datacore.api._breaker_pool', {'reuse_breaker': existing}), \
             patch('datacore.breaker.Breaker') as mock_cls:
            breaker = _get_breaker('reuse_breaker')
            assert breaker is existing
            mock_cls.assert_not_called()

    def test_get_duckdb_import_failure(self):
        """duckdb 导入失败时 _get_duckdb 返回 None"""
        with patch('datacore.api._duckdb_store', None), \
             patch('datacore.store.duckdb.DuckDBStore', side_effect=ImportError('no duckdb')):
            store = _get_duckdb()
            assert store is None

    # ──────────── OHLCV 自动周期转换 ────────────

    def test_maybe_resample_ohlcv_success(self):
        """请求更粗周期时成功重采样为 KlineData"""
        bars = [
            KBar(date='2024-01-01 09:30:00', open=1.0, high=2.0, low=0.5, close=1.5, volume=100, amount=1000),
            KBar(date='2024-01-01 09:31:00', open=1.5, high=2.5, low=1.0, close=2.0, volume=200, amount=2000),
            KBar(date='2024-01-01 09:32:00', open=2.0, high=3.0, low=1.5, close=2.5, volume=150, amount=1500),
            KBar(date='2024-01-01 09:33:00', open=2.5, high=3.5, low=2.0, close=3.0, volume=120, amount=1200),
            KBar(date='2024-01-01 09:34:00', open=3.0, high=4.0, low=2.5, close=3.5, volume=130, amount=1300),
        ]
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=KlineData(symbol='RB', period='1m', bars=bars, source='test'),
        )

        dc = UnifiedDataProvider()
        result = dc._maybe_resample_ohlcv(payload, {'period': '5m'})

        assert result.available
        assert result.data is not None
        assert isinstance(result.data, KlineData)
        assert result.data.period == '5m'
        assert len(result.data.bars) == 1
        assert result.meta.get('resampled_from') == '1m'
        assert any('重采样' in w for w in result.warnings)

    def test_maybe_resample_ohlcv_exception_fallback(self):
        """重采样异常时降级返回原始 payload"""
        bars = [KBar(date='2024-01-01 09:30:00', open=1.0, high=2.0, low=0.5, close=1.5, volume=100)]
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=KlineData(symbol='RB', period='1m', bars=bars, source='test'),
        )

        with patch('datacore.resampler.ohlcv.resample_ohlcv', side_effect=RuntimeError('resample fail')):
            dc = UnifiedDataProvider()
            result = dc._maybe_resample_ohlcv(payload, {'period': '5m'})

        assert result is payload

    def test_maybe_resample_ohlcv_invalid_target_period(self):
        """非法目标周期直接返回原始 payload"""
        bars = [KBar(date='2024-01-01', open=1.0, high=2.0, low=0.5, close=1.5, volume=100)]
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=KlineData(symbol='RB', period='daily', bars=bars, source='test'),
        )
        dc = UnifiedDataProvider()
        result = dc._maybe_resample_ohlcv(payload, {'period': 'invalid'})
        assert result is payload

    def test_maybe_resample_ohlcv_no_source_period(self):
        """无法推断源周期时直接返回原始 payload"""
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data={'close': 1.0},
        )
        dc = UnifiedDataProvider()
        result = dc._maybe_resample_ohlcv(payload, {'period': '5m'})
        assert result is payload

    def test_maybe_resample_ohlcv_not_finer(self):
        """源周期不比目标周期更细时直接返回原始 payload"""
        bars = [KBar(date='2024-01-01', open=1.0, high=2.0, low=0.5, close=1.5, volume=100)]
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=KlineData(symbol='RB', period='daily', bars=bars, source='test'),
        )
        dc = UnifiedDataProvider()
        result = dc._maybe_resample_ohlcv(payload, {'period': '1m'})
        assert result is payload

    def test_maybe_resample_ohlcv_empty_dataframe(self):
        """payload 转换为空 DataFrame 时直接返回原始 payload"""
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=KlineData(symbol='RB', period='1m', bars=[], source='test'),
        )
        dc = UnifiedDataProvider()
        result = dc._maybe_resample_ohlcv(payload, {'period': '5m'})
        assert result is payload

    def test_maybe_resample_ohlcv_empty_resampled(self):
        """重采样结果为空时直接返回原始 payload"""
        bars = [KBar(date='2024-01-01 09:30:00', open=1.0, high=2.0, low=0.5, close=1.5, volume=100)]
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=KlineData(symbol='RB', period='1m', bars=bars, source='test'),
        )
        with patch('datacore.resampler.ohlcv.resample_ohlcv', return_value=pd.DataFrame()):
            dc = UnifiedDataProvider()
            result = dc._maybe_resample_ohlcv(payload, {'period': '5m'})
        assert result is payload

    def test_maybe_resample_ohlcv_is_finer_value_error(self):
        """is_finer 抛出 ValueError 时降级返回原始 payload"""
        bars = [KBar(date='2024-01-01', open=1.0, high=2.0, low=0.5, close=1.5, volume=100)]
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=KlineData(symbol='RB', period='daily', bars=bars, source='test'),
        )
        with patch('datacore.resampler.registry.is_finer', side_effect=ValueError('invalid')):
            dc = UnifiedDataProvider()
            result = dc._maybe_resample_ohlcv(payload, {'period': '5m'})
        assert result is payload

    def test_detect_source_period_kline_period(self):
        """KlineData.period 存在时直接返回"""
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES,
            data=KlineData(symbol='RB', period='5m', bars=[], source='test'),
        )
        assert UnifiedDataProvider._detect_source_period(payload) == '5m'

    def test_detect_source_period_dataframe(self):
        """DataFrame 数据通过 auto.infer_source_period 推断"""
        df = pd.DataFrame({
            'open': [1.0, 2.0],
            'high': [2.0, 3.0],
            'low': [0.5, 1.5],
            'close': [1.5, 2.5],
        }, index=pd.to_datetime(['2024-01-01 09:30:00', '2024-01-01 09:31:00']))
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES,
            data=df,
        )
        assert UnifiedDataProvider._detect_source_period(payload) == '1m'

    def test_detect_source_period_kline_bars(self):
        """KlineData 无 period 时从 bars 推断"""
        bars = [
            KBar(date='2024-01-01 09:30:00', open=1.0, high=2.0, low=0.5, close=1.5, volume=100),
            KBar(date='2024-01-01 09:31:00', open=1.5, high=2.5, low=1.0, close=2.0, volume=200),
        ]
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES,
            data=KlineData(symbol='RB', period='', bars=bars, source='test'),
        )
        assert UnifiedDataProvider._detect_source_period(payload) == '1m'

    def test_detect_source_period_unsupported(self):
        """无法识别数据源周期时返回 None"""
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES,
            data={'close': 1.0},
        )
        assert UnifiedDataProvider._detect_source_period(payload) is None

    def test_payload_to_dataframe_kline(self):
        """KlineData 转换为 DataFrame"""
        bars = [
            KBar(date='2024-01-01', open=1.0, high=2.0, low=0.5, close=1.5, volume=100),
        ]
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES,
            data=KlineData(symbol='RB', period='daily', bars=bars, source='test'),
        )
        df = UnifiedDataProvider._payload_to_dataframe(payload)
        assert isinstance(df, pd.DataFrame)
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.name == 'date'
        assert df.loc['2024-01-01', 'close'] == 1.5

    def test_payload_to_dataframe_dataframe_datetime_index(self):
        """已有 DatetimeIndex 的 DataFrame 直接复制"""
        df = pd.DataFrame({'close': [1.0, 2.0]}, index=pd.to_datetime(['2024-01-01', '2024-01-02']))
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES,
            data=df,
        )
        result = UnifiedDataProvider._payload_to_dataframe(payload)
        assert isinstance(result, pd.DataFrame)
        assert isinstance(result.index, pd.DatetimeIndex)
        assert result is not df

    def test_payload_to_dataframe_dataframe_date_column(self):
        """含 date 列的 DataFrame 转换为 DatetimeIndex"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'close': [1.0, 2.0],
        })
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES,
            data=df,
        )
        result = UnifiedDataProvider._payload_to_dataframe(payload)
        assert isinstance(result, pd.DataFrame)
        assert isinstance(result.index, pd.DatetimeIndex)
        assert 'date' not in result.columns
        assert result.index.name == 'date'

    def test_payload_to_dataframe_invalid(self):
        """无法转换的 DataFrame 返回 None"""
        df = pd.DataFrame({'close': [1.0, 2.0]})
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES,
            data=df,
        )
        assert UnifiedDataProvider._payload_to_dataframe(payload) is None

    def test_payload_to_dataframe_unsupported_data(self):
        """不支持的数据类型返回 None"""
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES,
            data=[{'close': 1.0}],
        )
        assert UnifiedDataProvider._payload_to_dataframe(payload) is None

    def test_dataframe_to_payload_kline(self):
        """原始数据为 KlineData 时回包仍为 KlineData"""
        bars = [KBar(date='2024-01-01', open=1.0, high=2.0, low=0.5, close=1.5, volume=100)]
        original = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=KlineData(symbol='RB', period='1m', bars=bars, source='test', contract='main'),
            meta={'key': 'value'}, errors=[], warnings=['orig'],
        )
        df = pd.DataFrame({
            'open': [1.0], 'high': [2.0], 'low': [0.5], 'close': [1.5], 'volume': [100],
        }, index=pd.to_datetime(['2024-01-01']))
        result = UnifiedDataProvider._dataframe_to_payload(df, original, '5m')
        assert isinstance(result.data, KlineData)
        assert result.data.period == '5m'
        assert result.data.source == 'test'
        assert result.data.contract == 'main'
        assert result.meta == {'key': 'value'}
        assert 'orig' in result.warnings

    def test_dataframe_to_payload_dataframe(self):
        """原始数据为 DataFrame 时回包为 DataFrame"""
        original = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=pd.DataFrame({'close': [1.0, 2.0]}),
            meta={'key': 'value'}, errors=[], warnings=['orig'],
        )
        df = pd.DataFrame({
            'open': [1.0, 2.0], 'high': [2.0, 3.0], 'low': [0.5, 1.5], 'close': [1.5, 2.5],
        }, index=pd.to_datetime(['2024-01-01', '2024-01-02']))
        result = UnifiedDataProvider._dataframe_to_payload(df, original, 'daily')
        assert isinstance(result.data, pd.DataFrame)
        assert 'date' in result.data.columns
        assert result.meta == {'key': 'value'}
        assert 'orig' in result.warnings

    # ──────────── 缓存层 ────────────

    def test_check_cache_duckdb(self):
        """DuckDB 缓存命中时构建 KlineData 返回"""
        rows = [
            {'date': '2024-01-01', 'open': 1.0, 'high': 2.0, 'low': 0.5, 'close': 1.5, 'volume': 100, 'amount': 1000},
            {'date': '2024-01-02', 'open': 1.5, 'high': 2.5, 'low': 1.0, 'close': 2.0, 'volume': 200, 'amount': 2000},
        ]
        mock_db = MagicMock()
        mock_db.load_kline.return_value = rows
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch('datacore.api._get_cache', return_value=mock_cache), \
             patch('datacore.api._get_duckdb', return_value=mock_db):
            dc = UnifiedDataProvider()
            result = dc._check_cache('RB:ohlcv:period=daily')

        assert result is not None
        assert result.available
        assert result.grade == SourceGrade.CACHED
        assert isinstance(result.data, KlineData)
        assert len(result.data.bars) == 2
        assert result.data.bars[0].close == 1.5
        mock_db.load_kline.assert_called_once_with('RB', 'daily', days=120)

    def test_write_cache_duckdb(self):
        """可用 OHLCV KlineData 写入 DuckDB"""
        bars = [KBar(date='2024-01-01', open=1.0, high=2.0, low=0.5, close=1.5, volume=100)]
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=KlineData(symbol='RB', period='daily', bars=bars, source='test'),
        )
        mock_db = MagicMock()
        mock_cache = MagicMock()

        with patch('datacore.api._get_cache', return_value=mock_cache), \
             patch('datacore.api._get_duckdb', return_value=mock_db):
            dc = UnifiedDataProvider()
            dc._write_cache('RB:ohlcv:period=daily', payload)

        mock_cache.set.assert_called_once()
        mock_db.store_kline.assert_called_once_with(
            'RB', 'daily', [{'date': '2024-01-01', 'open': 1.0, 'high': 2.0, 'low': 0.5, 'close': 1.5, 'volume': 100.0, 'amount': 0.0, 'open_interest': 0.0, 'settlement': 0.0}]
        )

    def test_check_cache_duckdb_exception(self):
        """DuckDB 缓存读取异常时优雅降级"""
        mock_db = MagicMock()
        mock_db.load_kline.side_effect = RuntimeError('db fail')
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch('datacore.api._get_cache', return_value=mock_cache), \
             patch('datacore.api._get_duckdb', return_value=mock_db):
            dc = UnifiedDataProvider()
            result = dc._check_cache('RB:ohlcv:period=daily')

        assert result is None

    def test_write_cache_duckdb_exception(self):
        """DuckDB 缓存写入异常时不抛出"""
        bars = [KBar(date='2024-01-01', open=1.0, high=2.0, low=0.5, close=1.5, volume=100)]
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.PRIMARY,
            data=KlineData(symbol='RB', period='daily', bars=bars, source='test'),
        )
        mock_db = MagicMock()
        mock_db.store_kline.side_effect = RuntimeError('db fail')
        mock_cache = MagicMock()

        with patch('datacore.api._get_cache', return_value=mock_cache), \
             patch('datacore.api._get_duckdb', return_value=mock_db):
            dc = UnifiedDataProvider()
            dc._write_cache('RB:ohlcv:period=daily', payload)

        mock_cache.set.assert_called_once()
        mock_db.store_kline.assert_called_once()

    # ──────────── 数据源探测 ────────────

    def test_probe_source_check_exception(self):
        """source.check_available 异常时返回不可用"""
        source = MagicMock()
        source.name = 'bad_src'
        source.check_available.side_effect = RuntimeError('check fail')

        with patch('datacore.api.update_source_availability') as mock_metric:
            result = UnifiedDataProvider._probe_source(source)

        assert result['available'] is False
        assert 'latency_ms' in result
        mock_metric.assert_called_once_with('bad_src', False)

    def test_probe_source_update_availability_exception(self):
        """更新可用性指标异常时不影响结果"""
        source = MagicMock()
        source.name = 'good_src'
        source.check_available.return_value = True

        with patch('datacore.api.update_source_availability', side_effect=RuntimeError('metric fail')):
            result = UnifiedDataProvider._probe_source(source)

        assert result['available'] is True
        assert 'latency_ms' in result

    def test_probe_source_no_name(self):
        """source 无 name 时不调用指标更新"""
        source = MagicMock()
        source.name = ''
        source.check_available.return_value = True

        with patch('datacore.api.update_source_availability') as mock_metric:
            result = UnifiedDataProvider._probe_source(source)

        assert result['available'] is True
        mock_metric.assert_not_called()

    # ──────────── 模块级 K 线转换辅助函数 ────────────

    def test_kline_to_dataframe_full_fields(self):
        """_kline_to_dataframe 转换全部字段"""
        bars = [
            KBar(date='2024-01-01', open=1.0, high=2.0, low=0.5, close=1.5,
                 volume=100, amount=1000, open_interest=500.0, settlement=1.6),
            KBar(date='2024-01-02', open=1.5, high=2.5, low=1.0, close=2.0,
                 volume=200, amount=2000, open_interest=600.0, settlement=2.1),
        ]
        kline = KlineData(symbol='RB', period='daily', bars=bars, source='test')
        df = _kline_to_dataframe(kline)

        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.name == 'date'
        assert list(df.columns) == ['open', 'high', 'low', 'close', 'volume', 'amount', 'open_interest', 'settlement']
        assert df.loc['2024-01-01', 'settlement'] == 1.6
        assert df.loc['2024-01-02', 'open_interest'] == 600.0

    def test_kline_to_dataframe_empty(self):
        """空 bars 时返回空 DataFrame 并保留完整列"""
        kline = KlineData(symbol='RB', period='daily', bars=[], source='test')
        df = _kline_to_dataframe(kline)

        assert df.empty
        assert isinstance(df.index, pd.DatetimeIndex)
        assert list(df.columns) == ['open', 'high', 'low', 'close', 'volume', 'amount', 'open_interest', 'settlement']

    def test_dataframe_to_bars_full_fields(self):
        """_dataframe_to_bars 转换全部字段并处理可选字段"""
        df = pd.DataFrame({
            'open': [1.0, 2.0],
            'high': [2.0, 3.0],
            'low': [0.5, 1.5],
            'close': [1.5, 2.5],
            'volume': [100.0, 200.0],
            'amount': [1000.0, 2000.0],
            'open_interest': [500.0, 0.0],
            'settlement': [0.0, 2.1],
        }, index=pd.to_datetime(['2024-01-01', '2024-01-02']))
        bars = _dataframe_to_bars(df)

        assert len(bars) == 2
        assert bars[0].date == '2024-01-01 00:00:00'
        assert bars[0].open_interest == 500.0
        assert bars[0].settlement == 0.0
        assert bars[1].open_interest == 0.0
        assert bars[1].settlement == 2.1

    def test_dataframe_to_bars_optional_defaults(self):
        """_dataframe_to_bars 对缺失的可选字段使用默认值"""
        df = pd.DataFrame({
            'open': [1.0],
            'high': [2.0],
            'low': [0.5],
            'close': [1.5],
        }, index=pd.to_datetime(['2024-01-01']))
        bars = _dataframe_to_bars(df)

        assert len(bars) == 1
        assert bars[0].volume == 0.0
        assert bars[0].amount == 0.0
        assert bars[0].open_interest == 0.0
        assert bars[0].settlement == 0.0

    def test_cache_params_key_with_params(self):
        """有参数时按排序键拼接缓存键。"""
        key = UnifiedDataProvider._cache_params_key({"limit": 10, "period": "5m"})
        assert key == "limit=10:period=5m"

    def test_check_cache_invalid_dict_returns_none(self):
        """MemoryCache 返回无法构造 DataPayload 的字典时降级。"""
        mock_cache = MagicMock()
        mock_cache.get.return_value = {"invalid": "dict"}

        with patch('datacore.api._get_cache', return_value=mock_cache), \
             patch('datacore.api._get_duckdb', return_value=None):
            dc = UnifiedDataProvider()
            result = dc._check_cache('RB:ohlcv:period=daily')

        assert result is None

    def test_write_cache_unavailable_payload_skips(self):
        """不可用 payload 不写入缓存。"""
        payload = DataPayload(
            symbol='RB', data_type=DataType.OHLCV,
            market=MarketType.FUTURES, grade=SourceGrade.UNAVAILABLE,
        )
        mock_cache = MagicMock()

        with patch('datacore.api._get_cache', return_value=mock_cache), \
             patch('datacore.api._get_duckdb', return_value=None):
            dc = UnifiedDataProvider()
            dc._write_cache('RB:ohlcv:period=daily', payload)

        mock_cache.set.assert_not_called()

    def test_report_issue(self):
        """report_issue 调用 IssueRegistry 并返回结果。"""
        from datacore.issue import DataIssue, IssueType
        dc = UnifiedDataProvider()
        issue = DataIssue(
            symbol='RB', data_type='ohlcv',
            issue_type=IssueType.DATA_EMPTY,
            detail='no data', source='test', consumer='pytest',
        )
        with patch('datacore.issue.update_issues_open'):
            result = dc.report_issue(issue)
        assert isinstance(result, dict)
        assert result['reported'] is True
        assert result['mitigation'] is not None

    def test_get_f10(self):
        """get_f10 调用 api_f10 同步函数。"""
        with patch('datacore.api_f10.get_f10_sync') as mock_f10:
            mock_f10.return_value = DataPayload(
                symbol='RB', data_type=DataType.OHLCV,
                market=MarketType.FUTURES, data={'f10': True},
            )
            dc = UnifiedDataProvider()
            result = dc.get_f10('RB')
            mock_f10.assert_called_once_with(dc, 'RB')
            assert result.data == {'f10': True}


# ════════════════════════════════════════════════════════════
# DataCoreConfig 配置系统测试
# ════════════════════════════════════════════════════════════

class TestDataCoreConfig:
    """datacore.config 配置系统 100% 覆盖率测试。"""

    # ──── _load_yaml ────

    def test_load_yaml_no_yaml_module(self):
        """HAS_YAML=False 时返回空 dict"""
        with patch('datacore.config.HAS_YAML', False):
            from datacore.config import DataCoreConfig
            config = DataCoreConfig()
            assert config._yaml_config == {}

    def test_load_yaml_success(self):
        """YAML 文件找到并成功加载"""
        yaml_data = {'sources': {'tdx_lc': {'url': 'http://test:17709/'}}}
        with patch('datacore.config.yaml') as mock_yaml:
            mock_yaml.safe_load.return_value = yaml_data
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data='dummy')):
                    from datacore.config import DataCoreConfig
                    config = DataCoreConfig()
                    assert config._yaml_config == yaml_data
                    mock_yaml.safe_load.assert_called_once()

    def test_load_yaml_parse_error(self):
        """YAML 解析异常时跳过该文件"""
        with patch('datacore.config.yaml') as mock_yaml:
            mock_yaml.safe_load.side_effect = Exception('parse error')
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data='bad: data')):
                    from datacore.config import DataCoreConfig
                    config = DataCoreConfig()
                    assert config._yaml_config == {}

    def test_load_yaml_not_found(self):
        """所有配置文件都不存在时返回空 dict"""
        with patch('datacore.config.yaml') as mock_yaml:
            with patch('pathlib.Path.exists', return_value=False):
                from datacore.config import DataCoreConfig
                config = DataCoreConfig()
                assert config._yaml_config == {}
                mock_yaml.safe_load.assert_not_called()

    # ──── _load_env ────

    def test_load_env_reads_prefix(self):
        """仅读取 DATACORE_ 前缀的环境变量"""
        with patch.dict(os.environ, {
            'DATACORE_TDX_URL': 'http://env:17709/',
            'DATACORE_TIMEOUT': '10',
            'OTHER_VAR': 'ignore',
        }, clear=True):
            with patch.object(DataCoreConfig, '_load_yaml', return_value={}):
                config = DataCoreConfig()
                assert config._env_config['tdx_url'] == 'http://env:17709/'
                assert config._env_config['timeout'] == '10'
                assert 'other_var' not in config._env_config

    # ──── _get ────

    def test_get_env_overrides_yaml(self):
        """环境变量优先级高于 yaml"""
        with patch.object(DataCoreConfig, '_load_yaml', return_value={
            'sources': {'tdx_lc': {'url': 'http://yaml:17709/'}},
        }), patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            # _get 内部 env_key = key.upper().replace('.', '_')
            config._env_config = {'SOURCES_TDX_LC_URL': 'http://env:17709/'}
            assert config._get('sources.tdx_lc.url') == 'http://env:17709/'

    def test_get_yaml_value(self):
        """无环境变量时读取 yaml 值"""
        with patch.object(DataCoreConfig, '_load_yaml', return_value={
            'sources': {'tdx_lc': {'url': 'http://yaml:17709/'}},
        }), patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config._get('sources.tdx_lc.url') == 'http://yaml:17709/'

    def test_get_default_value(self):
        """键不存在时返回默认值"""
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config._get('nonexistent.key', 'fallback') == 'fallback'

    def test_get_none_default(self):
        """无默认值时返回 None"""
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config._get('nonexistent.key') is None

    # ──── property: tdx_url ────

    def test_tdx_url_default(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.tdx_url == 'http://127.0.0.1:17709/'

    def test_tdx_url_from_yaml(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={
            'sources': {'tdx_lc': {'url': 'http://custom:17709/'}},
        }), patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.tdx_url == 'http://custom:17709/'

    # ──── property: tdx_timeout ────

    def test_tdx_timeout_default(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.tdx_timeout == 3

    def test_tdx_timeout_from_env(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            config._env_config = {'SOURCES_TDX_LC_TIMEOUT': '10'}
            assert config.tdx_timeout == 10

    # ──── property: cache_ttl ────

    def test_cache_ttl_default(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.cache_ttl == 3600

    def test_cache_ttl_from_env(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            config._env_config = {'STORE_CACHE_TTL': '7200'}
            assert config.cache_ttl == 7200

    # ──── property: duckdb_path ────

    def test_duckdb_path_default(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}), \
             patch('os.path.expanduser', side_effect=lambda x: x.replace('~', '/home/user')):
            config = DataCoreConfig()
            assert config.duckdb_path == '/home/user/.datacore/datacore.db'
            assert '~' not in config.duckdb_path

    def test_duckdb_path_from_yaml(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={
            'store': {'duckdb_path': '/custom/path/db.duckdb'},
        }), patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.duckdb_path == '/custom/path/db.duckdb'

    # ──── property: pg_dsn ────

    def test_pg_dsn_none(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.pg_dsn is None

    # ──── property: redis_url ────

    def test_redis_url_none(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.redis_url is None

    # ──── property: store_backend ────

    def test_store_backend_default(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.store_backend == 'duckdb'

    def test_store_backend_from_yaml(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={
            'store': {'backend': 'postgres'},
        }), patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.store_backend == 'postgres'

    # ──── property: guosen_api_key ────

    def test_guosen_api_key_none(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.guosen_api_key is None

    def test_guosen_api_key_from_yaml(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={
            'sources': {'guosen': {'api_key': 'test-key-123'}},
        }), patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.guosen_api_key == 'test-key-123'

    # ──── property: guosen_url ────

    def test_guosen_url_default(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.guosen_url == 'https://api.guosen.com.cn/'

    def test_guosen_url_from_yaml(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={
            'sources': {'guosen': {'url': 'https://custom.guosen.com/'}},
        }), patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.guosen_url == 'https://custom.guosen.com/'

    # ──── property: guosen_timeout ────

    def test_guosen_timeout_default(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.guosen_timeout == 5

    def test_guosen_timeout_from_yaml(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={
            'sources': {'guosen': {'timeout': '15'}},
        }), patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert config.guosen_timeout == 15

    # ──── __repr__ ────

    def test_repr(self):
        with patch.object(DataCoreConfig, '_load_yaml', return_value={}), \
             patch.object(DataCoreConfig, '_load_env', return_value={}):
            config = DataCoreConfig()
            assert repr(config) == 'DataCoreConfig(backend=duckdb)'

    # ──── get_config 单例 ────

    def test_get_config_singleton(self):
        from datacore.config import get_config
        # 重置单例
        with patch('datacore.config._config_instance', None):
            c1 = get_config()
            c2 = get_config()
            assert c1 is c2
