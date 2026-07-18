"""WebSocket 实时行情测试。"""
import pytest
from unittest.mock import MagicMock


class TestStreamQuote:
    def test_default_values(self):
        from datacore.stream import StreamQuote
        q = StreamQuote(symbol="RB")
        assert q.symbol == "RB"
        assert q.last_price == 0.0
        assert q.bid_price == []
        assert q.ask_price == []

    def test_with_values(self):
        from datacore.stream import StreamQuote
        q = StreamQuote(
            symbol="RB", last_price=3500.0, high=3600.0,
            volume=10000, bid_price=[3499, 3498],
        )
        assert q.last_price == 3500.0
        assert len(q.bid_price) == 2


class TestStreamCallback:
    def test_on_quote_default(self):
        from datacore.stream import StreamCallback, StreamQuote
        cb = StreamCallback()
        # 默认实现不抛异常
        cb.on_quote(StreamQuote(symbol="RB"))
        cb.on_error(Exception("test"))
        cb.on_reconnect()

    def test_custom_callback(self):
        from datacore.stream import StreamCallback, StreamQuote
        received = []

        class MyCallback(StreamCallback):
            def on_quote(self, quote):
                received.append(quote)

        cb = MyCallback()
        cb.on_quote(StreamQuote(symbol="RB", last_price=3500))
        assert len(received) == 1
        assert received[0].last_price == 3500


class TestWebSocketManager:
    def test_subscribe(self):
        from datacore.stream import WebSocketManager, StreamCallback
        mgr = WebSocketManager()
        cb = StreamCallback()
        assert mgr.subscribe("RB", cb) is True
        assert mgr.total_subscriptions == 1

    def test_unsubscribe(self):
        from datacore.stream import WebSocketManager, StreamCallback
        mgr = WebSocketManager()
        cb = StreamCallback()
        mgr.subscribe("RB", cb)
        assert mgr.total_subscriptions == 1
        mgr.unsubscribe("RB", cb)
        assert mgr.total_subscriptions == 0

    def test_multiple_subscribers(self):
        from datacore.stream import WebSocketManager, StreamCallback
        mgr = WebSocketManager()
        cb1 = StreamCallback()
        cb2 = StreamCallback()
        mgr.subscribe("RB", cb1)
        mgr.subscribe("RB", cb2)
        assert len(mgr.get_subscribers("RB")) == 2

    def test_get_subscribers_none(self):
        from datacore.stream import WebSocketManager
        mgr = WebSocketManager()
        assert mgr.get_subscribers("NONEXIST") == []

    def test_start_stop(self):
        from datacore.stream import WebSocketManager
        mgr = WebSocketManager()
        assert mgr.is_running is False
        mgr.start()
        assert mgr.is_running is True
        mgr.stop()
        assert mgr.is_running is False

    def test_get_stream_manager_singleton(self):
        from datacore.stream import get_stream_manager
        m1 = get_stream_manager()
        m2 = get_stream_manager()
        assert m1 is m2
