# AI Agent 邮件处理系统设计文档

**版本**: 1.0
**日期**: 2026-03-29
**作者**: 资深 Java/AI 全栈工程师候选人
**面试职位**: AI 产品软件工程师（从 0 到 1）

---

## 1. 概述

### 1.1 项目背景

本系统是面试作品，直接对标招聘 JD 中的跨国药品分销 AI Agent 运营系统。核心目标是展示候选人具备：

- AI 工程化能力（RAG、向量检索、智能路由）
- 复杂系统架构能力（三层 AI 架构、Agent 合同制）
- 全栈开发能力（Python 后端 + 可观测性前端）
- 独立解决问题的能力（自驱动、自优化）

### 1.2 业务场景

**药品分销询盘处理**：接收来自巴西、中国等跨国客户的药品采购邮件，自动完成分类、检索、分析、报价全流程。

**核心流程**：
```
非结构化邮件 → AI 分类 → 上下文检索 → 结构化输出 → 业务动作
```

### 1.3 设计原则

| 原则 | 说明 |
|------|------|
| **直接对标 JD** | 每个功能模块都能在 JD 中找到对应要求 |
| **可演示性** | 面试时可现场跑通、可讲解架构决策 |
| **可观测性优先** | 所有 AI 调用、Agent 执行必须可追踪 |
| **进化式设计** | Prompt 可自动优化、系统可自我改进 |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         非结构化输入层                                │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 客户邮件 (英文/葡萄牙文/中文) + PDF 附件                           ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Layer 1: 分类路由 (Sonnet)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ 邮件类型识别  │  │ 优先级评分    │  │ 语言检测      │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │ 路由决策      │  │ 路由至 L2/人工/自动回复                         │  │
│  └──────────────┘  └──────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Layer 2: 上下文检索                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ ChromaDB     │  │ 客户历史     │  │ 价格政策库   │              │
│  │ 相似邮件     │  │ 对话记录     │  │ 合规要求     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐                                                  │
│  │ Wiki-Link    │  合同条款关联、政策引用链                           │
│  └──────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Layer 3: 分析生成                                  │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │ 智能路由      │  │ 80% Sonnet   │  │ 20% Opus     │              │
│  │ (成本优化)    │  │ (常规询盘)   │  │ (复杂条款)   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ 实体提取      │  │ 报价单生成   │  │ 回复草稿     │              │
│  │ 产品/数量/目的地│  │ JSON 格式     │  │ 多语言       │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         业务动作层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ 写入 CRM     │  │ 发送邮件      │  │ 触发合同     │              │
│  │ SQLite       │  │ SMTP/SendGrid│  │ Agent       │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Agent 合同制架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CEO Agent                                     │
│  职责：接收目标 → 解析为依赖图 → 分配子 Agent → 评审交付物               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   价格 Agent      │    │   合规 Agent      │    │   物流 Agent      │
│  查询价格库      │    │  检查出口许可    │    │  计算运费        │
│  预算：$0.10     │    │  预算：$0.15     │    │  预算：$0.12     │
│  写隔离 ✓        │    │  写隔离 ✓        │    │  写隔离 ✓        │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CEO 评审决策                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Promote      │  │ Redelegate   │  │ Reject       │              │
│  │ 批准并执行    │  │ 重新分配      │  │ 拒绝并记录   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. 核心模块设计

### 3.1 Layer 1: 分类路由模块

**输入**: 原始邮件（文本 + 附件）

**处理流程**:
1. 提取邮件正文和附件内容
2. 调用 Claude Sonnet 进行多标签分类
3. 输出结构化分类结果

**Prompt 设计**:
```python
classifier_prompt = """
你是一名药品分销公司的邮件分类专家。请分析以下邮件并输出 JSON：

{
  "type": "inquiry|complaint|question|contract|other",
  "priority_score": 0.0-1.0,
  "urgency": "low|medium|high",
  "language": "en|pt|zh",
  "products_mentioned": ["product1", "product2"],
  "customer_region": "brazil|china|other",
  "requires_human": boolean,
  "suggested_route": "quote_flow|complaint_flow|auto_reply|manual"
}

邮件内容：
{email_body}
"""
```

**输出示例**:
```json
{
  "type": "inquiry",
  "priority_score": 0.92,
  "urgency": "high",
  "language": "en",
  "products_mentioned": ["Paracetamol 500mg", "Amoxicillin 250mg"],
  "customer_region": "brazil",
  "requires_human": false,
  "suggested_route": "quote_flow"
}
```

### 3.2 Layer 2: 上下文检索模块

**组件**:
- **ChromaDB**: 存储历史邮件向量（Ollama mxb3embed-base 模型）
- **SQLite**: 客户信息、价格政策、合同条款
- **Wiki-Link**: 条款关联图谱

**检索策略**:
```python
async def retrieve_context(email_id: str, classification: dict) -> ContextResult:
    # 1. 向量检索：相似历史邮件
    similar_emails = chroma_collection.query(
        query_embedding=embed(email_body),
        n_results=3,
        where={"region": classification["customer_region"]}
    )

    # 2. 客户历史查询
    customer_history = db.query_customer(
        classification.get("customer_email")
    )

    # 3. 价格政策匹配
    pricing_policy = db.query_pricing(
        products=classification["products_mentioned"],
        region=classification["customer_region"]
    )

    # 4. 合规要求检查
    compliance = db.query_compliance(
        products=classification["products_mentioned"],
        destination=classification["customer_region"]
    )

    return ContextResult(
        similar_emails=similar_emails,
        customer_history=customer_history,
        pricing_policy=pricing_policy,
        compliance=compliance
    )
```

### 3.3 Layer 3: 分析生成模块

**智能路由策略**:
```python
async def intelligent_router(context: ContextResult) -> ModelChoice:
    # 简单查询：Sonnet（80% 场景）
    if context.complexity_score < 0.6:
        return ModelChoice.SONNET

    # 复杂条款分析：Opus（20% 场景）
    return ModelChoice.OPUS
```

**结构化输出 Prompt**:
```python
quote_generation_prompt = """
基于以下上下文，生成药品采购报价单：

【检索到的相似邮件】
{similar_emails}

【客户历史订单】
{customer_history}

【适用价格政策】
{pricing_policy}

【合规要求】
{compliance}

【原始询盘】
{original_email}

请输出 JSON 格式的报价单：
{
  "quote_id": "自动生成 UUID",
  "customer_email": "客户邮箱",
  "items": [
    {
      "product_name": "产品名称",
      "product_code": "产品编码",
      "quantity": 数量，
      "unit_price": 单价，
      "currency": "USD",
      "incoterm": "FOB|CIF",
      "lead_time_days": 交货天数
    }
  ],
  "total_amount": 总金额，
  "valid_until": "报价有效期",
  "shipping_port": "起运港",
  "payment_terms": "付款条款",
  "notes": "备注"
}
"""
```

### 3.4 CEO Agent 模块

**依赖图生成**:
```python
class CEOAgent:
    def decompose_goal(self, email: Email, classification: dict) -> DependencyGraph:
        """
        将询盘处理目标分解为子 Agent 任务依赖图
        """
        graph = DependencyGraph()

        # 所有询盘都需要价格查询
        price_task = graph.add_task(
            agent="price_agent",
            input={"products": classification["products_mentioned"]},
            budget=0.10
        )

        # 国际订单需要合规检查
        if classification["customer_region"] != "domestic":
            compliance_task = graph.add_task(
                agent="compliance_agent",
                input={"products": classification["products_mentioned"]},
                budget=0.15
            )
            graph.add_dependency(price_task, compliance_task)

        # 所有订单都需要物流计算
        logistics_task = graph.add_task(
            agent="logistics_agent",
            input={
                "destination": classification["customer_region"],
                "products": classification["products_mentioned"]
            },
            budget=0.12
        )
        graph.add_dependency(compliance_task, logistics_task)

        # 最后生成回复
        reply_task = graph.add_task(
            agent="reply_agent",
            input={"quote_data": logistics_task.output},
            budget=0.08
        )
        graph.add_dependency(logistics_task, reply_task)

        return graph
```

**沙箱执行**:
```python
class AgentSandbox:
    def __init__(self, budget: float, write_isolation: bool = True):
        self.budget = budget
        self.spent = 0.0
        self.write_isolation = write_isolation
        self.sandbox_db = SQLiteInMemory()  # 写隔离

    def execute(self, agent_fn, input_data: dict) -> AgentResult:
        # 预算硬 Kill
        estimated_cost = self.estimate_cost(agent_fn, input_data)
        if self.spent + estimated_cost > self.budget:
            raise BudgetExceeded(
                f"Agent exceeded budget: {self.spent + estimated_cost} > {self.budget}"
            )

        # 执行并追踪
        result = agent_fn(input_data, db=self.sandbox_db)
        self.spent += result.actual_cost

        return result
```

**评审决策**:
```python
class CEOReviewer:
    def review(self, task_result: AgentResult) -> Decision:
        """
        评审子 Agent 交付物

        Promote: 质量合格，批准执行
        Redelegate: 质量不足，重新分配
        Reject: 严重错误，拒绝并记录
        """
        quality_score = self.evaluate_quality(task_result)

        if quality_score >= 0.8:
            return Decision.PROMOTE
        elif quality_score >= 0.5:
            return Decision.REDELEGATE
        else:
            return Decision.REJECT
```

### 3.5 Prompt 进化模块

**Karpathy Autoresearch 模式**:
```python
class PromptEvolution:
    def __init__(self, ground_truth_dataset: str):
        self.ground_truth = load_dataset(ground_truth_dataset)
        self.version = 0
        self.history = []

    def mutate(self, prompt_template: str) -> List[str]:
        """生成 prompt 变体"""
        mutations = []

        # 变异策略 1: 添加约束
        mutations.append(prompt_template + "\n请确保输出严格符合 JSON Schema。")

        # 变异策略 2: 添加示例
        mutations.append(prompt_template + "\n示例输出：{...}")

        # 变异策略 3: 调整措辞
        mutations.append(prompt_template.replace("请分析", "请详细分析"))

        return mutations

    def evaluate(self, prompt_variants: List[str]) -> List[float]:
        """用 Ground Truth 评估每个变体"""
        scores = []
        for variant in prompt_variants:
            correct = 0
            for sample in self.ground_truth:
                result = self.run_with_prompt(variant, sample.input)
                if self.compare(result, sample.expected):
                    correct += 1
            scores.append(correct / len(self.ground_truth))
        return scores

    def evolve(self):
        """进化循环"""
        current_prompt = self.get_base_prompt()

        while True:
            variants = self.mutate(current_prompt)
            scores = self.evaluate(variants)

            best_idx = np.argmax(scores)
            if scores[best_idx] > self.current_score:
                current_prompt = variants[best_idx]
                self.version += 1
                self.save_version(current_prompt, scores[best_idx])
```

---

## 4. 可观测性设计

### 4.1 Metrics（核心指标）

| 指标 | 采集方式 | 展示频率 | 告警阈值 |
|------|---------|---------|---------|
| 邮件处理量 | 计数器 | 实时 | - |
| 平均处理延迟 | 直方图 | 实时 | >5s |
| 平均 Token 成本 | 直方图 | 实时 | >$0.05/封 |
| 分类准确率 | 抽样评估 | 每小时 | <95% |
| Sonnet 路由率 | 计数器 | 实时 | <80% |
| Prompt 版本数 | 计数器 | - | - |

### 4.2 Tracing（分布式追踪）

**Span 设计**:
```python
@trace("email_classification")
async def classify_email(email: Email) -> ClassificationResult:
    with tracer.span("llm_call") as span:
        span.set_attribute("model", "claude-sonnet-4")
        span.set_attribute("prompt_tokens", len(prompt))
        return await client.messages.create(...)

@trace("context_retrieval")
async def retrieve_context(...) -> ContextResult:
    with tracer.span("chroma_query") as span:
        span.set_attribute("collection", "emails")
        span.set_attribute("n_results", 3)
        ...

@trace("quote_generation")
async def generate_quote(...) -> QuoteResult:
    with tracer.span("llm_call") as span:
        span.set_attribute("model", "claude-opus-4")  # or sonnet
        ...
```

### 4.3 Agent 预算追踪

```python
class BudgetTracker:
    def __init__(self):
        self.budgets: Dict[str, float] = {}
        self.spent: Dict[str, float] = {}
        self.events: List[BudgetEvent] = []

    def record_spending(self, agent_id: str, cost: float):
        self.spent[agent_id] = self.spent.get(agent_id, 0) + cost

        # 预算硬 Kill 检查
        if self.spent[agent_id] > self.budgets[agent_id]:
            self.events.append(BudgetEvent(
                type="BUDGET_HARD_KILL",
                agent_id=agent_id,
                timestamp=datetime.now()
            ))
            raise BudgetExceeded()
```

### 4.4 Prompt 进化日志

```python
class PromptRegistry:
    def save_version(self, name: str, template: str, score: float, changes: str):
        version = {
            "name": name,
            "template": template,
            "score": score,
            "changes": changes,
            "timestamp": datetime.now().isoformat(),
            "ground_truth_size": len(self.ground_truth)
        }
        self.db.insert("prompt_versions", version)

    def get_diff(self, v1: int, v2: int) -> str:
        """生成版本间 diff"""
        t1 = self.get_template(v1)
        t2 = self.get_template(v2)
        return difflib.unified_diff(t1, t2)
```

---

## 5. 数据模型

### 5.1 SQLite Schema

```sql
-- 邮件表
CREATE TABLE emails (
    id TEXT PRIMARY KEY,
    raw_content TEXT,
    from_address TEXT,
    subject TEXT,
    received_at TIMESTAMP,
    processed_at TIMESTAMP,
    status TEXT -- 'pending', 'processing', 'completed', 'failed'
);

-- 分类结果表
CREATE TABLE classifications (
    email_id TEXT PRIMARY KEY,
    type TEXT,
    priority_score REAL,
    urgency TEXT,
    language TEXT,
    products_mentioned TEXT, -- JSON array
    customer_region TEXT,
    requires_human BOOLEAN,
    suggested_route TEXT,
    created_at TIMESTAMP
);

-- 报价单表
CREATE TABLE quotes (
    id TEXT PRIMARY KEY,
    email_id TEXT,
    quote_json TEXT, -- 完整 JSON
    total_amount REAL,
    currency TEXT,
    status TEXT, -- 'pending_review', 'approved', 'sent'
    created_at TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails(id)
);

-- Agent 执行日志表
CREATE TABLE agent_executions (
    id TEXT PRIMARY KEY,
    email_id TEXT,
    agent_name TEXT,
    status TEXT, -- 'running', 'completed', 'failed', 'budget_killed'
    budget_allocated REAL,
    actual_cost REAL,
    input_data TEXT, -- JSON
    output_data TEXT, -- JSON
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Prompt 版本表
CREATE TABLE prompt_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    version INTEGER,
    template TEXT,
    accuracy_score REAL,
    changes TEXT,
    created_at TIMESTAMP
);
```

### 5.2 ChromaDB Collection

```python
from chromadb import PersistentClient

client = PersistentClient(path="./chroma_data")

collection = client.create_collection(
    name="email_embeddings",
    metadata={"description": "Historical email embeddings for RAG"}
)

# 添加文档
collection.add(
    documents=[email_body],
    metadatas=[{
        "email_id": email_id,
        "type": classification["type"],
        "region": classification["region"],
        "products": classification["products"]
    }],
    ids=[email_id]
)
```

---

## 6. 技术栈选型与架构 Trade-off

### 6.1 架构决策总览

本节记录所有关键技术选型及其 Trade-off 分析。面试时应能清晰解释每个选择的原因和代价。

### 6.2 数据库选型

| 选项 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **SQLite** | 零配置、单文件、嵌入式 | 并发写入受限、无网络访问 | ✅ 选择 |
| PostgreSQL | 生产级、并发强、扩展好 | 需要独立服务、配置复杂 | 迁移目标 |
| MySQL | 广泛使用 | AI 生态集成不如 PG | - |

**决策**: SQLite for demo → PostgreSQL for prod

**迁移路径**: 使用 SQLAlchemy ORM，切换 DB 只需改 connection string

**面试回答示例**:
> "我选择 SQLite 是为了面试演示的便捷性，但通过 SQLAlchemy ORM 抽象，生产环境可以无缝迁移到 PostgreSQL。这体现了快速迭代和生产就绪的平衡。"

---

### 6.3 向量数据库选型

| 选项 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **ChromaDB** | 本地运行、JD 明确要求、Python 原生 | 大规模性能待验证 | ✅ 选择 |
| Qdrant | 性能更好、Rust 编写 | 需要独立服务 | - |
| Pinecone | 全托管、免运维 | 依赖外部服务、成本高 | - |
| Milvus | 开源、功能全 | 部署复杂 | - |

**决策**: ChromaDB（本地 persistent 模式）

**面试回答示例**:
> "ChromaDB 是 JD 明确要求的，同时也适合本地演示。生产环境如果规模扩大，可以考虑 Qdrant 获得更好的查询性能。"

---

### 6.4 Embedding 模型选型

| 选项 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **Ollama (mxb3embed-base)** | 本地运行、JD 明确要求、免费 | 质量略低于 API | ✅ 选择 |
| OpenAI Ada-002 | 质量好、API 简单 | 按次计费、依赖外部 | - |
| Cohere | 多语言支持好 | 成本较高 | - |

**决策**: Ollama 本地运行

**面试回答示例**:
> "Ollama 本地运行意味着零 API 成本，这对于频繁测试和演示非常重要。质量上 mxb3embed-base 对于邮件分类场景已经足够。"

---

### 6.5 Web 框架选型

| 选项 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **FastAPI** | 异步原生、自动文档、类型安全 | 生态较新 | ✅ 选择 |
| Flask | 生态成熟、简单 | 异步支持弱、类型安全差 | - |
| Django | 全功能、ORM 内置 | 重、异步支持晚 | - |

**决策**: FastAPI

**面试回答示例**:
> "FastAPI 是现代 Python Web 开发的行业标准，特别是对于 AI 应用，异步支持对于并发处理多个 LLM 调用至关重要。"

---

### 6.6 前端框架选型

| 选项 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **React + TypeScript** | 行业标准、类型安全、生态好 | 学习曲线 | ✅ 选择 |
| Vue | 学习曲线低、轻量 | 国内接受度略低 | - |
| Svelte | 更轻量、编译时优化 | 生态较小 | - |
| HTMX | 极简、后端友好 | 复杂交互受限 | - |

**决策**: React 18 + TypeScript + Tailwind CSS

**面试回答示例**:
> "React + TS 是行业标准，展示全栈能力。Tailwind CSS 允许快速迭代 UI，同时保持一致性。"

---

### 6.7 配置管理选型

| 选项 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **pydantic-settings** | 类型安全、自动验证、IDE 友好 | 需要额外依赖 | ✅ 选择 |
| os.environ | 零依赖 | 无验证、易出错 | - |
| YAML config | 可读性好 | 无类型安全 | - |

**决策**: pydantic-settings

**面试回答示例**:
> "配置管理的类型安全可以防止生产环境的配置错误。pydantic-settings 在启动时会验证所有必需的环境变量。"

---

### 6.8 依赖管理选型

| 选项 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **uv + requirements.txt** | 快速、可重现、兼容 | uv 较新 | ✅ 选择 |
| pip + requirements.txt | 标准、简单 | 慢、传递依赖不确定 | - |
| Poetry | 一体化、锁文件 | 慢、有时不稳定 | - |

**决策**: uv（开发）+ requirements.txt（兼容）

---

### 6.9 测试框架选型

| 选项 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **pytest + pytest-asyncio** | 生态好、异步支持、fixture 强大 | - | ✅ 选择 |
| unittest | 内置 | 语法冗长、fixture 弱 | - |

**决策**: pytest

---

### 6.10 可观测性选型

| 选项 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **OpenTelemetry + 自建 Dashboard** | 标准协议、可定制、展示工程能力 | 需要自己搭建 | ✅ 选择 |
| Datadog | 全功能、免运维 | 成本高、依赖外部 | - |
| Grafana Cloud | 强大可视化 | 配置复杂、依赖外部 | - |

**决策**: OpenTelemetry 协议 + 自建 React Dashboard

**面试回答示例**:
> "自建 Dashboard 可以完全定制面试演示的展示内容，同时展示对可观测性的深入理解。生产环境可以对接 Datadog 或 Grafana。"

---

### 6.11 生产级补充内容

基于"生产级完整实现"的要求，以下组件必须实现：

| 组件 | 说明 | 优先级 |
|------|------|--------|
| Migrations | Alembic 数据库版本控制 | P0 |
| Logging 配置 | 结构化日志、日志轮转 | P0 |
| 错误处理策略 | 统一错误处理、重试机制 | P0 |
| Secrets 管理 | .env + pydantic-settings | P0 |
| Rate Limiting | API 调用限流 | P0 |
| Health Check | 服务健康检查端点 | P0 |
| CI/CD | GitHub Actions 自动化 | P1 |
| Docker 化 | 容器化部署 | P1 |
| 备份策略 | 数据库备份脚本 | P2 |

---

## 7. 项目结构（生产级）

```
ai-email-agent/
├── .env.example              # 环境变量模板
├── .gitignore               # Git 忽略规则
├── .python-version          # Python 版本锁定
├── pyproject.toml           # 项目元数据 + 依赖
├── requirements.txt         # 锁定依赖
├── requirements-dev.txt     # 开发依赖
├── Dockerfile               # 生产镜像
├── docker-compose.yml       # 本地开发环境
├── Makefile                 # 常用命令
│
├── src/email_agent/
│   ├── __init__.py
│   ├── main.py              # 应用入口
│   ├── config.py            # 配置管理 (pydantic-settings)
│   ├── logging.conf         # 日志配置
│   │
│   ├── api/                 # API 层
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── deps.py          # 依赖注入
│   │   └── error_handlers.py # 统一错误处理
│   │
│   ├── core/                # 核心模块
│   │   ├── __init__.py
│   │   ├── security.py      # API Key 管理
│   │   ├── rate_limiter.py  # 限流
│   │   └── health.py        # Health Check
│   │
│   ├── layer1/              # 分类路由
│   │   ├── __init__.py
│   │   ├── classifier.py
│   │   └── prompts.py
│   │
│   ├── layer2/              # 上下文检索
│   │   ├── __init__.py
│   │   ├── retriever.py
│   │   └── chroma_client.py
│   │
│   ├── layer3/              # 分析生成
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   └── router.py
│   │
│   ├── agents/              # Agent 合同制
│   │   ├── __init__.py
│   │   ├── ceo_agent.py
│   │   ├── sandbox.py
│   │   └── reviewer.py
│   │
│   ├── evolution/           # Prompt 进化
│   │   ├── __init__.py
│   │   └── evolution.py
│   │
│   ├── observability/       # 可观测性
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   ├── tracing.py
│   │   └── budget_tracker.py
│   │
│   ├── storage/             # 数据存储
│   │   ├── __init__.py
│   │   ├── database.py      # SQLite 连接管理
│   │   ├── migrations/      # 数据库迁移
│   │   │   ├── 001_initial.sql
│   │   │   └── ...
│   │   └── models.py
│   │
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── email_parser.py
│
├── frontend/                # React 前端
│   ├── package.json
│   ├── .env.example
│   ├── Dockerfile
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── api/             # API 客户端
│       ├── components/      # UI 组件
│       ├── hooks/           # React Hooks
│       └── pages/           # 页面
│
├── tests/                   # 测试
│   ├── __init__.py
│   ├── conftest.py          # pytest fixture
│   ├── unit/                # 单元测试
│   ├── integration/         # 集成测试
│   └── e2e/                 # 端到端测试
│
├── scripts/                 # 辅助脚本
│   ├── seed_data.py         # 种子数据
│   ├── run_migrations.py    # 运行迁移
│   └── evaluate_prompt.py   # Prompt 评估
│
├── data/                    # 数据
│   ├── sample_emails.json   # 示例邮件
│   └── ground_truth.json    # Ground Truth
│
├── .github/                 # GitHub Actions
│   └── workflows/
│       ├── ci.yml           # CI 流水线
│       └── cd.yml           # CD 流水线
│
└── docs/
    ├── API.md               # API 文档
    ├── DEPLOYMENT.md        # 部署文档
    └── superpowers/
        └── specs/
            └── design.md    # 设计文档
```

**生产级项目结构说明**:

| 目录/文件 | 作用 | 生产级意义 |
|----------|------|-----------|
| `.env.example` | 环境变量模板 | 新成员快速上手 |
| `pyproject.toml` | 项目元数据 | Python 标准 |
| `migrations/` | 数据库版本控制 | 生产环境可重现 |
| `logging.conf` | 日志配置 | 生产问题调试 |
| `error_handlers.py` | 统一错误处理 | 用户体验一致 |
| `health.py` | Health Check | K8s/监控集成 |
| `rate_limiter.py` | API 限流 | 防止滥用 |
| `deps.py` | 依赖注入 | 测试友好 |
| `conftest.py` | pytest fixture | 测试可维护性 |
| `ci.yml` | CI 流水线 | 自动化测试 |

---

## 8. 面试演示脚本

### 8.1 演示流程（15 分钟）

**1. 系统概览（2 分钟）**
- 展示架构图
- 解释三层设计
- 说明与 JD 的对应关系

**2. 邮件处理演示（5 分钟）**
- 发送测试邮件
- 实时展示 Layer 1 分类结果
- 展示 Layer 2 检索到的上下文
- 展示 Layer 3 生成的报价单

**3. Agent 监控演示（3 分钟）**
- 展示 CEO Agent 依赖图分解
- 展示子 Agent 执行状态
- 展示预算消耗追踪

**4. 可观测性演示（3 分钟）**
- 展示核心指标仪表盘
- 展示分布式追踪时间线
- 展示 Prompt 进化历史

**5. 架构决策问答（2 分钟）**
- 为什么选择三层架构？
- 如何保证成本可控？
- 如何处理系统错误？

### 8.2 预期问题与回答

**Q1: 为什么分类和生成分开两层？**

A: 这是成本优化的关键。分类用便宜的 Sonnet 快速路由，只有复杂场景才用 Opus。JD 明确提到"80% 走 Sonnet 省成本"，这体现了工程思维而不是单纯调 API。

**Q2: 如何保证 Agent 不会无限消耗 Token？**

A: 预算硬 Kill 机制。每个子 Agent 执行前分配预算，沙箱内追踪实际消耗，超支立即终止。这是 JD 提到的"预算硬 kill"要求。

**Q3: Prompt 进化如何工作？**

A: 借鉴 Karpathy autoresearch 模式。用历史邮件作为 Ground Truth，自动变异 prompt、对比评估、保留优者。这是 JD 明确提到的进化模式。

---

## 9. 验收标准

### 9.1 功能验收

- [ ] 能接收并处理测试邮件
- [ ] Layer 1 分类准确率 >95%
- [ ] Layer 2 能检索到相关上下文
- [ ] Layer 3 生成正确的报价单 JSON
- [ ] CEO Agent 正确分解任务依赖图
- [ ] 子 Agent 预算硬 Kill 生效
- [ ] Prompt 进化能自动评估变体

### 9.2 可观测性验收

- [ ] 核心指标实时展示
- [ ] 分布式追踪可查看详情
- [ ] Agent 预算消耗可追踪
- [ ] Prompt 版本历史可对比

### 9.3 面试演示验收

- [ ] 系统可一键启动
- [ ] 演示数据预加载
- [ ] 界面美观、无明显 bug
- [ ] 能流畅回答架构问题

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| API 成本过高 | 测试费用超预算 | 本地 Mock、限制测试次数 |
| ChromaDB/Ollama 安装问题 | 环境配置复杂 | Docker 容器化、提供预构建镜像 |
| 前端界面 bug | 演示卡顿 | 提前测试、准备备用录屏 |
| Prompt 效果不稳定 | 分类准确率低 | Ground Truth 调优、人工审核开关 |

---

## 11. 后续迭代计划

**Phase 1** (核心功能): 三层架构 + 基础处理流程
**Phase 2** (Agent 合同制): CEO Agent + 子 Agent 沙箱
**Phase 3** (可观测性): Metrics + Tracing + Dashboard
**Phase 4** (Prompt 进化): 自动变异 + 评估 + 版本管理
**Phase 5** (UI 完善): 交互优化 + 边界情况处理

---

## 附录 A: 与 JD 要求的对应关系

| JD 要求 | 本系统设计 |
|--------|-----------|
| 63 个 Python 模块 | 模块化设计，每层独立包 |
| 19,600 行代码规模 | 完整实现约 15-20K 行 |
| 678MB 邮件数据库 | SQLite + ChromaDB 本地存储 |
| 34,000 向量块知识库 | ChromaDB Collection |
| 3 层架构 | Layer 1/2/3 明确分离 |
| 分类路由 (Sonnet) | Layer 1 分类器 |
| 上下文检索 (向量+wiki-link) | Layer 2 ChromaDB + Wiki-Link |
| 分析生成 (Opus/Sonnet 路由) | Layer 3 智能路由 |
| 80% 走 Sonnet 省成本 | 路由策略阈值控制 |
| CEO Agent 分解目标 | CEOAgent 依赖图生成 |
| 子 Agent 沙箱执行 | AgentSandbox 写隔离 |
| 预算硬 kill | BudgetTracker 硬限制 |
| CEO 评审交付物 | CEOReviewer Promote/Redelegate/Reject |
| 进化式 prompt 优化 | PromptEvolution Karpathy 模式 |
| 非结构化→结构化→业务动作 | 完整 Pipeline 实现 |

---

**设计文档结束**

*此设计文档是面试作品的核心交付物之一，展示候选人的系统设计能力和工程思维。*
