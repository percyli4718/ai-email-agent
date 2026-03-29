# AI Email Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个生产级的 AI 邮件处理 Agent 系统，完整实现三层 AI 架构、Agent 合同制、可观测性、和 React 管理后台。

**Architecture:**
- Layer 1: 邮件分类路由 (Claude Sonnet)
- Layer 2: 上下文检索 (ChromaDB + Ollama embedding)
- Layer 3: 分析生成 (Opus/Sonnet 智能路由)
- CEO Agent: 任务分解 + 子 Agent 沙箱执行 + 评审决策
- 可观测性：Metrics + Tracing + Budget Tracking

**Tech Stack:**
- Backend: Python 3.11+, FastAPI, Anthropic SDK, ChromaDB, Ollama, SQLite, pydantic-settings
- Frontend: React 18 + TypeScript + Tailwind CSS + Vite
- Testing: pytest + pytest-asyncio
- Observability: OpenTelemetry + 自建 Dashboard

---

## Tasks Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1. 项目初始化 | 1-3 | 项目骨架、配置、日志 |
| 2. Layer 1 | 4-5 | 分类路由 (Sonnet) |
| 3. Layer 2 | 6-8 | 上下文检索 (ChromaDB+Ollama) |
| 4. Layer 3 | 9-11 | 分析生成 (Opus/Sonnet 路由) |
| 5. Agent 合同制 | 12-14 | CEO Agent + 沙箱 + 评审 |
| 6. 可观测性 | 15-17 | Metrics + Tracing + Budget |
| 7. 数据存储 | 18 | SQLAlchemy + Models |
| 8. API 层 | 19-20 | FastAPI Routes + Main |
| 9. 前端 | 21-26 | React 组件 |
| 10. 测试 | 27-30 | 单元/集成/E2E 测试 |

**Total: 30 Tasks**

---

## Phase 1: 项目初始化

### Task 1: 创建项目骨架和配置
**Files:** `pyproject.toml`, `requirements.txt`, `.env.example`, `.gitignore`

[详细步骤见上文完整计划]

### Task 2: 创建配置管理模块
**Files:** `src/email_agent/config.py`

[详细步骤见上文完整计划]

### Task 3: 创建日志配置模块
**Files:** `src/email_agent/logging_config.py`

[详细步骤见上文完整计划]

---

## Phase 2: Layer 1 - 分类路由

### Task 4: 创建 Layer 1 Prompts
**Files:** `src/email_agent/layer1/prompts.py`

### Task 5: 创建 Layer 1 分类器
**Files:** `src/email_agent/layer1/classifier.py`, `tests/unit/test_classifier.py`

---

## Phase 3: Layer 2 - 上下文检索

### Task 6: 创建 ChromaDB 客户端
**Files:** `src/email_agent/layer2/chroma_client.py`

### Task 7: 创建 Embedding 服务
**Files:** `src/email_agent/layer2/embedding_service.py`

### Task 8: 创建 Layer 2 检索器
**Files:** `src/email_agent/layer2/retriever.py`, `tests/unit/test_retriever.py`

---

## Phase 4: Layer 3 - 分析生成

### Task 9: 创建 Layer 3 Prompts
**Files:** `src/email_agent/layer3/prompts.py`, `src/email_agent/layer3/schemas.py`

### Task 10: 创建智能路由
**Files:** `src/email_agent/layer3/router.py`

### Task 11: 创建 Layer 3 生成器
**Files:** `src/email_agent/layer3/generator.py`, `tests/unit/test_generator.py`

---

## Phase 5: Agent 合同制

### Task 12: 创建 CEO Agent
**Files:** `src/email_agent/agents/ceo_agent.py`

### Task 13: 创建 Agent 沙箱
**Files:** `src/email_agent/agents/sandbox.py`

### Task 14: 创建 CEO 评审器
**Files:** `src/email_agent/agents/reviewer.py`

---

## Phase 6: 可观测性

### Task 15: 创建指标收集
**Files:** `src/email_agent/observability/metrics.py`

### Task 16: 创建分布式追踪
**Files:** `src/email_agent/observability/tracing.py`

### Task 17: 创建预算追踪
**Files:** `src/email_agent/observability/budget_tracker.py`

---

## Phase 7: 数据存储

### Task 18: 创建数据库模块
**Files:** `src/email_agent/storage/database.py`, `src/email_agent/storage/models.py`

---

## Phase 8: API 层

### Task 19: 创建 API 路由
**Files:** `src/email_agent/api/schemas.py`, `src/email_agent/api/routes.py`

### Task 20: 创建 FastAPI 应用
**Files:** `src/email_agent/main.py`

---

## Phase 9: 前端

### Task 21: 前端项目骨架
**Files:** `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tailwind.config.js`

### Task 22-26: 前端组件
**Files:** `frontend/src/components/*.tsx`, `frontend/src/App.tsx`

---

## Phase 10: 测试

### Task 27-30: 测试
**Files:** `tests/unit/*.py`, `tests/integration/*.py`, `tests/e2e/*.py`

---

## Execution Handoff

**Plan complete and saved to** `docs/superpowers/plans/2026-03-29-ai-email-agent-implementation.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
