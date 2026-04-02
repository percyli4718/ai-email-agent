# AI Email Agent 部署指南

本文档提供 AI Email Agent 的生产环境部署说明。

## 目录

- [快速开始](#快速开始)
- [Docker 部署](#docker-部署)
- [环境变量配置](#环境变量配置)
- [健康检查](#健康检查)
- [日志管理](#日志管理)
- [性能调优](#性能调优)
- [故障排查](#故障排查)

---

## 快速开始

### 前置条件

- Docker 20.10+
- Docker Compose 2.0+
- Anthropic API Key

### 1. 克隆仓库

```bash
git clone <repo-url>
cd ai-email-agent
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入 ANTHROPIC_API_KEY
```

### 3. 启动服务

```bash
# 启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

### 4. 访问应用

- 前端：http://localhost
- 后端 API：http://localhost:8000
- API 健康检查：http://localhost:8000/api/health

---

## Docker 部署

### 构建镜像

```bash
# 构建后端镜像
docker build -t email-agent-backend .

# 构建前端镜像
docker build -t email-agent-frontend ./frontend
```

### 运行容器

```bash
# 运行后端
docker run -d \
  --name email-agent-backend \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -e ANTHROPIC_API_KEY=your-key \
  email-agent-backend

# 运行前端
docker run -d \
  --name email-agent-frontend \
  -p 80:80 \
  email-agent-frontend
```

### Docker Compose

```bash
# 启动所有服务
docker compose up -d

# 启动并启用 Ollama (需要 GPU)
docker compose --profile with-ollama up -d

# 查看服务状态
docker compose ps

# 重启服务
docker compose restart

# 更新镜像
docker compose pull
docker compose up -d --force-recreate
```

---

## 环境变量配置

### 必需变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | `sk-ant-...` |
| `DATABASE_URL` | 数据库连接 URL | `sqlite+aiosqlite:///./data/email_agent.db` |
| `PORT` | 后端服务端口 | `8000` |

### 可选变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `DEFAULT_AGENT_BUDGET` | Agent 默认预算 | `0.50` |
| `CHROMA_DB_PATH` | ChromaDB 数据路径 | `./data/chroma` |
| `OLLAMA_BASE_URL` | Ollama 服务地址 | `http://localhost:11434` |

### .env 示例

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-...
DATABASE_URL=sqlite+aiosqlite:///./data/email_agent.db
PORT=8000
LOG_LEVEL=INFO
DEFAULT_AGENT_BUDGET=0.50
```

---

## 健康检查

### API 端点

```bash
# 健康检查
curl http://localhost:8000/api/health

# 响应示例
{"status": "healthy", "timestamp": "2026-04-02T10:00:00Z"}
```

### Prometheus 指标

```bash
# 获取指标
curl http://localhost:8000/api/metrics/prometheus

# 获取指标摘要
curl http://localhost:8000/api/metrics
```

### Docker 健康检查

```bash
# 查看容器健康状态
docker inspect --format='{{.State.Health.Status}}' email-agent-backend

# 查看健康检查日志
docker inspect --format='{{json .State.Health}}' email-agent-backend | jq
```

---

## 日志管理

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看后端日志
docker compose logs -f backend

# 查看前端日志
docker compose logs -f frontend

# 最近 100 行
docker compose logs --tail=100 backend
```

### 日志轮转

创建 `docker-compose.override.yml`:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
```

### 导出日志

```bash
# 导出日志到文件
docker compose logs backend > backend.log
docker compose logs frontend > frontend.log
```

---

## 性能调优

### 数据库优化

```bash
# 定期清理旧数据
sqlite3 ./data/email_agent.db "DELETE FROM emails WHERE received_at < datetime('now', '-30 days');"
```

### 连接池配置

在 `config.py` 中调整:

```python
# 增加连接池大小
engine = create_async_engine(
    database_url,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

### 并发配置

```bash
# 使用 gunicorn 运行 (生产环境)
docker run -e WORKERS=4 email-agent-backend
```

---

## 故障排查

### 常见问题

#### 1. 容器无法启动

```bash
# 检查日志
docker compose logs backend

# 检查端口占用
docker compose ps
netstat -tlnp | grep 8000
```

#### 2. 数据库锁定

```bash
# 删除锁文件
rm ./data/email_agent.db-shm ./data/email_agent.db-wal

# 重启服务
docker compose restart backend
```

#### 3. API 密钥无效

```bash
# 验证密钥
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
  https://api.anthropic.com/v1/models

# 检查环境变量
docker compose exec backend env | grep ANTHROPIC
```

### 调试模式

```bash
# 启用调试日志
docker compose exec backend \
  sh -c "LOG_LEVEL=DEBUG python -m email_agent.main"
```

---

## 备份与恢复

### 备份数据

```bash
# 备份数据库
docker compose exec backend \
  cp /app/data/email_agent.db /tmp/backup.db

docker cp email-agent-backend:/tmp/backup.db ./backup.db
```

### 恢复数据

```bash
# 停止服务
docker compose down

# 恢复数据库
docker cp ./backup.db email-agent-backend:/app/data/email_agent.db

# 启动服务
docker compose up -d
```

---

## 安全建议

1. **不要提交 `.env` 文件** - 确保 `.env` 在 `.gitignore` 中
2. **使用 HTTPS** - 生产环境配置反向代理 (Nginx/Traefik) 并启用 HTTPS
3. **限制 API 访问** - 使用防火墙规则限制 API 端点访问
4. **定期更新镜像** - 定期拉取最新安全补丁

---

## 监控告警

### Prometheus + Grafana

1. 添加数据源：`http://backend:8000/api/metrics/prometheus`
2. 创建 Dashboard 监控:
   - 邮件处理数量
   - 平均处理时间
   - 预算使用率
   - API 错误率

### 告警规则示例

```yaml
# prometheus_alerts.yml
groups:
  - name: email_agent
    rules:
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "高错误率"
          
      - alert: BudgetExceeded
        expr: budget_spent > 0.45
        annotations:
          summary: "预算即将超支"
```
