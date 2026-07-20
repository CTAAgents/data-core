#!/usr/bin/env python3
"""Data-Core 脚手架 — 创建所有剩余包文件。"""
import os

BASE = r"d:\Programs\data-core\datacore"

files = {}

# === registry ===
files[os.path.join(BASE, "registry", "__init__.py")] = '''"""符号注册表。"""
from .symbol_registry import SymbolRegistry, SymbolEntry
__all__ = ["SymbolRegistry", "SymbolEntry"]
'''

files[os.path.join(BASE, "registry", "symbol_registry.py")] = r'''
"""统一符号注册表 — 符号解析 + 市场路由。"""

from __future__ import annotations
from typing import Optional
from datacore.models.enums import MarketType


class SymbolEntry:
    """符号条目。"""
    def __init__(self, symbol: str, name: str, market: MarketType,
                 sector: str = "", is_active: bool = True):
        self.symbol = symbol
        self.name = name
        self.market = market
        self.sector = sector
        self.is_active = is_active


class SymbolRegistry:
    """统一符号注册表。"""

    def __init__(self):
        self._entries: dict[str, SymbolEntry] = {}
        self._init_builtin()

    def _init_builtin(self):
        """初始化内置期货品种。"""
        futures = [
            # 黑色系
            ("RB", "螺纹钢", "黑色系"), ("HC", "热卷", "黑色系"),
            ("I", "铁矿石", "黑色系"), ("J", "焦炭", "黑色系"),
            ("JM", "焦煤", "黑色系"), ("SF", "硅铁", "黑色系"), ("SM", "锰硅", "黑色系"),
            # 能源
            ("SC", "原油", "能源链"), ("LU", "低硫燃油", "能源链"),
            ("FU", "燃油", "能源链"), ("BU", "沥青", "能源链"),
            ("PG", "液化气", "能源链"), ("PX", "对二甲苯", "能源链"),
            # 聚酯链
            ("TA", "PTA", "聚酯链"), ("PF", "短纤", "聚酯链"),
            ("EG", "乙二醇", "聚酯链"), ("EB", "苯乙烯", "聚酯链"),
            # 化工
            ("V", "PVC", "塑化链"), ("PP", "聚丙烯", "塑化链"),
            ("L", "聚乙烯", "塑化链"), ("MA", "甲醇", "塑化链"),
            ("SA", "纯碱", "化工"), ("UR", "尿素", "化工"), ("SH", "烧碱", "化工"),
            # 有色
            ("CU", "沪铜", "有色金属"), ("AL", "沪铝", "有色金属"),
            ("ZN", "沪锌", "有色金属"), ("PB", "沪铅", "有色金属"),
            ("NI", "沪镍", "有色金属"), ("SN", "沪锡", "有色金属"),
            ("AO", "氧化铝", "有色金属"), ("SS", "不锈钢", "有色金属"),
            # 贵金属
            ("AU", "黄金", "贵金属"), ("AG", "白银", "贵金属"),
            # 油脂油料
            ("A", "豆一", "油脂油料"), ("B", "豆二", "油脂油料"),
            ("M", "豆粕", "油脂油料"), ("Y", "豆油", "油脂油料"),
            ("P", "棕榈油", "油脂油料"), ("OI", "菜油", "油脂油料"),
            ("RM", "菜粕", "油脂油料"), ("PK", "花生", "油脂油料"),
            # 农产品
            ("C", "玉米", "农产品"), ("CS", "淀粉", "农产品"),
            ("SR", "白糖", "农产品"), ("CF", "棉花", "农产品"),
            ("JD", "鸡蛋", "农产品"), ("LH", "生猪", "农产品"),
            # 建材
            ("FG", "玻璃", "建材化工"), ("RU", "橡胶", "建材化工"),
            ("NR", "20号胶", "建材化工"), ("BR", "丁二烯胶", "建材化工"),
            ("SP", "纸浆", "建材化工"),
            # 新能源
            ("LC", "碳酸锂", "新能源"), ("SI", "工业硅", "新能源"),
            # 航运
            ("EC", "欧线集运", "航运"),
        ]
        for sym, name, sector in futures:
            self.register(sym, name, MarketType.FUTURES, sector)

    def register(self, symbol: str, name: str, market: MarketType,
                 sector: str = "", is_active: bool = True) -> SymbolEntry:
        entry = SymbolEntry(symbol, name, market, sector, is_active)
        self._entries[symbol.upper()] = entry
        return entry

    def resolve(self, symbol: str) -> Optional[SymbolEntry]:
        """解析符号，返回条目或 None。"""
        s = symbol.upper().strip()
        return self._entries.get(s)

    def resolve_market(self, symbol: str) -> Optional[MarketType]:
        """解析符号所属市场。"""
        entry = self.resolve(symbol)
        return entry.market if entry else None

    def list_by_market(self, market: MarketType) -> list[SymbolEntry]:
        return [e for e in self._entries.values() if e.market == market]

    def list_all(self) -> list[SymbolEntry]:
        return list(self._entries.values())
'''

# === store ===
files[os.path.join(BASE, "store", "__init__.py")] = '''"""存储层。"""
from .cache import MemoryCache
__all__ = ["MemoryCache"]
'''

files[os.path.join(BASE, "store", "cache.py")] = r'''
"""内存缓存 (TTL) — 零依赖，热数据加速。"""

from __future__ import annotations
import time
import pickle
from typing import Any, Optional


class MemoryCache:
    """进程内字典缓存，TTL 过期自动失效。"""

    def __init__(self, default_ttl: float = 3600):
        self._store: dict[str, tuple[bytes, float]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if item is None:
            return None
        value, expires = item
        if expires < time.time():
            del self._store[key]
            return None
        return pickle.loads(value)

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expires = time.time() + (ttl if ttl is not None else self.default_ttl)
        self._store[key] = (pickle.dumps(value), expires)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def purge(self) -> int:
        now = time.time()
        expired = [k for k, (_, e) in self._store.items() if e < now]
        for k in expired:
            del self._store[k]
        return len(expired)

    def clear(self) -> None:
        self._store.clear()
'''

files[os.path.join(BASE, "store", "duckdb.py")] = r'''
"""DuckDB 持久化存储 — 冷数据持久化。"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False


DB_DIR = Path.home() / ".datacore"


class DuckDBStore:
    """DuckDB 持久化存储引擎。"""

    def __init__(self, db_path: Optional[str] = None):
        if not HAS_DUCKDB:
            raise ImportError("duckdb not installed: pip install duckdb")
        self.db_path = db_path or str(DB_DIR / "datacore.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
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
'''

# === futures ===
files[os.path.join(BASE, "futures", "__init__.py")] = '''"""期货数据模块。"""
from .futures_provider import FuturesDataProvider
__all__ = ["FuturesDataProvider"]
'''

files[os.path.join(BASE, "futures", "providers", "__init__.py")] = '''"""期货数据源提供者。"""
from .base import FuturesDataSource
from .tdx_lc import TdxLcProvider
from .eastmoney import EastMoneyFuturesProvider

__all__ = ["FuturesDataSource", "TdxLcProvider", "EastMoneyFuturesProvider"]
'''

# === equity ===
files[os.path.join(BASE, "equity", "__init__.py")] = '''"""A 股数据模块。"""
from .equity_provider import EquityDataProvider
__all__ = ["EquityDataProvider"]
'''

files[os.path.join(BASE, "equity", "providers", "__init__.py")] = '''"""A 股数据源提供者。"""
from .base import EquityDataSource
from .tencent import TencentProvider
from .eastmoney import EastMoneyEquityProvider

__all__ = ["EquityDataSource", "TencentProvider", "EastMoneyEquityProvider"]
'''

# === config ===
config_dir = r"d:\Programs\data-core\config"

# === 写入所有文件 ===
for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.lstrip("\n"))
    print(f"  ✅ {os.path.relpath(path, BASE)}")

print(f"\n--- 完成: {len(files)} 个文件 ---")
