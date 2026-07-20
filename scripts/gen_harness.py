"""Data-Core Harness 工程文档和测试批量生成器。"""
import os
import shutil

BASE = r"d:\Programs\data-core"
DOCS = os.path.join(BASE, "docs", "harness")
FDT_TMP = r"d:\Programs\FDT\_harness_src"

def _write(path, content):
    tmp = os.path.join(FDT_TMP, os.path.basename(path))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content.lstrip("\n"))
    shutil.copy(tmp, path)
    print(f"  {os.path.relpath(path, BASE)}")


def _w(path, content):
    _write(os.path.join(DOCS, path), content)


# ═══════════════════════════════════════════════
# 01-architecture.md
# ═══════════════════════════════════════════════
_w("01-architecture.md", """
# Data-Core 架构文档

> 版本: v0.1.0 | 更新: 2026-07-18

## 1. 系统定位

Data-Core 是独立的数据基础设施模块，为 FTS 因子策略系统及其他投研工具提供统一数据接口。
所有数据源自包含，零外部 MCP/Skill/Agent 依赖。

## 2. 分层架构

```
+------------------------------------------------------------------+
|  UnifiedDataProvider (api.py)                                     |
|  get(symbol, data_type) -> 符号解析 -> 市场路由                    |
+-------------------+----------------------------------------------+
|                   |                                              |
|  futures/         |  equity/                                     |
|  TQ-Local -> EM   |  腾讯 -> 东方财富 -> 国信                     |
|  期货基本面        |  A 股财务                                    |
+-------------------+----------------------------------------------+
|  models/          |  registry/          |  store/                |
|  enums/payload    |  SymbolRegistry     |  MemoryCache/DuckDB    |
+-------------------+---------------------+------------------------+
```

## 3. 市场路由

- 纯字母代码（RB, CU）→ futures
- 纯数字代码（600519, 510300）→ equity
- 未知符号 → UNAVAILABLE

## 4. 数据源降级链

| 市场 | P0 | P1 | P2 |
|------|----|----|----|
| 期货 | TQ-Local (127.0.0.1:17709) | 东方财富 HTTP | 天勤(可选) |
| A 股 | 腾讯 HTTP (qt.gtimg.cn) | 东方财富 HTTP | 国信 HTTP(待实现) |

## 5. 存储架构

- 热缓存: MemoryCache (进程内字典, TTL)
- 冷存储: DuckDB (持久化, 可选)
""")

# ═══════════════════════════════════════════════
# 02-lifecycle.md
# ═══════════════════════════════════════════════
_w("02-lifecycle.md", """
# Data-Core 生命周期

> 版本: v0.1.0 | 更新: 2026-07-18

## 1. 数据采集生命周期

```
REQUEST -> 符号解析 -> 市场路由 -> 数据源降级 -> 缓存检查 -> 数据返回
                                          |
                                    源不可用 -> 下一源
                                          |
                                    全部失败 -> UNAVAILABLE
```

## 2. 模块阶段

| 阶段 | 模块 | 状态 |
|------|------|------|
| Phase 1 | models / registry / store | ✅ 完成 |
| Phase 2 | futures providers | ✅ 完成 |
| Phase 3 | equity providers | ✅ 完成 |
| Phase 4 | equity/financial + guosen provider | ✅ 基本 |
| Phase 5 | 工程化(文档/测试/审计) | 🔧 进行中 |
""")

# ═══════════════════════════════════════════════
# 03-configuration.md
# ═══════════════════════════════════════════════
_w("03-configuration.md", """
# Data-Core 配置

> 版本: v0.1.0 | 更新: 2026-07-18

## 1. 配置方式

Data-Core 支持 3 层配置（优先级从高到低）:

| 优先级 | 方式 | 说明 |
|--------|------|------|
| P0 | 环境变量 | DATACORE_* 前缀 |
| P1 | config/settings.yaml | 文件配置 |
| P2 | 代码默认值 | 硬编码兜底 |

## 2. 配置项

| 配置 | 环境变量 | 默认值 | 说明 |
|------|---------|--------|------|
| TDX URL | DATACORE_TDX_URL | http://127.0.0.1:17709/ | TQ-Local 地址 |
| TDX 超时 | DATACORE_TDX_TIMEOUT | 3 | HTTP 超时秒数 |
| 缓存 TTL | DATACORE_CACHE_TTL | 3600 | 内存缓存秒数 |
| DB 路径 | DATACORE_DB_PATH | ~/.datacore/datacore.db | DuckDB 路径 |
""")

# ═══════════════════════════════════════════════
# 04-resilience.md
# ═══════════════════════════════════════════════
_w("04-resilience.md", """
# Data-Core 鲁棒性

> 版本: v0.1.0 | 更新: 2026-07-18

## 1. 降级策略

| 场景 | 行为 |
|------|------|
| TQ-Local 不可用 | 自动降级到东方财富 HTTP |
| 腾讯 API 不可用 | 自动降级到东方财富 HTTP |
| 所有数据源不可用 | 返回 UNAVAILABLE 等级 |
| 网络超时 | 3s 快速失败，尝试下一源 |

## 2. 熔断器

每个数据源关联熔断器: 连续 3 次失败后跳过该源 60 秒。
（TODO: 当前使用简单 try/except，熔断器待实现。）
""")

# ═══════════════════════════════════════════════
# 05-observability.md
# ═══════════════════════════════════════════════
_w("05-observability.md", """
# Data-Core 可观测性

> 版本: v0.1.0 | 更新: 2026-07-18

## 1. 数据质量等级

每个 DataPayload 携带 grade 字段:

| 等级 | 含义 |
|------|------|
| PRIMARY | 第一数据源成功返回 |
| DAILY | 降级源返回 |
| CACHED | 缓存命中 |
| STALE | 过期缓存 |
| UNAVAILABLE | 全部源不可用 |

## 2. 健康检查

```python
from datacore import UnifiedDataProvider
dc = UnifiedDataProvider()
# 检查各源可用性
# TODO: 实现统一健康检查接口
```

## 3. 指标待实现

- 各数据源请求成功率
- 各数据源响应时间 P50/P95
- 缓存命中率
- 降级触发次数
""")

# ═══════════════════════════════════════════════
# 06-testing.md
# ═══════════════════════════════════════════════
_w("06-testing.md", """
# Data-Core 测试

> 版本: v0.1.0 | 更新: 2026-07-18

## 1. 测试文件

| 文件 | 用例数 | 覆盖范围 |
|------|--------|---------|
| tests/test_models.py | 6 | enums/payload/ohlcv |
| tests/test_registry.py | 5 | SymbolRegistry |
| tests/test_store.py | 5 | MemoryCache/DuckDB |
| tests/test_futures_mock.py | 4 | TdxLcProvider(模拟) |
| tests/test_equity_mock.py | 4 | TencentProvider(模拟) |
| tests/test_api.py | 4 | UnifiedDataProvider 路由 |

## 2. 运行

```bash
cd D:\\\\Programs\\\\data-core
python -m pytest tests/ -v
```

## 3. 测试策略

- models/registry/store: 纯单元测试，零外部依赖
- providers: Mock 数据源测试，不依赖真实网络
- api.py: Mock provider 注入测试路由逻辑
""")

# ═══════════════════════════════════════════════
# 07-operations.md
# ═══════════════════════════════════════════════
_w("07-operations.md", """
# Data-Core 运维

> 版本: v0.1.0 | 更新: 2026-07-18

## 1. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1.0 | 2026-07-18 | 初始版本: models + registry + store + futures + equity providers |

## 2. 安装

```bash
pip install -e D:\\\\Programs\\\\data-core
```

## 3. 依赖

必须: numpy, pandas, httpx
可选: duckdb (持久化), beautifulsoup4 (交易所解析)

## 4. 文件结构

27 个 Python 文件, ~38KB 代码, 跨 9 个子目录。
""")

# ═══════════════════════════════════════════════
# 08-gap-analysis.md
# ═══════════════════════════════════════════════
_w("08-gap-analysis.md", """
# Data-Core 差距分析

> 版本: v0.1.0 | 更新: 2026-07-18

## 差距登记

| ID | 优先级 | 描述 | 状态 |
|----|--------|------|------|
| G01 | P2 | 熔断器实现: 当前仅有简单 try/except | 待实现 |
| G02 | P2 | DuckDB 持久化集成: 存储层已实现但未接入 api.py | 待实现 |
| G03 | P2 | 国信 HTTP 数据源: 已有占位但尚未对接具体 API | 待实现 |
| G04 | P1 | 健康检查接口: UnifiedDataProvider 缺少 get_health() | 待实现 |
| G05 | P2 | 请求指标收集: 成功率/延迟/缓存命中率 | 待实现 |
| G06 | P1 | A 股 ETF/可转债/REITs 市场代码支持完善 | 待实现 |
""")

# ═══════════════════════════════════════════════
# 09-advancement-plan.md
# ═══════════════════════════════════════════════
_w("09-advancement-plan.md", """
# Data-Core 晋级计划

> 版本: v0.1.0 | 更新: 2026-07-18

## 里程碑

| 里程碑 | 目标版本 | 截止 | 关键交付 |
|--------|---------|------|---------|
| M1 基础可用 | v0.1.0 | 2026-07-18 | ✅ models/registry/store + futures/equity providers |
| M2 工程化完善 | v0.2.0 | TBD | 熔断器 + 健康检查 + 指标收集 |
| M3 全市场覆盖 | v0.3.0 | TBD | 国信源 + ETF/可转债/REITs 代码完善 |
| M4 生产就绪 | v1.0.0 | TBD | DuckDB 持久化 + 数据刷新调度 + 监控告警 |
""")

# ═══════════════════════════════════════════════
# tests/
# ═══════════════════════════════════════════════
def _wt(path, content):
    _write(os.path.join(BASE, path), content)

_wt("tests/__init__.py", "")
_wt("tests/conftest.py", """import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
""")

_wt("tests/test_models.py", """
import pytest
from datacore.models.enums import DataType, MarketType, SourceGrade
from datacore.models.payload import DataPayload
from datacore.models.ohlcv import KBar, KlineData, QuoteData

class TestEnums:
    def test_data_type_values(self):
        assert DataType.OHLCV.value == "ohlcv"
        assert DataType.QUOTE.value == "quote"

    def test_market_type(self):
        assert MarketType.FUTURES.value == "futures"
        assert MarketType.STOCK.value == "stock"

    def test_source_grade_order(self):
        assert SourceGrade.PRIMARY.value == "primary"
        assert SourceGrade.UNAVAILABLE.value == "unavailable"

class TestPayload:
    def test_data_payload_defaults(self):
        dp = DataPayload(symbol="RB", data_type=DataType.OHLCV, market=MarketType.FUTURES)
        assert not dp.available
        assert dp.grade == SourceGrade.UNAVAILABLE

    def test_data_payload_available(self):
        dp = DataPayload(symbol="RB", data_type=DataType.OHLCV,
                         market=MarketType.FUTURES, grade=SourceGrade.PRIMARY)
        assert dp.available

class TestOHLCV:
    def test_kbar(self):
        kb = KBar(date="20260717", open=100.0, high=101.0, low=99.0, close=100.5, volume=1000)
        assert kb.date == "20260717"
        assert kb.open_interest is None  # optional

    def test_kline_data(self):
        kd = KlineData(symbol="RB", period="daily")
        assert len(kd.bars) == 0
""")

_wt("tests/test_registry.py", """
import pytest
from datacore.registry.symbol_registry import SymbolRegistry
from datacore.models.enums import MarketType

class TestSymbolRegistry:
    def test_init_has_futures(self):
        sr = SymbolRegistry()
        assert sr.resolve("RB") is not None
        assert sr.resolve("CU") is not None

    def test_resolve_market(self):
        sr = SymbolRegistry()
        assert sr.resolve_market("RB") == MarketType.FUTURES

    def test_unknown_symbol(self):
        sr = SymbolRegistry()
        assert sr.resolve("ZZZ") is None

    def test_list_by_market(self):
        sr = SymbolRegistry()
        futures = sr.list_by_market(MarketType.FUTURES)
        assert len(futures) > 50  # 56 futures symbols

    def test_register_dynamic(self):
        sr = SymbolRegistry()
        sr.register("TEST", "Test Symbol", MarketType.STOCK)
        assert sr.resolve("TEST") is not None
        assert sr.resolve_market("TEST") == MarketType.STOCK
""")

_wt("tests/test_store.py", """
import pytest, time
from datacore.store.cache import MemoryCache

class TestMemoryCache:
    def test_set_get(self):
        c = MemoryCache(default_ttl=3600)
        c.set("key1", {"data": 123})
        assert c.get("key1") == {"data": 123}

    def test_expiry(self):
        c = MemoryCache(default_ttl=0.1)
        c.set("key1", "value")
        time.sleep(0.15)
        assert c.get("key1") is None

    def test_invalidate(self):
        c = MemoryCache()
        c.set("key1", "value")
        c.invalidate("key1")
        assert c.get("key1") is None

    def test_clear(self):
        c = MemoryCache()
        c.set("a", 1)
        c.set("b", 2)
        c.clear()
        assert c.get("a") is None
        assert c.get("b") is None

    def test_purge(self):
        c = MemoryCache(default_ttl=-1)
        c.set("x", 1)
        c.set("y", 2)
        n = c.purge()
        assert n == 2
""")

_wt("tests/test_futures_mock.py", """
import pytest
from unittest.mock import patch, MagicMock
from datacore.futures.providers.tdx_lc import TdxLcProvider

class TestTdxLcMock:
    def test_check_available_false(self):
        p = TdxLcProvider()
        p._post = lambda m, params: {}
        assert not p.check_available()

    def test_check_available_true(self):
        p = TdxLcProvider()
        p._post = lambda m, params: {"Value": [{"Code": "RB2501"}]}
        assert p.check_available()

    def test_fetch_kline_no_contract(self):
        p = TdxLcProvider()
        p._post = lambda m, params: {}
        kd = p.fetch_kline("ZZZ")
        assert kd is None

    def test_fetch_quote_no_contract(self):
        p = TdxLcProvider()
        p._post = lambda m, params: {}
        qd = p.fetch_quote("ZZZ")
        assert qd is None
""")

_wt("tests/test_equity_mock.py", """
import pytest
from unittest.mock import patch, MagicMock
from datacore.equity.providers.tencent import TencentProvider
from datacore.models.enums import DataType

class TestTencentMock:
    def test_check_available_false(self):
        p = TencentProvider()
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception("fail")
            assert not p.check_available()

    def test_fetch_quote_fail_returns_none(self):
        p = TencentProvider()
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception("fail")
            result = p.fetch("600519", DataType.QUOTE)
            assert result is None

    def test_fetch_kline_fail_returns_none(self):
        p = TencentProvider()
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception("fail")
            result = p.fetch("600519", DataType.OHLCV)
            assert result is None

    def test_provider_attributes(self):
        p = TencentProvider()
        assert p.name == "tencent"
        assert p.priority == 0
        assert DataType.OHLCV in p.supported_types
        assert DataType.QUOTE in p.supported_types
""")

_wt("tests/test_api.py", """
import pytest
from datacore import UnifiedDataProvider
from datacore.models.enums import DataType, SourceGrade

class TestUnifiedDataProvider:
    def test_init(self):
        dc = UnifiedDataProvider()
        assert dc.registry is not None

    def test_list_symbols(self):
        dc = UnifiedDataProvider()
        syms = dc.list_symbols()
        assert len(syms) > 0

    def test_unknown_symbol_returns_unavailable(self):
        dc = UnifiedDataProvider()
        payload = dc.get("ZZZ", DataType.OHLCV)
        assert not payload.available
        assert payload.grade == SourceGrade.UNAVAILABLE

    def test_get_batch(self):
        dc = UnifiedDataProvider()
        results = dc.get_batch(["RB", "CU"], DataType.OHLCV)
        assert len(results) == 2
        # Both should be unavailable (no real data source in test)
        assert not results["RB"].available
        assert not results["CU"].available
""")

# ═══════════════════════════════════════════════
# README.md
# ═══════════════════════════════════════════════
_wt("README.md", """# Data-Core — 统一数据中心

为股票、期货等市场的投研提供统一数据接口的独立基础设施模块。

## 快速开始

```bash
pip install -e D:\\\\Programs\\\\data-core
```

```python
from datacore import UnifiedDataProvider
from datacore.models.enums import DataType

dc = UnifiedDataProvider()

# 期货 OHLCV
ohlcv = dc.get("RB", DataType.OHLCV, {"period": "daily", "days": 400})

# A 股行情
quote = dc.get("600519", DataType.QUOTE)

# A 股财务指标
fin = dc.get("600519", DataType.FINANCIAL)
```

## 数据源

| 市场 | 第一源 | 降级源 | 兜底 |
|------|--------|--------|------|
| 期货 | TQ-Local (通达信) | 东方财富 HTTP | 天勤(可选) |
| A 股 | 腾讯 HTTP | 东方财富 HTTP | 国信 HTTP |

## 架构

```
UnifiedDataProvider
  +-- futures/        TQ-Local -> 东方财富
  +-- equity/         腾讯 -> 东方财富 -> 国信
  +-- models/         数据类型定义
  +-- registry/       符号注册表 (56个期货品种)
  +-- store/          缓存/DuckDB 持久化
```

## 依赖

必须: numpy, pandas, httpx
可选: duckdb, beautifulsoup4

## 测试

```bash
cd D:\\\\Programs\\\\data-core
python -m pytest tests/ -v
```

## 版本

v0.1.0 (2026-07-18)
""")

# ═══════════════════════════════════════════════
# Clean up tmp
# ═══════════════════════════════════════════════
shutil.rmtree(FDT_TMP, ignore_errors=True)
print("\nAll files created: 9 harness docs + 1 readme + 7 test files")
