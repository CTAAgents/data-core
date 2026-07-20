# Data-Core 部署指南

> 版本: v2.4.0 | 更新: 2026-07-20

## 目录

1. [快速部署](#1-快速部署)
2. [环境变量清单](#2-环境变量清单)
3. [监控接入](#3-监控接入)
4. [备份与恢复](#4-备份与恢复)
5. [性能调优](#5-性能调优)
6. [变更记录](#6-变更记录)

---

## 1. 快速部署

### 前置条件

- Python 3.10+
- Git

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/CTAAgents/data-core.git
cd data-core

# 2. 创建虚拟环境（推荐）
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

# 3. 安装
pip install -e ".[full]"

# 4. 验证
datacore status
```

### 环境变量

无需额外配置即可运行。可选配置见[环境变量清单](#2-环境变量清单)。

### 可选后端

PostgreSQL 或 Redis 后端需要独立安装，Data-Core 不负责管理这些服务。默认使用 DuckDB 零配置运行。

---

## 2. 环境变量清单

| 变量 | 必需 | 默认值 | 说明 |
|:-----|:-----|:-------|:-----|
| `DATACORE_STORE_BACKEND` | 否 | `duckdb` | 存储后端 (duckdb/postgres/redis) |
| `DATACORE_STORE_DUCKDB_PATH` | 否 | `~/.datacore/datacore.db` | DuckDB 数据库路径 |
| `DATACORE_STORE_POSTGRESQL_DSN` | 否 | - | PostgreSQL 连接 DSN |
| `DATACORE_STORE_REDIS_URL` | 否 | - | Redis 连接 URL |
| `DATACORE_CACHE_TTL` | 否 | `3600` | 内存缓存 TTL（秒）|
| `DATACORE_LOG_LEVEL` | 否 | `INFO` | 日志级别 |
| `DATACORE_LLM_API_KEY` | 否 | - | LLM API Key（情绪打分）|
| `DATACORE_LLM_MODEL` | 否 | `gpt-4o-mini` | LLM 模型 |
| `DATACORE_SOURCES_GUOSEN_API_KEY` | 否 | - | 国信证券 API Key |
| `DATACORE_SOURCES_TDX_LC_URL` | 否 | `http://127.0.0.1:17709/` | 通达信本地服务地址 |
| `DATACORE_METRICS_PORT` | 否 | `9090` | Prometheus 指标服务器端口 |
| `DATACORE_METRICS_ENABLED` | 否 | `true` | 是否启用 Prometheus 指标 |

### 安全注意事项

- **所有敏感信息通过环境变量注入，禁止硬编码**
- 生产环境使用 `.env.production` 文件（加入 `.gitignore`）
- API Key 定期轮换
- Prometheus `/metrics` 端点建议配置访问控制

---

## 3. 监控接入

### 3.1 健康检查接口

```bash
# HTTP 健康检查（需启动 API 服务）
curl http://localhost:8000/health
# 返回: {"status": "healthy", "version": "2.4.0", "sources": {...}}

# Prometheus 健康检查端点
curl http://localhost:9090/healthz
# 返回: {"status": "ok"}
```

### 3.2 Prometheus 指标

Data-Core v2.2.0 内置 Prometheus 可观测性集成，提供 11 个标准指标：

```bash
# 启动指标服务器
python -c "from datacore.metrics_endpoint import start_metrics_server; start_metrics_server()"

# 访问指标端点
curl http://localhost:9090/metrics
```

**可用指标**:

| 指标名 | 类型 | 说明 |
|:-------|:-----|:-----|
| `datacore_api_requests_total` | Counter | API 请求总数 |
| `datacore_api_request_duration_seconds` | Histogram | API 请求延迟分布 |
| `datacore_api_errors_total` | Counter | API 错误总数 |
| `datacore_source_degradations_total` | Counter | 数据源降级总次数 |
| `datacore_source_availability` | Gauge | 数据源可用性 (0.0~1.0) |
| `datacore_cache_hits_total` | Counter | 缓存命中次数 |
| `datacore_cache_misses_total` | Counter | 缓存未命中次数 |
| `datacore_resampler_operations_total` | Counter | 周期转换操作总数 |
| `datacore_issues_open` | Gauge | 当前未解决问题数 |
| `datacore_tool_invocations_total` | Counter | Tool 调用总数 |
| `datacore_tool_errors_total` | Counter | Tool 错误总数 |

**Prometheus 配置示例**:

```yaml
scrape_configs:
  - job_name: 'datacore'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: /metrics
```

### 3.3 日志

- 日志输出到 stdout/stderr
- 通过 `DATACORE_LOG_LEVEL` 控制日志级别
- 生产环境建议设置为 `WARNING`

---

## 4. 备份与恢复

### 4.1 DuckDB 备份

```bash
# 备份
cp /root/.datacore/datacore.db /backup/datacore-$(date +%Y%m%d).db

# 恢复
cp /backup/datacore-20260719.db /root/.datacore/datacore.db
```

### 4.2 PostgreSQL 备份

```bash
# 备份
pg_dump -h localhost -U datacore datacore > /backup/datacore-$(date +%Y%m%d).sql

# 恢复
psql -h localhost -U datacore datacore < /backup/datacore-20260719.sql
```

### 4.3 自动备份脚本

创建 `scripts/backup.sh`：

```bash
#!/bin/bash
BACKUP_DIR=/backup
DB_PATH=/root/.datacore/datacore.db
RETENTION_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份 DuckDB
cp $DB_PATH $BACKUP_DIR/datacore-$(date +%Y%m%d).db

# 清理过期备份
find $BACKUP_DIR -name "datacore-*.db" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_DIR/datacore-$(date +%Y%m%d).db"
```

---

## 5. 性能调优

### 5.1 缓存优化

| 配置 | 建议值 | 说明 |
|:-----|:-------|:-----|
| `DATACORE_CACHE_TTL` | 3600 (1h) | 高频查询可适当延长 |
| DuckDB 路径 | SSD 磁盘 | 避免使用网络存储 |

### 5.2 并发优化

- Data-Core 默认使用 HTTP Pull，适合低并发场景
- 高并发场景建议前置缓存层（Redis）
- 多实例部署时共享 DuckDB 文件需谨慎（DuckDB 单写入器）

### 5.3 内存管理

- MemoryCache 默认无大小限制
- 大量数据采集时可调用 `MemoryCache.purge()` 清理过期键
- 建议定期运行 `datacore status` 监控内存使用

### 5.4 复权/换月优化

- 期货主力连续建议使用 `adjustment="continuous"`（默认成交量加权）
- A 股建议使用 `adjustment="qfq"`（前复权）
- 周期转换自动从细粒度重采样，无需手动转换

---

## 6. 变更记录

| 日期 | 版本 | 更新内容 |
|:-----|:-----|:---------|
| 2026-07-20 | v2.4.0 | 更新版本号至 v2.4.0，新增 Prometheus 监控接入、11 个标准指标、环境变量扩展、复权/换月优化建议 |
| 2026-07-19 | v0.6.0 | 初始版本，包含基础部署指南、环境变量清单、备份策略 |
