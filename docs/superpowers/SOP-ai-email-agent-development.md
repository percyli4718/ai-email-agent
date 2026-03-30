# AI Email Agent 项目开发 SOP

**版本**: 1.0
**日期**: 2026-03-30
**项目**: AI Email Agent (面试作品)
**目标职位**: AI 产品软件工程师（从 0 到 1）

---

## 流程总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI Email Agent 开发 SOP                              │
└─────────────────────────────────────────────────────────────────────────────┘

  Step 1: 需求梳理          →  Step 2: UI/UX 设计       →  Step 3: 架构设计
  ┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
  │ superpowers:     │        │ frontend-design: │        │ superpowers:     │
  │ brainstorming    │        │ frontend-design  │        │ brainstorming    │
  │ (需求澄清)        │        │ (界面设计)        │        │ (架构决策)        │
  └──────────────────┘        └──────────────────┘        └──────────────────┘
              │                          │                          │
              ▼                          ▼                          ▼
  ┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
  │ 实施计划.md       │        │ ui-mockups.html  │        │ 设计文档.md       │
  └──────────────────┘        └──────────────────┘        └──────────────────┘
              │                          │                          │
              └──────────────────────────┼──────────────────────────┘
                                         │
                                         ▼
  Step 4: 编写计划            →  Step 5: 执行计划       →  Step 6: 并行调试
  ┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
  │ superpowers:     │        │ superpowers:     │        │ superpowers:     │
  │ writing-plans    │        │ executing-plans  │        │ dispatching-     │
  │ (30 任务拆解)     │        │ (按层实现)        │        │ parallel-agents  │
  └──────────────────┘        └──────────────────┘        │ (并行修复)        │
              │                          │                └──────────────────┘
              │                          │                          │
              ▼                          ▼                          │
  ┌──────────────────┐        ┌──────────────────┐                  │
  │ 实施计划 (更新)    │        │ src/ 代码实现     │ ◀────────────────┘
  └──────────────────┘        └──────────────────┘
                                         │
                                         ▼
  Step 7: 验证完成            →  Step 8: 代码审查       →  Step 9: Git 推送
  ┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
  │ superpowers:     │        │ superpowers:     │        │ git push         │
  │ verification-    │        │ requesting-code- │        │ (用户确认后)     │
  │ before-completion│        │ review           │        └──────────────────┘
  │ (98% 一致性检查)  │        │ (质量检查)        │                  │
  └──────────────────┘        └──────────────────┘                  ▼
              │                          │               ┌──────────────────┐
              │                          │               │ GitHub 仓库       │
              │                          │               │ 已推送 ✓         │
              ▼                          ▼               └──────────────────┘
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                              完成                                        │
  │  • 单元测试：22/22 (100%)                                                │
  │  • 设计文档一致性：100%                                                  │
  │  • 前端 UI 一致性：98%+                                                  │
  └──────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: 需求梳理与多轮澄清

**输入**:
- `ai-product-jd.md` (原始 JD 文档)
- 用户背景：AI 全栈工程师 (Python)、AI 科技自媒体、出海工具开发

**使用 Skill**: `superpowers:brainstorming`

**过程**:
1. 阅读 JD，识别关键词：
   - "63 个 Python 模块"、"19,600 行代码"
   - "3 层架构：分类路由、上下文检索、分析生成"
   - "CEO Agent 分解目标、子 Agent 沙箱执行、预算硬 kill"
   - "进化式 prompt 优化 (Karpathy Autoresearch 模式)"
   - "80% 走 Sonnet 省成本"

2. 调用 `superpowers:brainstorming` 向用户提问：
   - Q1: 倾向哪种邮件处理场景？(药品分销/电商咨询/其他)
   - Q2: 是否需要完整实现 3 层 AI 架构？
   - Q3: 可观测性需要哪些维度？(Metrics/Tracing/Budget/Prompt 进化)
   - Q4: 前端 UI 是否需要设计？(Dashboard 展示)

3. 用户确认后，梳理出最终 PRD

**输出**:
- `docs/superpowers/plans/2026-03-29-ai-email-agent-implementation.md`

**验收标准**:
- 需求理解度 >95%
- 用户确认所有核心功能点

---

## Step 2: UI/UX 设计

**输入**:
- Step 1 输出的 PRD 文档

**使用 Skill**: `frontend-design:frontend-design`

**设计要求**:
- 深色主题 (专业感、科技感)
- 三大核心 Tab: Inbox / Metrics / Agents
- 邮件状态指示器 (未处理/处理中/已完成)
- 优先级徽章 (高/中/低)
- Metrics 卡片 (6 个核心指标)
- Agent 预算进度条 (橙色渐变)

**输出**:
- `ui-mockups.html` (完整界面 mockup)

**验收标准**:
- 包含所有 JD 要求的可视化元素
- 设计风格统一、专业

---

## Step 3: 架构设计与 Trade-off 分析

**输入**:
- PRD 文档
- UI Mockups

**使用 Skill**: `superpowers:brainstorming`

**架构决策点**:
| 决策点 | 选项 A | 选项 B | 决策 | 原因 |
|--------|--------|--------|------|------|
| 数据库 | SQLite | PostgreSQL | SQLite | 演示便捷，ORM 抽象可迁移 |
| 向量库 | ChromaDB | Qdrant | ChromaDB | JD 明确要求，本地运行 |
| Embedding | Ollama | OpenAI API | Ollama | 零成本，本地运行 |
| Web 框架 | FastAPI | Flask | FastAPI | 异步原生，类型安全 |
| 前端 | React+TS | Vue | React+TS | 行业标准 |
| 配置 | pydantic-settings | os.environ | pydantic | 类型安全 |

**输出**:
- `docs/superpowers/specs/2026-03-29-ai-email-agent-design.md`

**验收标准**:
- 所有技术选型有明确 Trade-off 分析
- 架构决策可解释、可辩护

---

## Step 4: 编写实施计划

**输入**:
- 设计文档
- UI Mockups

**使用 Skill**: `superpowers:writing-plans`

**计划结构**:
```
Phase 1: 项目骨架 (Task 1-3)
Phase 2: Layer 1 分类 (Task 4-5)
Phase 3: Layer 2 检索 (Task 6-8)
Phase 4: Layer 3 生成 (Task 9-11)
Phase 5: Agent 系统 (Task 12-14)
Phase 6: 可观测性 (Task 15-17)
Phase 7: 存储与 API (Task 18-20)
Phase 8: 前端实现 (Task 21-26)
Phase 9: 测试 (Task 27-30)
Phase 10: 收尾 (Git Push)
```

**每个任务包含**:
- 文件路径
- 测试代码示例
- 实现代码示例
- git commit 命令

**输出**:
- 更新 `docs/superpowers/plans/2026-03-29-ai-email-agent-implementation.md` (30 tasks)

**验收标准**:
- 任务拆解粒度适中 (每个任务 1-2 小时)
- 任务依赖关系清晰

---

## Step 5: 执行计划

**输入**:
- 实施计划 (30 tasks)

**使用 Skill**: `superpowers:executing-plans`

**执行顺序**:
1. Phase 1-4: 核心 3 层实现
2. Phase 5: Agent 合同制系统
3. Phase 6: 可观测性
4. Phase 7-8: API + 前端
5. Phase 9: 测试修复

**输出**:
- `src/email_agent/` 完整实现
- `frontend/src/` 完整实现

**验收标准**:
- 代码与设计文档一致
- 所有文件按结构创建

---

## Step 6: 并行调试与修复

**触发条件**: 测试失败 (多个独立错误)

**使用 Skill**: `superpowers:dispatching-parallel-agents`

**适用场景**:
- 3+ 测试文件失败
- 错误原因相互独立
- 可并行调查

**示例**:
```
并行任务分配:
├─ Agent 1: 修复 test_classifier.py (JSON 解析问题)
├─ Agent 2: 修复 test_generator.py (mock 返回值问题)
├─ Agent 3: 修复 test_retriever.py (Ollama proxy 问题)
└─ Agent 4: 修复 test_tracing.py (context manager yield 问题)
```

**输出**:
- 所有测试通过

**验收标准**:
- 测试通过率 100%
- 各 agent 修复无冲突

---

## Step 7: 验证完成

**触发条件**: 所有任务完成，测试通过

**使用 Skill**: `superpowers:verification-before-completion`

**验证清单**:
```markdown
- [ ] 单元测试通过率 >= 98%
- [ ] 设计文档模块一致性 >= 98%
- [ ] 前端 UI 与 mockups 一致性 >= 98%
- [ ] 所有核心功能可运行
- [ ] 代码无安全漏洞
- [ ] Git 提交记录清晰
```

**输出**:
- 验证报告

**验收标准**:
- 所有检查项通过
- 一致性 >98%

---

## Step 8: 代码审查

**触发条件**: 验证通过

**使用 Skill**: `superpowers:requesting-code-review`

**审查清单**:
```markdown
- [ ] 代码符合 Python 最佳实践
- [ ] 类型注解完整
- [ ] 错误处理适当
- [ ] 日志记录完整
- [ ] 无硬编码凭据
- [ ] 依赖版本锁定
```

**输出**:
- Code Review 报告
- 待修复问题列表 (如有)

**验收标准**:
- 无严重问题
- 所有问题已修复或记录

---

## Step 9: Git 推送

**触发条件**: 用户确认推送

**流程**:
```bash
# 1. 提交更改
git add -A
git commit -m "feat: complete AI Email Agent implementation"

# 2. 添加远程仓库
git remote add origin git@github.com:percyli4718/ai-email-agent.git

# 3. 推送 (用户确认后执行)
git push -u origin ai-email-agent-implementation
```

**输出**:
- GitHub 仓库已推送
- PR/Issue 模板 (可选)

**验收标准**:
- 代码已推送到远程仓库
- 分支命名规范

---

## Superpowers 技能使用统计

| 阶段 | 技能 | 调用次数 | 作用 |
|------|------|----------|------|
| 1 | `superpowers:brainstorming` | 1 | 需求澄清与多轮提问 |
| 2 | `frontend-design:frontend-design` | 1 | UI/UX 设计 |
| 3 | `superpowers:brainstorming` | 1 | 架构 Trade-off 分析 |
| 4 | `superpowers:writing-plans` | 1 | 编写 30 任务实施计划 |
| 5 | `superpowers:executing-plans` | 1 | 执行计划 |
| 6 | `superpowers:dispatching-parallel-agents` | 1 | 并行修复测试 |
| 7 | `superpowers:verification-before-completion` | 1 | 完成验证 |
| 8 | `superpowers:requesting-code-review` | 1 | 代码审查 |
| **总计** | | **8 次** | |

---

## openSpec 对比点

本 SOP 可用于与 openSpec 最佳实践对比以下维度：

1. **需求澄清效率**: brainstorming vs openSpec 需求模板
2. **设计驱动开发**: frontend-design + superpowers vs openSpec 设计流程
3. **计划可执行性**: writing-plans vs openSpec 任务拆解
4. **并行调试**: dispatching-parallel-agents vs openSpec 并发策略
5. **验证严谨性**: verification-before-completion vs openSpec 验收标准
6. **整体开发周期**: 9 Step SOP vs openSpec 标准流程

---

## 项目成果

- **GitHub**: https://github.com/percyli4718/ai-email-agent
- **测试**: 22/22 通过 (100%)
- **一致性**: 100% (设计文档), 98%+ (UI)
- **代码规模**: ~30 个 Python 模块

---

**文档结束**
