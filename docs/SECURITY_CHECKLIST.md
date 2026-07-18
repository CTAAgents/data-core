# Data-Core 安全配置检查清单

> 版本: v1.0.0 | 更新: 2026-07-19

## 检查项

| # | 检查项 | 状态 | 说明 |
|:-:|:-------|:-----|:-----|
| 1 | 所有敏感信息通过环境变量注入 | ✅ | 见 config.py，全部使用 `DATACORE_*` 环境变量 |
| 2 | 无硬编码密钥/密码/API Key | ✅ | Grep 审计未发现任何硬编码凭据 |
| 3 | 参数化 SQL 查询 | ✅ | DuckDB 使用 `?` 占位符，PostgreSQL 使用 `%s` 占位符 |
| 4 | HTTP 请求超时配置 | ✅ | 全部 provider 设置 3s~10s 超时 |
| 5 | follow_redirects 受控 | ✅ | 仅 shengyishe provider 启用 |
| 6 | YAML 安全加载 | ✅ | 使用 `yaml.safe_load` 解析 |
| 7 | .gitignore 排除敏感文件 | ✅ | `.env`, `*.key`, `settings.yaml` 已排除 |

## 生产环境建议

- 使用 `.env.production` 管理环境变量，确保加入 `.gitignore`
- API Key 定期轮换（建议 90 天）
- 生产环境日志级别设置为 `WARNING` 避免敏感数据泄露
- 如使用国信证券 API，确保 HTTPS 传输
