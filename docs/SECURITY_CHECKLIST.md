# Data-Core 安全配置检查清单

> 版本: v2.4.0 | 更新: 2026-07-20

## 检查项

| # | 检查项 | 状态 | 说明 |
|:-:|:-------|:-----|:-----|
| 1 | 所有敏感信息通过环境变量注入 | ✅ | 见 config.py，全部使用 `DATACORE_*` 环境变量 |
| 2 | 无硬编码密钥/密码/API Key | ✅ | Grep 审计未发现任何硬编码凭据 |
| 3 | 参数化 SQL 查询 | ✅ | DuckDB 使用 `?` 占位符，PostgreSQL 使用 `%s` 占位符 |
| 4 | HTTP 请求超时配置 | ✅ | 全部 provider 设置 3s~10s 超时 |
| 5 | follow_redirects 受控 | ✅ | 仅 shengyishe provider 启用 |
| 6 | YAML 安全加载 | ✅ | 使用 `yaml.safe_load` 解析 |
| 7 | .gitignore 排除敏感文件 | ✅ | `.env`, `*.key`, `settings.yaml`, `*.db` 已排除 |
| 8 | BaseTool 参数校验 | ✅ | 23 个 Tool 全部配备 Pydantic args_schema，参数类型安全 |
| 9 | Prometheus 指标无敏感数据 | ✅ | 指标仅包含计数/延迟/可用性，无业务敏感数据 |
| 10 | 线程安全指标更新 | ✅ | observability.py 使用 threading.Lock 保护所有指标更新 |
| 11 | 可选依赖安全降级 | ✅ | pydantic/prometheus_client 未安装时自动降级，不影响核心功能 |
| 12 | API 层埋点无敏感信息 | ✅ | observe_api_call/observe_tool_call 装饰器仅记录端点名和调用状态 |

## 生产环境建议

- 使用 `.env.production` 管理环境变量，确保加入 `.gitignore`
- API Key 定期轮换（建议 90 天）
- 生产环境日志级别设置为 `WARNING` 避免敏感数据泄露
- 如使用国信证券 API，确保 HTTPS 传输
- Prometheus `/metrics` 端点建议配置访问控制（仅允许内网或认证后访问）
- 指标服务器端口（默认 9090）建议通过防火墙限制访问

## 变更记录

| 日期 | 版本 | 更新内容 |
|:-----|:-----|:---------|
| 2026-07-20 | v2.4.0 | 新增 BaseTool 参数校验、Prometheus 指标安全、线程安全、可选依赖降级、API 层埋点等 5 项检查 |
| 2026-07-19 | v1.0.0 | 初始版本，7 项安全检查清单 |
