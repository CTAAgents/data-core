"""store 模块全覆盖测试 — mock 所有第三方数据库依赖，纯内存运行。"""

from __future__ import annotations

import pickle
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

import datacore.store.duckdb as _duckdb_mod
from datacore.store import DuckDBStore, MemoryCache, PostgresStore, RedisStore
from datacore.store.postgres import build_postgres_store
from datacore.store.redis import build_redis_store


# =============================================================================
# DuckDBStore
# =============================================================================


class TestDuckDBStore:
    """DuckDBStore 全覆盖测试。"""

    def test_init_import_error(self):
        """HAS_DUCKDB=False 时抛出 ImportError。"""
        with patch.object(_duckdb_mod, "HAS_DUCKDB", False):
            with pytest.raises(ImportError, match="duckdb not installed"):
                DuckDBStore()

    def test_init_default_path(self):
        """默认 db_path 来自配置。"""
        mock_duckdb = MagicMock()
        with (
            patch.object(_duckdb_mod, "HAS_DUCKDB", True),
            patch.object(_duckdb_mod, "duckdb", mock_duckdb, create=True),
            patch("datacore.store.duckdb.os.makedirs") as mock_makedirs,
            patch("datacore.store.duckdb.get_config") as mock_get_config,
        ):
            mock_cfg = MagicMock()
            mock_cfg.duckdb_path = "/tmp/.datacore/db.duckdb"
            mock_get_config.return_value = mock_cfg
            store = DuckDBStore()
            assert store._conn is None
            mock_makedirs.assert_called_once_with("/tmp/.datacore", exist_ok=True)

    def test_init_custom_path(self):
        """传入自定义 db_path。"""
        mock_duckdb = MagicMock()
        with (
            patch.object(_duckdb_mod, "HAS_DUCKDB", True),
            patch.object(_duckdb_mod, "duckdb", mock_duckdb, create=True),
            patch("datacore.store.duckdb.os.makedirs"),
        ):
            store = DuckDBStore(db_path="/tmp/custom/test.db")
            assert store.db_path == "/tmp/custom/test.db"

    def test_conn_property(self):
        """conn 属性延迟初始化并缓存。"""
        mock_conn = MagicMock()
        mock_duckdb = MagicMock()
        mock_duckdb.connect.return_value = mock_conn
        with (
            patch.object(_duckdb_mod, "HAS_DUCKDB", True),
            patch.object(_duckdb_mod, "duckdb", mock_duckdb, create=True),
            patch("datacore.store.duckdb.os.makedirs"),
        ):
            store = DuckDBStore(db_path="/tmp/test.db")
            conn = store.conn
            mock_duckdb.connect.assert_called_once_with("/tmp/test.db")
            assert conn is mock_conn
            # 再次访问应返回缓存连接
            assert store.conn is mock_conn
            assert mock_duckdb.connect.call_count == 1

    def test_init_schema(self):
        """init_schema 执行 3 条建表 SQL。"""
        mock_conn = MagicMock()
        mock_duckdb = MagicMock()
        mock_duckdb.connect.return_value = mock_conn
        with (
            patch.object(_duckdb_mod, "HAS_DUCKDB", True),
            patch.object(_duckdb_mod, "duckdb", mock_duckdb, create=True),
            patch("datacore.store.duckdb.os.makedirs"),
        ):
            store = DuckDBStore(db_path="/tmp/test.db")
            store.init_schema()
            assert mock_conn.execute.call_count == 3

    def test_close(self):
        """close 关闭连接并置 None。"""
        mock_conn = MagicMock()
        mock_duckdb = MagicMock()
        mock_duckdb.connect.return_value = mock_conn
        with (
            patch.object(_duckdb_mod, "HAS_DUCKDB", True),
            patch.object(_duckdb_mod, "duckdb", mock_duckdb, create=True),
            patch("datacore.store.duckdb.os.makedirs"),
        ):
            store = DuckDBStore(db_path="/tmp/test.db")
            _ = store.conn
            store.close()
            mock_conn.close.assert_called_once()
            assert store._conn is None

    def test_close_without_conn(self):
        """连接未初始化时 close 不报错。"""
        with (
            patch.object(_duckdb_mod, "HAS_DUCKDB", True),
            patch.object(_duckdb_mod, "duckdb", MagicMock(), create=True),
            patch("datacore.store.duckdb.os.makedirs"),
        ):
            store = DuckDBStore(db_path="/tmp/test.db")
            store.close()  # 不应抛出

    # ──────────── store / load 方法测试（:memory: 模式）──────────────

    def test_store_kline(self):
        """存储 K 线并返回行数。"""
        store = DuckDBStore(":memory:")
        store.init_schema()
        bars = [
            {"date": "2026-06-01", "open": 4000.0, "high": 4050.0,
             "low": 3980.0, "close": 4020.0, "volume": 10000, "amount": 4e7},
            {"date": "2026-06-02", "open": 4020.0, "high": 4100.0,
             "low": 4010.0, "close": 4080.0, "volume": 12000, "amount": 4.8e7},
        ]
        n = store.store_kline("RB", "1d", bars)
        assert n == 2

    def test_load_kline(self):
        """加载 K 线并验证排序（DESC）。"""
        store = DuckDBStore(":memory:")
        store.init_schema()
        bars = [
            {"date": "2026-06-01", "open": 4000.0, "high": 4050.0,
             "low": 3980.0, "close": 4020.0, "volume": 10000, "amount": 4e7},
            {"date": "2026-06-02", "open": 4020.0, "high": 4100.0,
             "low": 4010.0, "close": 4080.0, "volume": 12000, "amount": 4.8e7},
        ]
        store.store_kline("RB", "1d", bars)
        loaded = store.load_kline("RB", "1d", days=365)
        assert len(loaded) == 2
        # 第一条应为最近日期（DESC）
        assert loaded[0]["date"] == "2026-06-02"
        assert loaded[0]["close"] == 4080.0
        assert loaded[1]["date"] == "2026-06-01"
        assert loaded[1]["close"] == 4020.0

    def test_store_quote(self):
        """存储行情快照。"""
        store = DuckDBStore(":memory:")
        store.init_schema()
        quote = {"collected_at": "2025-06-01 10:30:00",
                 "last_price": 4100.0, "volume": 50000, "amount": 2.05e8}
        store.store_quote("RB", quote)
        loaded = store.load_quote("RB")
        assert loaded is not None
        assert loaded["symbol"] == "RB"
        assert loaded["last_price"] == 4100.0

    def test_load_quote(self):
        """加载最新行情快照（未找到时返回 None）。"""
        store = DuckDBStore(":memory:")
        store.init_schema()
        # 无数据时返回 None
        assert store.load_quote("NONEXIST") is None

        # 写入两条，验证返回最新的一条
        store.store_quote("RB", {"collected_at": "2025-01-01 09:30:00",
                                 "last_price": 4000.0, "volume": 100, "amount": 1e5})
        store.store_quote("RB", {"collected_at": "2025-06-01 10:30:00",
                                 "last_price": 4100.0, "volume": 200, "amount": 2e5})
        loaded = store.load_quote("RB")
        assert loaded["last_price"] == 4100.0
        # DuckDB TIMESTAMP 返回 datetime 对象
        from datetime import datetime
        assert loaded["collected_at"] == datetime(2025, 6, 1, 10, 30, 0)

    def test_store_macro(self):
        """存储宏观指标。"""
        store = DuckDBStore(":memory:")
        store.init_schema()
        store.store_macro("GDP", "2025-Q1", 5.5)
        store.store_macro("GDP", "2025-Q2", 5.2)
        rows = store.load_macro("GDP", limit=10)
        assert len(rows) == 2

    def test_load_macro(self):
        """加载宏观指标，验证 limit 和排序。"""
        store = DuckDBStore(":memory:")
        store.init_schema()
        for i in range(5):
            store.store_macro("PMI", f"2025-0{i+1}", 50.0 + i)
        # limit=2
        rows = store.load_macro("PMI", limit=2)
        assert len(rows) == 2
        # 按 date DESC 排序
        assert rows[0]["date"] == "2025-05"
        assert rows[1]["date"] == "2025-04"

    def test_store_kline_upsert(self):
        """重复写入幂等 — INSERT OR REPLACE 不产生重复行。"""
        store = DuckDBStore(":memory:")
        store.init_schema()
        bar = {"date": "2026-06-01", "open": 4000.0, "high": 4050.0,
               "low": 3980.0, "close": 4020.0, "volume": 10000, "amount": 4e7}
        # 第一次写入
        n1 = store.store_kline("RB", "1d", [bar])
        assert n1 == 1
        # 第二次写入相同主键（更新 close）
        bar2 = {**bar, "close": 4050.0}
        n2 = store.store_kline("RB", "1d", [bar2])
        assert n2 == 1
        # 验证只有一行，且 close 被更新
        loaded = store.load_kline("RB", "1d", days=365)
        assert len(loaded) == 1
        assert loaded[0]["close"] == 4050.0

    def test_store_kline_empty(self):
        """空列表引发 InvalidInputException（DuckDB 限制）。"""
        store = DuckDBStore(":memory:")
        store.init_schema()
        import duckdb
        with pytest.raises(duckdb.InvalidInputException, match="executemany requires"):
            store.store_kline("RB", "1d", [])


# =============================================================================
# PostgresStore
# =============================================================================


class TestPostgresStore:
    """PostgresStore 全覆盖测试。"""

    def test_init_import_error(self):
        """psycopg2 不可用时抛出 ImportError。"""
        with patch("datacore.store.postgres._pg_available", return_value=False):
            with pytest.raises(ImportError, match="psycopg2 not installed"):
                PostgresStore()

    def test_init_no_dsn(self):
        """DSN 未配置时抛出 ValueError。"""
        with (
            patch("datacore.store.postgres._pg_available", return_value=True),
            patch("datacore.store.postgres.get_config") as mock_get_config,
        ):
            mock_cfg = MagicMock()
            mock_cfg.pg_dsn = None
            mock_get_config.return_value = mock_cfg
            with pytest.raises(ValueError, match="PostgreSQL DSN not configured"):
                PostgresStore()

    def test_init_success(self):
        """初始化成功，自动建 4 张表。"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pg = MagicMock()
        mock_pg.connect.return_value = mock_conn
        with (
            patch("datacore.store.postgres._pg_available", return_value=True),
            patch.dict("sys.modules", {"psycopg2": mock_pg}),
            patch("datacore.store.postgres.get_config") as mock_get_config,
        ):
            mock_cfg = MagicMock()
            mock_cfg.pg_dsn = "postgresql://u:p@localhost/db"
            mock_get_config.return_value = mock_cfg
            store = PostgresStore()
            assert store._dsn == "postgresql://u:p@localhost/db"
            # _ensure_tables 共 4 条建表 SQL
            assert mock_cursor.execute.call_count == 4

    def test_conn_property(self):
        """conn 属性延迟连接并设置 autocommit。"""
        mock_conn = MagicMock()
        mock_pg = MagicMock()
        mock_pg.connect.return_value = mock_conn
        with patch.dict("sys.modules", {"psycopg2": mock_pg}):
            store = object.__new__(PostgresStore)
            store._dsn = "postgresql://test"
            store._conn = None
            conn = store.conn
            mock_pg.connect.assert_called_once_with("postgresql://test")
            assert mock_conn.autocommit is True
            assert conn is mock_conn
            # 缓存
            assert store.conn is mock_conn
            assert mock_pg.connect.call_count == 1

    def test_cache_get_hit(self):
        """cache_get 命中未过期缓存。"""
        value_bytes = pickle.dumps("cached")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (value_bytes, time.time() + 3600)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        store = object.__new__(PostgresStore)
        store._conn = mock_conn
        result = store.cache_get("mykey")
        assert result == "cached"
        mock_cursor.execute.assert_called_once()

    def test_cache_get_miss(self):
        """cache_get 未命中返回 None。"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        store = object.__new__(PostgresStore)
        store._conn = mock_conn
        assert store.cache_get("missing") is None

    def test_cache_get_expired(self):
        """cache_get 已过期则删除并返回 None。"""
        value_bytes = pickle.dumps("stale")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (value_bytes, 1)  # epoch 1 = 已过期
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        store = object.__new__(PostgresStore)
        store._conn = mock_conn
        result = store.cache_get("expired_key")
        assert result is None
        # 至少两次 execute：SELECT + DELETE
        assert mock_cursor.execute.call_count >= 2

    def test_cache_set(self):
        """cache_set 写入序列化值。"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        store = object.__new__(PostgresStore)
        store._conn = mock_conn
        store.cache_set("k", "v", 300)
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[0].startswith("INSERT INTO datacore_cache")
        assert call_args[1][0] == "k"
        assert pickle.loads(call_args[1][1]) == "v"

    def test_cache_invalidate(self):
        """cache_invalidate 发送 DELETE。"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        store = object.__new__(PostgresStore)
        store._conn = mock_conn
        store.cache_invalidate("delkey")
        mock_cursor.execute.assert_called_once_with(
            "DELETE FROM datacore_cache WHERE key = %s", ("delkey",)
        )

    def test_cache_purge(self):
        """cache_purge 清除过期条目并返回计数。"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (5,)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        store = object.__new__(PostgresStore)
        store._conn = mock_conn
        count = store.cache_purge()
        assert count == 5
        # SELECT COUNT + DELETE
        assert mock_cursor.execute.call_count == 2

    def test_close(self):
        """close 关闭连接并置 None。"""
        mock_conn = MagicMock()
        store = object.__new__(PostgresStore)
        store._conn = mock_conn
        store.close()
        mock_conn.close.assert_called_once()
        assert store._conn is None

    def test_close_without_conn(self):
        """连接未初始化时 close 不报错。"""
        store = object.__new__(PostgresStore)
        store._conn = None
        store.close()  # 不应抛出

    # ── build_postgres_store ────────────────────────────────────────────

    def test_build_unavailable(self):
        """psycopg2 不可用时返回 None。"""
        with patch("datacore.store.postgres._pg_available", return_value=False):
            assert build_postgres_store() is None

    def test_build_no_dsn(self):
        """DSN 为空时返回 None。"""
        with (
            patch("datacore.store.postgres._pg_available", return_value=True),
            patch("datacore.store.postgres.get_config") as mock_get_config,
        ):
            mock_cfg = MagicMock()
            mock_cfg.pg_dsn = None
            mock_get_config.return_value = mock_cfg
            assert build_postgres_store() is None

    def test_build_ok(self):
        """正常返回 PostgresStore 实例。"""
        mock_conn = MagicMock()
        mock_pg = MagicMock()
        mock_pg.connect.return_value = mock_conn
        with (
            patch("datacore.store.postgres._pg_available", return_value=True),
            patch.dict("sys.modules", {"psycopg2": mock_pg}),
            patch("datacore.store.postgres.get_config") as mock_get_config,
        ):
            mock_cfg = MagicMock()
            mock_cfg.pg_dsn = "postgresql://test"
            mock_get_config.return_value = mock_cfg
            store = build_postgres_store()
            assert isinstance(store, PostgresStore)

    def test_build_exception(self):
        """连接异常时返回 None。"""
        mock_pg = MagicMock()
        mock_pg.connect.side_effect = Exception("connection failed")
        with (
            patch("datacore.store.postgres._pg_available", return_value=True),
            patch.dict("sys.modules", {"psycopg2": mock_pg}),
            patch("datacore.store.postgres.get_config") as mock_get_config,
        ):
            mock_cfg = MagicMock()
            mock_cfg.pg_dsn = "postgresql://test"
            mock_get_config.return_value = mock_cfg
            assert build_postgres_store() is None


# =============================================================================
# RedisStore
# =============================================================================


class TestRedisStore:
    """RedisStore 全覆盖测试。"""

    def test_init_import_error(self):
        """redis 不可用时抛出 ImportError。"""
        with patch("datacore.store.redis._redis_available", return_value=False):
            with pytest.raises(ImportError, match="redis not installed"):
                RedisStore()

    def test_init_no_url(self):
        """URL 未配置时抛出 ValueError。"""
        with (
            patch("datacore.store.redis._redis_available", return_value=True),
            patch("datacore.store.redis.get_config") as mock_get_config,
        ):
            mock_cfg = MagicMock()
            mock_cfg.redis_url = None
            mock_get_config.return_value = mock_cfg
            with pytest.raises(ValueError, match="Redis URL not configured"):
                RedisStore()

    def test_init_success(self):
        """初始化成功，ping 验证连接。"""
        mock_r = MagicMock()
        mock_redis_module = MagicMock()
        mock_redis_module.from_url.return_value = mock_r
        with (
            patch("datacore.store.redis._redis_available", return_value=True),
            patch.dict("sys.modules", {"redis": mock_redis_module}),
            patch("datacore.store.redis.get_config") as mock_get_config,
        ):
            mock_cfg = MagicMock()
            mock_cfg.redis_url = "redis://localhost:6379/0"
            mock_get_config.return_value = mock_cfg
            store = RedisStore()
            mock_redis_module.from_url.assert_called_once_with(
                "redis://localhost:6379/0", decode_responses=False
            )
            mock_r.ping.assert_called_once()

    def test_cache_get_hit(self):
        """cache_get 命中返回反序列化值。"""
        mock_r = MagicMock()
        mock_r.get.return_value = pickle.dumps("redis_val")
        store = object.__new__(RedisStore)
        store._r = mock_r
        assert store.cache_get("hitkey") == "redis_val"
        mock_r.get.assert_called_once_with("hitkey")

    def test_cache_get_miss(self):
        """cache_get 未命中返回 None。"""
        mock_r = MagicMock()
        mock_r.get.return_value = None
        store = object.__new__(RedisStore)
        store._r = mock_r
        assert store.cache_get("misskey") is None

    def test_cache_set(self):
        """cache_set 序列化并设置 TTL。"""
        mock_r = MagicMock()
        store = object.__new__(RedisStore)
        store._r = mock_r
        store.cache_set("k", "v", 600)
        mock_r.set.assert_called_once_with("k", pickle.dumps("v"), ex=600)

    def test_cache_invalidate(self):
        """cache_invalidate 删除并发布消息。"""
        mock_r = MagicMock()
        store = object.__new__(RedisStore)
        store._r = mock_r
        store.cache_invalidate("delkey")
        mock_r.delete.assert_called_once_with("delkey")
        mock_r.publish.assert_called_once_with("datacore_cache_invalidate", "delkey")

    def test_cache_invalidate_publish_fail(self):
        """cache_invalidate 发布失败不抛出异常。"""
        mock_r = MagicMock()
        mock_r.publish.side_effect = Exception("publish fail")
        store = object.__new__(RedisStore)
        store._r = mock_r
        store.cache_invalidate("key")  # 不应抛出
        mock_r.delete.assert_called_once_with("key")

    def test_cache_purge(self):
        """cache_purge 返回 0。"""
        store = object.__new__(RedisStore)
        store._r = MagicMock()
        assert store.cache_purge() == 0

    def test_close(self):
        """close 不报错。"""
        store = object.__new__(RedisStore)
        store._r = MagicMock()
        store.close()

    # ── build_redis_store ───────────────────────────────────────────────

    def test_build_unavailable(self):
        """redis 不可用时返回 None。"""
        with patch("datacore.store.redis._redis_available", return_value=False):
            assert build_redis_store() is None

    def test_build_no_url(self):
        """URL 为空时返回 None。"""
        with (
            patch("datacore.store.redis._redis_available", return_value=True),
            patch("datacore.store.redis.get_config") as mock_get_config,
        ):
            mock_cfg = MagicMock()
            mock_cfg.redis_url = None
            mock_get_config.return_value = mock_cfg
            assert build_redis_store() is None

    def test_build_ok(self):
        """正常返回 RedisStore 实例。"""
        mock_r = MagicMock()
        mock_redis_module = MagicMock()
        mock_redis_module.from_url.return_value = mock_r
        with (
            patch("datacore.store.redis._redis_available", return_value=True),
            patch.dict("sys.modules", {"redis": mock_redis_module}),
            patch("datacore.store.redis.get_config") as mock_get_config,
        ):
            mock_cfg = MagicMock()
            mock_cfg.redis_url = "redis://localhost:6379/0"
            mock_get_config.return_value = mock_cfg
            store = build_redis_store()
            assert isinstance(store, RedisStore)

    def test_build_exception(self):
        """连接异常时返回 None。"""
        mock_redis_module = MagicMock()
        mock_redis_module.from_url.side_effect = Exception("connection failed")
        with (
            patch("datacore.store.redis._redis_available", return_value=True),
            patch.dict("sys.modules", {"redis": mock_redis_module}),
            patch("datacore.store.redis.get_config") as mock_get_config,
        ):
            mock_cfg = MagicMock()
            mock_cfg.redis_url = "redis://localhost:6379/0"
            mock_get_config.return_value = mock_cfg
            assert build_redis_store() is None


# =============================================================================
# MemoryCache（现有测试之外的补充场景）
# =============================================================================


class TestMemoryCacheExtended:
    """MemoryCache 补充测试。"""

    def test_set_get_complex(self):
        """存储复杂 Python 对象。"""
        c = MemoryCache()
        data = {"a": [1, 2, 3], "b": {"nested": True}}
        c.set("complex", data)
        assert c.get("complex") == data

    def test_custom_ttl(self):
        """set 时传入自定义 TTL。"""
        c = MemoryCache(default_ttl=3600)
        c.set("short", "val", ttl=0.05)
        time.sleep(0.07)
        assert c.get("short") is None

    def test_invalidate_missing(self):
        """invalidate 不存在的 key 不报错。"""
        c = MemoryCache()
        c.invalidate("nonexistent")

    def test_purge_no_expired(self):
        """purge 无过期条目返回 0。"""
        c = MemoryCache(default_ttl=3600)
        c.set("a", 1)
        assert c.purge() == 0
        assert c.get("a") == 1

    def test_clear_empty(self):
        """clear 空缓存不报错。"""
        c = MemoryCache()
        c.clear()
        assert c.get("k") is None
