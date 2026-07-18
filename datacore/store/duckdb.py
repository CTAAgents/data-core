"""DuckDB 持久化存储 — 冷数据持久化（默认后端）。"""

from __future__ import annotations

import os
from typing import Optional

from datetime import datetime, timedelta

from datacore.config import get_config

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False


class DuckDBStore:
    """DuckDB 持久化存储引擎。"""

    def __init__(self, db_path: Optional[str] = None):
        if not HAS_DUCKDB:
            raise ImportError("duckdb not installed: pip install duckdb")
        self.db_path = db_path or get_config().duckdb_path
        _dir = os.path.dirname(self.db_path)
        if _dir:
            os.makedirs(_dir, exist_ok=True)
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    @property
    def conn(self):
        if self._conn is None:
            self._conn = duckdb.connect(self.db_path)
        return self._conn

    def init_schema(self):
        """建表（幂等）。"""
        schemas = [
            """CREATE TABLE IF NOT EXISTS kline_cache (
                symbol VARCHAR NOT NULL, period VARCHAR NOT NULL,
                date VARCHAR NOT NULL, open DOUBLE, high DOUBLE,
                low DOUBLE, close DOUBLE, volume DOUBLE, amount DOUBLE,
                PRIMARY KEY (symbol, period, date)
            )""",
            """CREATE TABLE IF NOT EXISTS quote_cache (
                symbol VARCHAR NOT NULL, collected_at TIMESTAMP NOT NULL,
                last_price DOUBLE, volume DOUBLE, amount DOUBLE
            )""",
            """CREATE TABLE IF NOT EXISTS macro_cache (
                indicator VARCHAR NOT NULL, date VARCHAR NOT NULL,
                value DOUBLE, PRIMARY KEY (indicator, date)
            )""",
        ]
        for sql in schemas:
            self.conn.execute(sql)

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def store_kline(self, symbol: str, period: str, bars: list[dict]) -> int:
        """批量存储 K 线数据。返回插入行数。"""
        sql = (
            "INSERT OR REPLACE INTO kline_cache "
            "(symbol, period, date, open, high, low, close, volume, amount) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        rows = [
            (symbol, period, b["date"], b.get("open"), b.get("high"),
             b.get("low"), b.get("close"), b.get("volume"), b.get("amount"))
            for b in bars
        ]
        self.conn.executemany(sql, rows)
        return len(rows)

    def load_kline(self, symbol: str, period: str, days: int = 120) -> list[dict]:
        """加载 K 线数据。按 date DESC 排序。"""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        sql = (
            "SELECT symbol, period, date, open, high, low, close, volume, amount "
            "FROM kline_cache WHERE symbol = ? AND period = ? AND date >= ? "
            "ORDER BY date DESC"
        )
        result = self.conn.execute(sql, (symbol, period, cutoff)).fetchall()
        columns = ["symbol", "period", "date", "open", "high", "low", "close", "volume", "amount"]
        return [dict(zip(columns, row)) for row in result]

    def store_quote(self, symbol: str, quote: dict) -> None:
        """存储行情快照。"""
        sql = (
            "INSERT INTO quote_cache "
            "(symbol, collected_at, last_price, volume, amount) "
            "VALUES (?, ?, ?, ?, ?)"
        )
        self.conn.execute(sql, (
            symbol,
            quote.get("collected_at", datetime.now().isoformat()),
            quote.get("last_price"),
            quote.get("volume"),
            quote.get("amount"),
        ))

    def load_quote(self, symbol: str) -> Optional[dict]:
        """加载最近行情快照。"""
        sql = (
            "SELECT symbol, collected_at, last_price, volume, amount "
            "FROM quote_cache WHERE symbol = ? "
            "ORDER BY collected_at DESC LIMIT 1"
        )
        row = self.conn.execute(sql, (symbol,)).fetchone()
        if row is None:
            return None
        columns = ["symbol", "collected_at", "last_price", "volume", "amount"]
        return dict(zip(columns, row))

    def store_macro(self, indicator: str, date: str, value: float) -> None:
        """存储宏观指标值。"""
        sql = (
            "INSERT OR REPLACE INTO macro_cache (indicator, date, value) "
            "VALUES (?, ?, ?)"
        )
        self.conn.execute(sql, (indicator, date, value))

    def load_macro(self, indicator: str, limit: int = 50) -> list[dict]:
        """加载宏观指标数据。"""
        sql = (
            "SELECT indicator, date, value "
            "FROM macro_cache WHERE indicator = ? "
            "ORDER BY date DESC LIMIT ?"
        )
        result = self.conn.execute(sql, (indicator, limit)).fetchall()
        columns = ["indicator", "date", "value"]
        return [dict(zip(columns, row)) for row in result]
