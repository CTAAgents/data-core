# Data-Core Operations

Version: v0.4.0 | Updated: 2026-07-18

## Version History

| 版本 | 日期 | 变更说明 |
|:-----|:-----|:---------|
| **v0.4.0** | **2026-07-18** | **工程完善版：熔断器 + 健康检查 + 指标收集 + DuckDB 持久化 + CLI 增强** |
| | | • 新增 Breaker 熔断器（CLOSED/OPEN/HALF_OPEN） |
| | | • 新增 get_health() 健康检查接口（返回各数据源实时状态） |
| | | • 新增 MetricsCollector 指标收集框架 |
| | | • 新增 store/duckdb.py DuckDB 加密持久化 |
| | | • CLI status 命令显示真实数据源状态 |
| | | • ETF/CB/REIT 基础数据获取支持 |
| | | • 新增 3 个测试文件，80 个测试用例 |
| **v0.3.0** | **2026-07-18** | **数据加工层：情绪管线 + 市场制度检测** |
| | | • 新增 `processing/` 模块（7个文件） |
| | | • 新增 SENTIMENT/MARKET_STATE DataType |
| | | • 规则情绪基线（词典法，零成本，含否定词/程度副词） |
| | | • LLM 情绪打分骨架（含降级到规则基线） |
| | | • 情绪聚合器（时间衰减+置信度加权+按日聚合） |
| | | • 市场制度检测（趋势/波动率/成交量综合判断） |
| | | • SENTIMENT/MARKET_STATE/NEWS/MACRO 接入 UnifiedDataProvider |
| | | • 新增 36 个测试用例（总计 104 个） |
| v0.2.0 | 2026-07-18 | 期货能力增强 + 新闻资讯模块 + 宏观数据模块 |
| v0.1.0 | 2026-07-18 | Initial version, 27 source files, 28 test cases |

## Dependencies

### 必需依赖
- `numpy>=1.24`, `pandas>=2.0`, `httpx>=0.25`, `pyyaml>=6.0`

### 可选依赖
| 分组 | 依赖 | 说明 |
|:-----|:-----|:-----|
| `store` | `duckdb>=0.9` | DuckDB 持久化 |
| `postgres` | `psycopg2-binary>=2.9` | PostgreSQL |
| `redis` | `redis>=5.0` | Redis 缓存 |
| `full` | 以上全部 | 完整功能 |
| - | `openai>=1.0` | LLM 情绪打分（v0.3.0，可选） |
| - | `beautifulsoup4>=4.12` | HTML 解析 |

## File Structure

```
datacore/                    52 个 Python 源文件
├── models/                  数据模型与枚举
├── registry/                品种注册表
├── store/                   存储层（含 duckdb.py 持久化）
├── breaker.py               熔断器（v0.4.0 新增）
├── metrics.py               指标收集（v0.4.0 新增）
├── futures/                 期货数据模块
├── equity/                  股票数据模块
├── news/                    新闻资讯模块
├── macro/                   宏观数据模块
├── processing/              数据加工层
│   ├── base.py              ProcessingStage 抽象基类
│   ├── models.py            情绪/市场制度数据模型
│   ├── sentiment/           情绪加工管线
│   └── market_regime.py     市场制度检测
├── config.py                统一配置
├── api.py                   统一入口 API（含 get_health()）
└── cli.py                   命令行工具（status 显示真实状态）

tests/                       16 个测试文件，184 个测试用例
├── test_breaker.py          熔断器测试（v0.4.0 新增）
├── test_health.py           健康检查测试（v0.4.0 新增）
├── test_metrics.py          指标收集测试（v0.4.0 新增）
├── test_processing.py       数据加工层测试
└── ...

docs/harness/                9 个工程规范文档
.pylintrc                    pylint 项目级配置（审计满分）

**总计: 52 个源文件 + 16 个测试文件 + 9 个工程文档**
