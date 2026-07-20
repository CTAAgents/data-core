# Data-Core Gap Analysis

Version: v2.4.0 | Updated: 2026-07-20

## Overview

所有 Phase 0-17 差距已全部关闭。v2.4.0 Provider adjustment 参数打通版完成，关闭 G34（股票 K 线强制复权，无法获取原始数据）。消费端可通过 `adjustment="none"` 获取未复权原始数据。测试总数 1974 个（新增 10 个 adjustment 测试），ruff 代码审计零错误。

| 阶段 | 版本 | 状态 | 新增差距 | 关闭差距 |
|:-----|:-----|:-----|:---------|:---------|
| Phase 5 | v0.5.0 | ✅ COMPLETED | 2 (G11, G12) | 6 (G03, G07, G08, G09, D01, D03, D05) |
| Phase 6 | v0.6.0 | ✅ COMPLETED | 0 | 1 (G11) |
| Phase 7 | v1.0.0 | ✅ COMPLETED | 0 | 1 (G12) |
| Phase 8 | v1.1.0 | ✅ COMPLETED | 4 (G13, G14, G15, G16) | 4 (G13, G14, G15, G16) |
| Phase 9 | v1.2.0 | ✅ COMPLETED | 2 (G17, G18) | 2 (G17, G18) |
| Phase 10 | v1.3.0 | ✅ COMPLETED | 8 (G19-G26) | 8 (G19-G26) |
| Phase 11 | v2.0.0 | ✅ COMPLETED | 2 (G27-G28) | 2 (G27-G28) |
| Phase 12 | v2.0.0 | ✅ COMPLETED | 0 | 0 (终验通过) |
| Phase 13 | v2.1.0 | ✅ COMPLETED | 1 (G29) | 1 (G29) |
| Phase 14 | v2.1.0 | ✅ COMPLETED | 1 (G30) | 1 (G30) |
| Phase 15 | v2.2.0 | ✅ COMPLETED | 1 (G31) | 1 (G31) |
| Phase 16 | v2.3.0 | ✅ COMPLETED | 2 (G32, G33) | 2 (G32, G33) |
| Phase 17 | v2.4.0 | ✅ COMPLETED | 1 (G34) | 1 (G34) |

## v2.4.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G34 | Provider 层强制复权，无法获取原始数据 | v2.4.0 | tencent.py/eastmoney.py 股票 K 线原本硬编码 qfq/fqt=1 强制前复权，消费端无法获取未复权原始数据。修复：Provider 层接收 params["adjustment"] 参数，映射到 API 复权参数（腾讯: qfq/hfq/不带；东财: fqt=0/1/2）。默认值 "qfq" 保持向后兼容。api.py params 直接透传到 Provider。消费端可调用 dc.get("600519", OHLCV, {"adjustment": "none"}) 获取原始数据。 |

## v2.3.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G32 | SymbolRegistry 不识别 A 股代码 | v2.3.0 | SymbolRegistry._init_builtin 原本只注册 56 个期货品种，导致 dc.get("600519", QUOTE) 路由失败返回 "Unknown symbol"。新增 _guess_equity_market() 规则识别：6 位纯数字前缀（60/00/30/68/8/4）→ STOCK，ETF 前缀（510/511/512/513/515/588/159/516）→ ETF，可转债前缀（110/113/118/127/128/132/133）→ CB。无需显式注册全部 A 股股票。 |
| G33 | 东方财富期货 secid 格式过时 | v2.3.0 | eastmoney.py 原本用 secid="CF.RB" 调用 push2his API 返回空数据。修复为带交易所前缀的主力合约探测格式：遍历 [115.RB9999, 113.RB9999, 114.RB9999, 8.RB9999] 期货 secid 候选，第一个返回非空 klinedata 即采用。保持原有 fields/klt/fqt 参数不变。 |


## v2.2.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G31 | Prometheus 可观测性集成 | v2.2.0 | 新增 datacore/observability.py + datacore/metrics_endpoint.py，11 个标准指标（Counter/Gauge/Histogram），observe_api_call / observe_tool_call 装饰器埋点，Prometheus exposition format HTTP 端点（/metrics、/healthz、/），prometheus_client 可选依赖降级，线程安全实现，metrics.py 增强（_format_prometheus() 方法向后兼容），19 个测试用例 |

## v2.1.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G29 | API 层周期自动转换 | v2.1.0 | UnifiedDataProvider.get() 对 OHLCV 类型数据自动重采样，支持 1m→5m→15m→30m→60m→daily→weekly→monthly，自动推断源周期，出错时降级返回原始数据，payload.meta.resampled_from 记录源周期，异步接口自动继承 |
| G30 | BaseTool args_schema 补全 | v2.1.0 | 新增 datacore/tools/schemas.py，23 个 Pydantic Schema 类，23 个 Tool 全部配备 args_schema，pydantic 为可选依赖，未安装时 args_schema = None，完全兼容 LangChain StructuredTool |

## v2.0.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G27 | FDT 兼容层 | v2.0.0 | 新增 fdc_compat.py，提供 FDC 兼容的函数签名，数据格式适配（DataFrame/Series），字段名映射，错误码兼容，98 个测试用例 |
| G28 | Qlib/RD-Agent 适配器 | v2.0.0 | 新增 qlib_adapter/ 模块，Qlib DataProvider 完整接口实现，表达式引擎支持，数据格式双向转换器，99 个测试用例 |

## v1.3.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G19 | BaseTool 接口层 | v1.3.0 | 新增 DataCoreBaseTool 基类（兼容 LangChain 协议），23 个 Tool，all_tools 自动发现机制 |
| G20 | 复权/换月引擎 | v1.3.0 | 新增 adjustment/ 模块，股票前复权/后复权/不复权，期货主力连续合约（3种换月方式），换月价差调整（3种方式） |
| G21 | 周期转换引擎 | v1.3.0 | 新增 resampler/ 模块，1m→5m→15m→30m→60m→daily→weekly→monthly 全周期支持，OHLCV 正确聚合，auto 模式 |
| G22 | 消费者反馈通道 | v1.3.0 | 新增 issue.py，IssueRegistry + DataIssue + IssueType，report_issue() API，自动降级应对，get_health() 集成 |
| G23 | 数据清洗模块 | v1.3.0 | 新增 cleaning/ 模块，unit_unify / date_align / duplicate_merge / outlier_filter |
| G24 | 数据校验模块 | v1.3.0 | 新增 validation/ 模块，weight_score / cross_source / missing_detect / cal_math |
| G25 | 采集模块骨架 | v1.3.0 | 新增 collectors/ 模块骨架，web_crawl / open_source / local_doc / search |
| G26 | 运维工具模块 | v1.3.0 | 新增 operations/ 模块，crawl_retry / error_log / config_tools |

## v1.2.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G17 | 技术指标模块 | v1.2.0 | 新增 indicators/ 模块（从 FDC 吸收），37+ 基础指标，三层路由体系（TDX→numpy→TA-Lib），趋势成熟度评估 |
| G18 | 期货数据源扩展 | v1.2.0 | 新增 3 个期货数据源（QMT/TqSdk/WebFallback），期货降级链从 4 源扩展为 7 源 |

## v1.1.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G13 | 异步数据接口 | v1.1.0 | 新增 AsyncDataProvider（api_async.py），基于 run_in_executor 线程池桥接同步代码，提供异步双接口 |
| G14 | F10 综合报告 | v1.1.0 | 新增 F10 综合报告（api_f10.py + UnifiedDataProvider.get_f10），聚合期限结构/价差/基差/仓单/持仓排名 |
| G15 | core 共享基础设施 | v1.1.0 | 新增 datacore/core/ 模块（types.py + data_freshness.py + __init__.py），提供 KlineBar/QuoteData/FreshnessStatus 核心类型 |
| G16 | 数据新鲜度评估 | v1.1.0 | 新增 DataFreshnessAssessor 数据新鲜度评估器，三级状态（FRESH/STALE/EXPIRED），可观测性完整 |

## v1.0.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G12 | P2 基本面LLM加工（研报摘要） | v1.0.0 | Phase 6 已实现基本面 LLM 加工模块（fundamental_llm.py），含研报摘要 + 财报提取，12 个测试用例 |

## v0.6.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G11 | P2 LLM 情绪打分实际接入 | v0.6.0 | Phase 6 实现 LLM 情绪打分端到端验证（15 个测试），含真实 API 调用路径 |

## v0.5.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G03 | 国信 HTTP 数据源 | v0.5.0 | 正式接入 GuosenProvider，含 mock 测试 7 个 |
| G07 | 新闻数据源实际接入 | v0.5.0 | 财联社/华尔街见闻/东方财富研报 HTTP 抓取实现，含 mock 测试 19 个 |
| G08 | 国家统计局/央行宏观源 | v0.5.0 | 新增 national_bureau.py / pboc.py，3 源降级链，mock 测试 28 个 |
| G09 | 期货基本面数据抓取 | v0.5.0 | 新增 exchange_api.py / shengyishe.py，4 源降级链，mock 测试 6 个 |
| D01 | 基差近似算法 | v0.5.0 | 国信 base 近似算法已通过 shengyishe 真实现货数据源修复 |
| D03 | news provider 异常处理 | v0.5.0 | 新闻数据源 HTTP 异常路径已通过 mock 测试覆盖 |
| D05 | DuckDB 未接入 api.py | v0.5.0 | DuckDB 已接入 api.py 缓存层（MemoryCache → DuckDB → HTTP） |

## v0.4.0 已关闭差距

| ID | 标题 | 关闭版本 | 说明 |
|:---|:-----|:---------|:-----|
| G01 | 熔断器 | v0.4.0 | 实现 Breaker 类（CLOSED/OPEN/HALF_OPEN） |
| G02 | DuckDB 集成 | v0.4.0 | store/duckdb.py 新增加密持久化 store/load 方法 |
| G04 | 健康检查接口 | v0.4.0 | UnifiedDataProvider 新增 get_health() 方法 |
| G05 | 指标收集 | v0.4.0 | 新增 MetricsCollector（成功率/延迟/缓存命中率） |
| G06 | ETF/CB/REIT 支持 | v0.4.0 | DataType 已定义，基础数据获取已实现 |

## v0.3.0 已关闭差距

| 标题 | 关闭版本 | 说明 |
|:-----|:---------|:-----|
| SENTIMENT DataType 缺失 | v0.3.0 | 新增 SENTIMENT 枚举 + 情绪加工管线 |
| MARKET_STATE DataType 缺失 | v0.3.0 | 新增 MARKET_STATE 枚举 + 市场制度检测 |
| 情绪打分能力缺失 | v0.3.0 | 实现规则基线 + LLM 骨架（含降级） |
| 情绪聚合能力缺失 | v0.3.0 | 实现时间衰减+置信度加权聚合 |
| 市场制度检测缺失 | v0.3.0 | 实现 bull/bear/sideways 检测 |
| NEWS/MACRO 未接入统一API | v0.3.0 | 已接入 UnifiedDataProvider |

## v0.2.0 已关闭差距

| 标题 | 关闭版本 | 说明 |
|:-----|:---------|:-----|
| 期货特异 DataType 缺失 | v0.2.0 | 新增 6 个期货特异类型 |
| ETF/可转债 DataType 缺失 | v0.2.0 | 新增 6 个 ETF/CB 类型 |
| 新闻资讯模块缺失 | v0.2.0 | 新增 news/ 模块 + 分类器 |
| 宏观数据模块缺失 | v0.2.0 | 新增 macro/ 模块 |

## 差距关闭统计

| 版本 | 新增 | 关闭 | 累计关闭 |
|:-----|:-----|:-----|:---------|
| v0.2.0 | 4 | 4 | 4 |
| v0.3.0 | 6 | 6 | 10 |
| v0.4.0 | 6 (G01-G06) | 6 | 16 |
| v0.5.0 | 2 (G11, G12) | 7 (G03, G07, G08, G09, D01, D03, D05) | 23 |
| v0.6.0 | 0 | 1 (G11) | 24 |
| v1.0.0 | 0 | 1 (G12) | 25 |
| v1.1.0 | 4 (G13-G16) | 4 (G13-G16) | 29 |
| v1.2.0 | 2 (G17-G18) | 2 (G17-G18) | 31 |
| v1.3.0 | 8 (G19-G26) | 8 (G19-G26) | 39 |
| v2.0.0 | 2 (G27-G28) | 2 (G27-G28) | 41 |
| v2.1.0 | 2 (G29-G30) | 2 (G29-G30) | 43 |
| v2.2.0 | 1 (G31) | 1 (G31) | 44 |
| v2.3.0 | 2 (G32-G33) | 2 (G32-G33) | 46 |
| v2.4.0 | 1 (G34) | 1 (G34) | 47 |

## 最终状态

v2.4.0 所有已登记差距（G01-G34, D01-D05）全部关闭。项目已达到统一数据枢纽完整标准 + 缺口补全 + Prometheus 可观测性集成 + FDT 集成修复 + Provider adjustment 参数打通，observability.py + metrics_endpoint.py 全部交付，SymbolRegistry A 股自动识别 + 东方财富期货 secid 修复 + Provider 复权参数可配置，1984 测试全部通过（新增 20 个 adjustment 测试），88% 覆盖率（核心模块接近 100%），ruff 代码审计零错误。消费端可通过 adjustment="none" 获取未复权原始数据。
