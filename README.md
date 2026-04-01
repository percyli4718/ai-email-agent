# AI Email Agent

AI-powered email processing system for pharmaceutical distribution.

**核心能力:**
- 📧 3-Layer AI 架构处理邮件分类、检索和报价生成
- 🤖 CEO Agent 任务分解与多 Agent 协同
- 💰 预算控制系统（$5 总预算，单次 L1 ~$0.003，L3 ~$0.01-0.10）
- 🔍 语义搜索 + 数据库检索（ChromaDB + Ollama 本地 embedding）
- 📊 完整可观测性（指标、追踪、预算事件）

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        非结构化邮件输入                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: 分类 (Claude Sonnet 4)     成本：~$0.003/邮件           │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│ │ 邮件类型识别  │ │ 优先级评分    │ │ 建议路由      │             │
│ └──────────────┘ └──────────────┘ └──────────────┘             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: 检索 (ChromaDB + Ollama + DB)  成本：~$0.001/次        │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│ │ 相似邮件检索  │ │ 定价政策查询  │ │ 合规要求查询  │             │
│ │ (ChromaDB)   │ │ (SQLAlchemy) │ │ (SQLAlchemy) │             │
│ └──────────────┘ └──────────────┘ └──────────────┘             │
│ 使用 Ollama nomic-embed-text 本地 embedding (768 维)            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: 生成 (Claude Opus 4/Sonnet 4 智能路由)                  │
│ 成本：Sonnet ~$0.01-0.05/次，Opus ~$0.05-0.10/次               │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│ │ 报价生成      │ │ 多语言回复    │ │ 合规检查      │             │
│ └──────────────┘ └──────────────┘ └──────────────┘             │
│ 智能路由策略：80% 简单任务 → Sonnet，20% 复杂任务 → Opus           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CEO Agent 任务协调（可选）预算：$0.10-0.15/任务                  │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│ │ Price Agent  │→│Compliance    │→│Logistics     │→ Reply      │
│ │ $0.10        │ │Agent $0.15   │ │Agent $0.12   │ Agent $0.08 │
│ └──────────────┘ └──────────────┘ └──────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 前置条件

- Python 3.11+
- Node.js 18+
- Ollama 本地运行
- Anthropic API Key（用于 L1/L3）

### 安装步骤

```bash
# 1. 克隆仓库
git clone <repo-url>
cd ai-email-agent

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 安装前端依赖
cd frontend
npm install
cd ..

# 4. 复制环境变量文件
cp .env.example .env

# 5. 编辑 .env 配置
# 必要配置:
#   ANTHROPIC_API_KEY=your_key_here
#   DATABASE_URL=sqlite+aiosqlite:///./data/email_agent.db
#   CHROMA_DB_PATH=./data/chroma
#   OLLAMA_BASE_URL=http://localhost:11434

# 6. 初始化数据库
python scripts/seed_data.py

# 7. 注入定价和合规数据
python scripts/seed_pricing_compliance.py

# 8. 初始化 ChromaDB
python -c "from email_agent.retriever.chroma_init import initialize_chromadb; initialize_chromadb()"
```

### 运行服务

```bash
# 后端服务
python -m email_agent.main

# 前端开发服务器
cd frontend
npm run dev
```

访问 http://localhost:5173 查看前端界面

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/emails` | GET | 获取邮件列表 |
| `/api/emails/{id}` | GET | 获取邮件详情 |
| `/api/emails/{id}/process` | POST | 处理邮件（L1→L2→L3） |
| `/api/emails/{id}/analysis` | GET | 获取分析结果 |
| `/api/metrics` | GET | 可观测性指标 |
| `/api/traces` | GET | 分布式追踪 |
| `/api/health` | GET | 健康检查 |

## 邮件生成器

### 生成测试邮件

```bash
# 前端界面
# 在 Inbox 页面顶部点击"➕ 创建新邮件"按钮

# API 调用
curl -X POST http://localhost:8000/api/emails/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 5, "auto_process": false}'

# 注入模板数据
python scripts/seed_email_templates.py
```

### 预算估算

| 操作 | 成本 |
|------|------|
| 仅生成邮件 | $0 (本地生成) |
| 自动触发处理 | ~$0.02-0.05/封 |
| 批量生成 10 封 + 自动处理 | ~$0.20-0.50 |
```

## 测试指南

### 运行所有测试

```bash
# 完整测试套件
pytest

# 带覆盖率报告
pytest --cov=email_agent --cov-report=html

# 单个测试文件
pytest tests/layer2/test_retriever_e2e.py -v
```

### 分层测试

**Layer 1 分类器测试** (需要 API Key，~$0.01):
```bash
pytest tests/layer1/test_classifier_e2e.py -v
```

**Layer 2 检索器测试** (不需要 API Key):
```bash
pytest tests/layer2/test_retriever_e2e.py -v
```

**Layer 3 生成器测试** (需要 API Key，~$0.01-0.05):
```bash
pytest tests/layer3/test_generator_e2e.py -v
```

**CEO Agent 测试** (不需要 API Key):
```bash
pytest tests/agents/test_ceo_agent_e2e.py -v
```

**完整流程测试** (需要 API Key，~$0.02-0.10):
```bash
pytest tests/e2e/test_full_pipeline.py -v
```

### 预算估算

| 测试类型 | 单次成本 | 推荐频率 |
|---------|---------|---------|
| Layer 1 E2E | ~$0.01 | 每日 |
| Layer 2 E2E | ~$0.001 | 每次提交 |
| Layer 3 E2E | ~$0.01-0.05 | 每日 |
| 完整流程 | ~$0.02-0.10 | 每周 |
| CEO Agent | $0 (mock) | 每次提交 |

## 项目结构

```
ai-email-agent/
├── src/email_agent/
│   ├── layer1/
│   │   ├── classifier.py        # L1 分类器 (Sonnet)
│   │   └── types.py             # 分类结果类型定义
│   ├── layer2/
│   │   ├── retriever.py         # L2 检索器
│   │   ├── chroma_init.py       # ChromaDB 初始化
│   │   └── vector_store.py      # 向量存储
│   ├── layer3/
│   │   ├── generator.py         # L3 生成器 (Opus/Sonnet)
│   │   └── smart_router.py      # 智能模型路由
│   ├── agents/
│   │   ├── ceo_agent.py         # CEO Agent (任务分解)
│   │   ├── price_agent.py       # 价格 Agent
│   │   ├── compliance_agent.py  # 合规 Agent
│   │   ├── logistics_agent.py   # 物流 Agent
│   │   └── reply_agent.py       # 回复 Agent
│   ├── observability/
│   │   ├── metrics.py           # Prometheus 指标
│   │   ├── budget_tracker.py    # 预算追踪
│   │   └── tracer.py            # 分布式追踪
│   ├── storage/
│   │   ├── models.py            # SQLAlchemy 模型
│   │   ├── database.py          # 数据库操作
│   │   └── connection.py        # 连接管理
│   └── api/
│       ├── routes.py            # FastAPI 路由
│       └── schemas.py           # Pydantic 模式
├── frontend/                    # React + Tailwind UI
├── tests/
│   ├── layer1/                  # L1 测试
│   ├── layer2/                  # L2 测试
│   ├── layer3/                  # L3 测试
│   ├── agents/                  # Agent 测试
│   └── e2e/                     # 端到端测试
├── scripts/
│   ├── seed_data.py             # 种子数据注入
│   └── seed_pricing_compliance.py  # 定价/合规数据
└── data/                        # 数据库和向量存储
```

## 演示脚本

### 场景 1: 欧洲客户询价 (标准流程)

```bash
# 1. 准备测试邮件
curl -X POST http://localhost:8000/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "from_email": "john@pharmacom.co.uk",
    "subject": "RFQ: Paracetamol 500mg - 1000 boxes",
    "body": "Dear Supplier, We are interested in purchasing Paracetamol 500mg 1000 boxes for delivery to London, UK. Please provide your best quote."
  }'

# 2. 处理邮件（L1→L2→L3）
curl -X POST http://localhost:8000/api/emails/{email_id}/process

# 3. 查看结果
curl http://localhost:8000/api/emails/{email_id}/analysis
```

**预期结果:**
- L1: 分类为 "inquiry", 优先级 0.8, 建议路由 "quote_flow"
- L2: 检索到相似邮件 3 封，欧洲定价政策，CE/GMP 合规要求
- L3: 生成完整报价单（FOB London, $2.80/box, 14 天交货）

### 场景 2: 南美客户询价 (高复杂度 → Opus)

```bash
# 高复杂度邮件触发 Opus 模型
curl -X POST http://localhost:8000/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "from_email": "ana@pharma.br",
    "subject": "RFQ: Amoxicillin 500mg - 5000 boxes to Brazil",
    "body": "We need Amoxicillin 500mg 5000 boxes with ANVISA registration, GMP certificate, and CIF Santos terms. Delivery within 30 days required."
  }'
```

**预期结果:**
- 智能路由识别为高复杂度（20% 概率 → Opus）
- L2 检索南美合规要求（ANVISA, Import Permit）
- L3 生成包含所有证书的详细报价

### 场景 3: CEO Agent 任务分解

```python
from email_agent.config import settings
from email_agent.agents.ceo_agent import CEOAgent

ceo = CEOAgent(settings)

# 任务分解
graph = ceo.decompose_inquiry(email_body, classification)

# 执行任务图
import asyncio
results = asyncio.run(ceo.execute_graph(graph, email_id))

# 查看结果
for task_id, result in results.items():
    print(f"Task {task_id}: {result}")
```

**预期输出:**
```
[price_agent] 预算：$0.10, 状态：completed
[compliance_agent] 预算：$0.15, 状态：completed
[logistics_agent] 预算：$0.12, 状态：completed
[reply_agent] 预算：$0.08, 状态：completed
总成本：$0.45
```

## 预算控制策略

### 硬限制配置

```python
# .env
DEFAULT_AGENT_BUDGET=0.50      # 单个 Agent 预算上限
DAILY_BUDGET_LIMIT=5.00        # 每日总预算
COST_PER_WARNING=0.01          # 成本警告阈值
```

### 智能路由策略

```python
# 简单任务 (80%) → Sonnet ($0.01-0.05)
# - 标准询价
# - 已有客户回复
# - 单产品查询

# 复杂任务 (20%) → Opus ($0.05-0.10)
# - 多产品国际订单
# - 需要特殊合规
# - 高价值客户 (Tier A)
```

### 成本优化建议

1. **开发阶段:** 使用 mock 数据测试 L2 检索
2. **回归测试:** 优先运行不需要 API Key 的测试
3. **CI/CD:** 仅在 nightly build 运行完整 L1→L2→L3 流程
4. **监控:** 设置预算警告邮件通知

## 故障排查

### ChromaDB 初始化失败

```bash
# 检查 Ollama 是否运行
ollama list

# 手动初始化 ChromaDB
python -c "from email_agent.retriever.chroma_init import initialize_chromadb; initialize_chromadb()"
```

### 数据库锁错误

```bash
# 删除数据库文件重新创建
rm data/email_agent.db
python scripts/seed_data.py
```

### API 调用失败

```bash
# 检查 API Key
echo $ANTHROPIC_API_KEY

# 测试连接
curl https://api.anthropic.com/v1/models \
  -H "Authorization: Bearer $ANTHROPIC_API_KEY"
```

## License

MIT
