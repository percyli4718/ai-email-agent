# AI Email Agent 用户操作手册

**版本**: 1.0
**日期**: 2026-03-30
**项目**: AI Email Agent

---

## 目录

1. [快速开始](#1-快速开始)
2. [环境准备](#2-环境准备)
3. [安装步骤](#3-安装步骤)
4. [运行测试](#4-运行测试)
5. [启动应用](#5-启动应用)
6. [API 使用](#6-_api-使用)
7. [前端界面](#7-前端界面)
8. [常见问题](#8-常见问题)

---

## 1. 快速开始

```bash
# 克隆仓库
git clone git@github.com:percyli4718/ai-email-agent.git
cd ai-email-agent

# 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 ANTHROPIC_API_KEY

# 运行测试
pytest tests/unit/ -v

# 启动应用
python -m uvicorn src.email_agent.main:app --reload

# 访问前端 (开发中)
cd frontend && npm install && npm run dev
```

---

## 2. 环境准备

### 2.1 系统要求

| 组件 | 版本要求 | 检查命令 |
|------|----------|----------|
| Python | 3.10+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| pip | 23.0+ | `pip --version` |

### 2.2 必需 API Key

| 服务 | 环境变量 | 获取方式 |
|------|----------|----------|
| Anthropic API | `ANTHROPIC_API_KEY` | https://console.anthropic.com |

### 2.3 可选服务

| 服务 | 用途 | 环境变量 |
|------|------|----------|
| Ollama | 本地 Embedding | `OLLAMA_HOST` |
| ChromaDB | 向量数据库 | `CHROMA_PERSIST_DIR` |

---

## 3. 安装步骤

### 3.1 后端安装

```bash
# 1. 克隆仓库
git clone git@github.com:percyli4718/ai-email-agent.git
cd ai-email-agent

# 2. 创建虚拟环境
python3 -m venv .venv

# 3. 激活虚拟环境
# Linux/Mac
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 安装为可编辑包
pip install -e .
```

### 3.2 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 或使用 yarn
yarn install
```

### 3.3 环境配置

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑 .env 文件
cat .env
```

**.env 配置说明**:

```bash
# 必填：Anthropic API Key
ANTHROPIC_API_KEY=your-api-key-here

# 可选：自定义配置
ENV=development
DATABASE_URL=sqlite+aiosqlite:///./data/email_agent.db
CHROMA_PERSIST_DIR=./data/chroma
OLLAMA_HOST=localhost:11434
MAX_SONNET_COST=0.10
MAX_OPUS_COST=0.50
TARGET_SONNET_RATE=0.8
LOG_LEVEL=INFO
```

---

## 4. 运行测试

### 4.1 运行所有单元测试

```bash
# 激活虚拟环境后
pytest tests/unit/ -v
```

**预期输出**:
```
============================= test session starts ==============================
collected 22 items

tests/unit/test_agents.py::test_ceo_decomposes_inquiry PASSED            [  4%]
tests/unit/test_agents.py::test_dependency_graph_tracks_dependencies PASSED [  9%]
tests/unit/test_classifier.py::test_classifier_parses_response PASSED    [ 13%]
...
tests/unit/test_tracing.py::test_trace_span_context_manager PASSED       [100%]

============================== 22 passed in 1.40s ==============================
```

### 4.2 运行特定测试文件

```bash
# 只测试分类器
pytest tests/unit/test_classifier.py -v

# 只测试生成器
pytest tests/unit/test_generator.py -v

# 只测试 Agent 系统
pytest tests/unit/test_agents.py -v
```

### 4.3 运行测试并生成覆盖率报告

```bash
# 生成 HTML 覆盖率报告
pytest --cov=src/email_agent --cov-report=html tests/unit/

# 打开报告
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov\index.html  # Windows
```

### 4.4 测试命令速查表

| 命令 | 说明 |
|------|------|
| `pytest tests/unit/ -v` | 详细输出运行所有测试 |
| `pytest tests/unit/ -q` | 简洁输出 |
| `pytest tests/unit/ -k classifier` | 只运行包含"classifier"的测试 |
| `pytest --tb=short` | 简短错误追踪 |
| `pytest --cov=src/email_agent` | 生成覆盖率报告 |

---

## 5. 启动应用

### 5.1 启动后端服务

```bash
# 在项目根目录，激活虚拟环境后
python -m uvicorn src.email_agent.main:app --reload --host 0.0.0.0 --port 8000
```

**启动日志**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     application_starting env=development
INFO:     database_initialized url=sqlite+aiosqlite:///./data/email_agent.db
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 5.2 访问 API 文档

浏览器打开：http://localhost:8000/docs

![API Docs](https://via.placeholder.com/800x600?text=Swagger+UI+Preview)

### 5.3 启动前端开发服务器

```bash
cd frontend
npm run dev
```

**访问地址**: http://localhost:5173

---

## 6. API 使用

### 6.1 健康检查

```bash
curl http://localhost:8000/health
```

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-30T12:00:00Z"
}
```

### 6.2 处理邮件

```bash
curl -X POST http://localhost:8000/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Bulk Order Inquiry",
    "body": "We want to order Paracetamol 500mg, 50000 units.",
    "from": "customer@example.com"
  }'
```

**响应**:
```json
{
  "email_id": "email-12345",
  "status": "processing",
  "classification": {
    "type": "inquiry",
    "priority_score": 0.92,
    "suggested_route": "quote_flow"
  }
}
```

### 6.3 获取处理状态

```bash
curl http://localhost:8000/api/emails/email-12345
```

### 6.4 获取 Metrics

```bash
curl http://localhost:8000/api/metrics
```

**响应**:
```json
{
  "emails_processed": 247,
  "avg_processing_time_ms": 1200,
  "avg_cost_per_email": 0.018,
  "classification_accuracy": 0.983,
  "sonnet_routing_rate": 0.82
}
```

### 6.5 获取 Traces

```bash
curl http://localhost:8000/api/traces
```

### 6.6 API 端点速查表

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 根路径，返回服务信息 |
| `/health` | GET | 健康检查 |
| `/api/emails` | POST | 提交新邮件处理 |
| `/api/emails/{id}` | GET | 获取邮件处理状态 |
| `/api/metrics` | GET | 获取系统指标 |
| `/api/traces` | GET | 获取分布式追踪数据 |

---

## 7. 前端界面

### 7.1 访问界面

浏览器打开：http://localhost:5173

### 7.2 界面导航

| Tab | 功能 | 说明 |
|-----|------|------|
| 📧 Inbox | 邮件列表 | 查看所有邮件及处理状态 |
| 📊 Metrics | 指标仪表盘 | 核心系统指标展示 |
| 🤖 Agents | Agent 监控 | 查看 Agent 执行状态和预算 |

### 7.3 Inbox 界面

- **状态指示器**:
  - 🟢 绿色 = 待处理 (pending)
  - 🟡 黄色 = 处理中 (processing)
  - ⚪ 灰色 = 已完成 (completed)

- **优先级徽章**:
  - 🔴 HIGH = 高优先级
  - 🟡 MEDIUM = 中优先级
  - ⚪ LOW = 低优先级

### 7.4 Metrics 界面

显示 6 个核心指标:
1. 今日邮件数
2. 平均处理延迟
3. 平均 Token 成本
4. 分类准确率
5. Sonnet 路由率
6. Prompt 版本数

### 7.5 Agents 界面

- CEO Agent 状态
- 子 Agent 列表 (价格/合规/物流/回复)
- 预算消耗进度条

---

## 8. 常见问题

### 8.1 安装问题

**Q: pip install 失败，提示依赖冲突**

A: 尝试更新 pip 后重新安装:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Q: 前端 npm install 失败**

A: 检查 Node.js 版本:
```bash
node --version  # 需要 18+
npm --version
```

### 8.2 测试问题

**Q: 测试失败，提示 ModuleNotFoundError**

A: 确保已安装为可编辑包:
```bash
pip install -e .
```

**Q: 测试失败，提示 ANTHROPIC_API_KEY 验证错误**

A: 检查 .env 文件配置:
```bash
cat .env | grep ANTHROPIC
# 确保有有效值
```

### 8.3 运行问题

**Q: 后端启动失败，端口被占用**

A: 更换端口:
```bash
python -m uvicorn src.email_agent.main:app --port 8001
```

**Q: 前端无法连接后端**

A: 检查 CORS 配置，确保后端允许前端端口访问。

### 8.4 获取更多帮助

```bash
# 查看项目 README
cat README.md

# 查看设计文档
cat docs/superpowers/specs/ai-email-agent-design.md

# 查看开发 SOP
cat docs/superpowers/SOP-ai-email-agent-development.md
```

---

## 附录 A: 项目结构

```
ai-email-agent/
├── src/email_agent/
│   ├── layer1/          # 分类路由
│   ├── layer2/          # 上下文检索
│   ├── layer3/          # 分析生成
│   ├── agents/          # Agent 系统
│   ├── observability/   # 可观测性
│   ├── storage/         # 数据存储
│   ├── api/             # API 路由
│   ├── config.py        # 配置
│   └── main.py          # 应用入口
├── frontend/
│   └── src/
│       ├── App.tsx      # 主组件
│       └── main.tsx     # 入口
├── tests/unit/          # 单元测试
├── docs/                # 文档
├── requirements.txt     # 依赖
└── .env                 # 环境配置
```

---

## 附录 B: 依赖说明

**后端依赖** (requirements.txt):
| 包 | 版本 | 用途 |
|----|------|------|
| fastapi | 0.109.0 | Web 框架 |
| uvicorn | 0.27.0 | ASGI 服务器 |
| anthropic | 0.18.0 | Claude API |
| chromadb | 0.4.22 | 向量数据库 |
| ollama | >=0.1.7 | 本地 Embedding |
| sqlalchemy | 2.0.25 | ORM |
| pydantic | 2.5.3 | 数据验证 |
| structlog | 24.1.0 | 日志 |

**前端依赖** (package.json):
| 包 | 版本 | 用途 |
|----|------|------|
| react | 18.x | UI 框架 |
| typescript | 5.x | 类型系统 |
| tailwindcss | 3.x | CSS 框架 |
| vite | 5.x | 构建工具 |

---

**文档结束**

如有疑问，请查看项目 README.md 或提交 Issue。
