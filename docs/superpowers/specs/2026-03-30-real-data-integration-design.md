# AI Email Agent 真实数据集成设计文档

**日期:** 2026-03-30
**状态:** 已批准
**作者:** AI Assistant

---

## 1. 概述

### 1.1 目标
实现 AI Email Agent 的完整真实数据流，从 Mock 数据逐步迁移到真实数据处理。

### 1.2 范围
- Layer 1: 电子邮件分类器（集成 Anthropic API）
- Layer 2: 上下文检索器（已集成 ChromaDB + Ollama）
- Layer 3: 报价生成器（集成 Anthropic API）
- CEO Agent: 任务编排和调度
- 数据持久化：SQLAlchemy + SQLite
- API 路由：从 Mock 数据切换到数据库

### 1.3 约束条件
- API Key 预算：$5 美元，仅在最终验证阶段使用
- Ollama 服务：本地运行，nomic-embed-text 模型
- ChromaDB: 持久化存储在 ./data/chroma

---

## 2. 架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   API Routes (routes.py)                ││
│  │  - GET /api/emails           - GET /api/metrics         ││
│  │  - GET /api/emails/{id}      - GET /api/agents/status   ││
│  │  - POST /api/process-email   - GET /api/traces          ││
│  └─────────────────────────────────────────────────────────┘│
│                              ↓                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                  CEO Agent (ceo_agent.py)               ││
│  │  - Task Dependency Graph                                ││
│  │  - Sub-Agent Coordination                               ││
│  │  - Budget Management                                    ││
│  └─────────────────────────────────────────────────────────┘│
│                              ↓                                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Layer 1    │    │   Layer 2    │    │   Layer 3    │  │
│  │  Classifier  │ →  │   Retriever  │ →  │  Generator   │  │
│  │              │    │              │    │              │  │
│  │  - Anthropic │    │  - ChromaDB  │    │  - Anthropic │  │
│  │  - Prompts   │    │  - Ollama    │    │  - Router    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         ↓                    ↓                    ↓          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Anthropic   │    │  SQLite DB   │    │  Anthropic   │  │
│  │    API       │    │  (Emails)    │    │    API       │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
1. 新邮件到达
         ↓
2. Layer 1 分类器 (调用 Anthropic API)
   - 分类结果：{type, priority, region, products, ...}
         ↓
3. CEO Agent 创建任务依赖图
   - Price Agent → Compliance Agent → Logistics Agent → Reply Agent
         ↓
4. Layer 2 检索器 (ChromaDB + Ollama)
   - 相似邮件搜索
   - 客户历史查询
   - 定价政策检索
         ↓
5. Layer 3 生成器 (调用 Anthropic API)
   - 智能模型路由 (Sonnet vs Opus)
   - 生成结构化报价
         ↓
6. 结果持久化到数据库
   - Email 表
   - EmailAnalysis 表
   - AgentExecution 表
```

---

## 3. 组件设计

### 3.1 数据库层

**文件:** `src/email_agent/storage/models.py` (已完成)

**表结构:**
- `customers`: 客户信息
- `emails`: 邮件记录
- `email_analysis`: AI 分析结果
- `agent_executions`: Agent 执行跟踪

**集成点:**
- API routes 从数据库读取真实数据
- Layer 1/2/3 的输出写入数据库

### 3.2 Layer 1: 电子邮件分类器

**文件:** `src/email_agent/layer1/classifier.py` (已有 80%)

**需要修改:**
1. 增加从数据库读取邮件的方法
2. 分类结果写入 `email_analysis` 表
3. 添加重试逻辑和错误处理

**API 调用:**
- 模型：Claude Sonnet 3.5 (默认) / Opus 4.0 (复杂邮件)
- 成本：~$0.003/请求 (Sonnet)

### 3.3 Layer 2: 上下文检索器

**文件:** `src/email_agent/layer2/chroma_client.py` (已完成)
**文件:** `src/email_agent/layer2/retriever.py` (已有 70%)

**已完成:**
- ChromaDB 集成（使用 curl 生成 embedding）
- Ollama nomic-embed-text 模型
- 10 封模拟邮件注入

**需要修改:**
1. `retriever.py` 集成到主流程
2. 增加客户历史查询实现
3. 增加定价政策检索实现

### 3.4 Layer 3: 报价生成器

**文件:** `src/email_agent/layer3/generator.py` (已有 70%)

**需要修改:**
1. 增加从数据库读取上下文的方法
2. 生成结果写入 `email_analysis` 表
3. 模型路由器集成真实 API

**API 调用:**
- 模型路由：简单→Sonnet, 复杂→Opus
- 成本：~$0.01-0.05/请求

### 3.5 CEO Agent

**文件:** `src/email_agent/agents/ceo_agent.py` (已有 60%)

**需要修改:**
1. 完整实现任务依赖图执行
2. 子 Agent 调用真实 L1/L2/L3
3. 预算追踪集成

---

## 4. API 路由设计

### 4.1 现有路由 (Mock 数据)

```python
GET /api/emails           # 返回 MOCK_EMAILS
GET /api/emails/{id}      # 返回 Mock 分析
GET /api/agents/status    # 返回 Mock 状态
GET /api/metrics          # 真实数据 (MetricsCollector)
GET /api/traces           # 真实数据 (Tracer)
```

### 4.2 新路由 (真实数据)

```python
POST /api/process-email   # 处理新邮件（新增）
  Request: {email_body, from_address, subject}
  Response: {email_id, status, classification}
```

### 4.3 修改现有路由

```python
GET /api/emails           # 从数据库读取
GET /api/emails/{id}      # 从数据库 + email_analysis 读取
GET /api/agents/status    # 从 agent_executions 读取
```

---

## 5. 执行计划

### 5.1 阶段 1: 数据库集成 (无 API Key)
1. 实现数据库 CRUD 操作
2. 修改 API routes 读取真实数据
3. 注入更多模拟数据用于测试

### 5.2 阶段 2: Layer 2 完整集成 (无 API Key)
1. 完善 Retriever 的客户历史查询
2. 完善 Retriever 的定价政策检索
3. 测试 ChromaDB 搜索流程

### 5.3 阶段 3: Layer 1 集成 (使用 API Key)
1. 测试 Classifier 调用 Anthropic API
2. 分类结果写入数据库
3. 验证 L1 输出格式

### 5.4 阶段 4: Layer 3 集成 (使用 API Key)
1. 测试 Generator 调用 Anthropic API
2. 模型路由器验证
3. 生成结果写入数据库

### 5.5 阶段 5: CEO Agent 完整实现
1. 任务依赖图执行
2. 子 Agent 协调
3. 预算追踪验证

### 5.6 阶段 6: 端到端测试
1. 完整数据流测试
2. 性能测试
3. 错误处理测试

---

## 6. 测试策略

### 6.1 单元测试
- 每个 Layer 独立测试
- Mock API 调用

### 6.2 集成测试
- L1→L2→L3 数据流
- 数据库读写

### 6.3 E2E 测试
- 完整邮件处理流程
- API 端点测试

---

## 7. 成本控制

### 7.1 API Key 预算
- 总预算：$5
- 预计单次测试成本：$0.01-0.05
- 可用测试次数：100-500 次

### 7.2 优化策略
1. 开发阶段使用 Mock 数据
2. 只在最终验证使用真实 API
3. Layer 3 使用智能路由（优先 Sonnet）

---

## 8. 验收标准

- [ ] API routes 全部从数据库读取真实数据
- [ ] Layer 1 分类器成功调用 Anthropic API
- [ ] Layer 2 检索器成功搜索 ChromaDB
- [ ] Layer 3 生成器成功生成报价
- [ ] CEO Agent 完整执行任务流
- [ ] 所有数据持久化到数据库
- [ ] 端到端测试通过

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| API Key 超预算 | 高 | 严格控制在最终阶段使用 |
| Ollama 服务不稳定 | 中 | 已有 curl 备用方案 |
| ChromaDB 数据损坏 | 中 | 定期备份数据目录 |
| Anthropic API 限流 | 中 | 添加重试逻辑和延迟 |

---

**设计文档结束**
