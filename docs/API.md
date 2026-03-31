# AI Email Agent API 文档

## 概述

AI Email Agent 提供 RESTful API 用于处理药品分销相关的电子邮件。系统采用三层 AI 架构，自动完成邮件分类、上下文检索和报价生成。

**Base URL:** `http://localhost:8000`

**API 版本:** v1

## 认证

当前版本无需认证。生产环境建议使用 API Key 或 JWT。

## 数据模型

### Email

```typescript
{
  id: string              // 邮件唯一标识
  from_address: string    // 发件人邮箱
  subject: string         // 邮件主题
  body: string            // 邮件正文
  priority: "low" | "medium" | "high"
  status: "pending" | "processing" | "completed" | "failed"
  region: string          // 客户区域
  customer_id: number     // 关联客户 ID
  created_at: datetime    // 创建时间
  updated_at: datetime    // 更新时间
}
```

### EmailAnalysis

```typescript
{
  email_id: string
  layer1_classification: {
    type: "inquiry" | "complaint" | "status_check" | "rfq"
    priority_score: number      // 0-1
    urgency: "low" | "medium" | "high"
    language: string
    products_mentioned: string[]
    customer_region: string
    suggested_route: string
  }
  layer2_retrieval: {
    similar_emails: object
    pricing_policy: object
    compliance: object
  }
  layer3_output: {
    quote_id: string
    total_amount: number
    items: array
    valid_until: string
  }
  processing_time_ms: number
  cost: number              // API 调用成本 (美元)
  model_used: string        // "sonnet-4" 或 "opus-4"
}
```

### Customer

```typescript
{
  id: number
  name: string
  email: string
  tier: "A" | "B" | "C"     // 客户等级
  region: string            // 区域
  total_orders: number
  total_revenue: number
}
```

---

## API 端点

### 邮件管理

#### `GET /api/emails`

获取邮件列表

**参数:**
- `status` (可选): 按状态过滤
- `priority` (可选): 按优先级过滤
- `limit` (可选): 返回数量限制 (默认 50)

**响应:**
```json
{
  "emails": [
    {
      "id": "email_001",
      "from_address": "john@pharmacom.co.uk",
      "subject": "RFQ: Paracetamol 500mg",
      "priority": "high",
      "status": "completed",
      "created_at": "2026-03-30T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

#### `GET /api/emails/{email_id}`

获取邮件详情

**路径参数:**
- `email_id`: 邮件 ID

**响应:**
```json
{
  "id": "email_001",
  "from_address": "john@pharmacom.co.uk",
  "subject": "RFQ: Paracetamol 500mg",
  "body": "Dear Supplier,\n\nWe are interested in...",
  "priority": "high",
  "status": "completed",
  "region": "Europe",
  "customer": {
    "name": "PharmaCom UK",
    "tier": "A"
  },
  "created_at": "2026-03-30T10:00:00Z"
}
```

---

#### `POST /api/emails`

创建新邮件

**请求体:**
```json
{
  "from_email": "john@pharmacom.co.uk",
  "subject": "RFQ: Paracetamol 500mg",
  "body": "Dear Supplier,\n\nWe are interested in...",
  "priority": "high",
  "region": "Europe"
}
```

**响应:** 创建的 Email 对象

---

#### `POST /api/emails/{email_id}/process`

处理邮件（触发 L1→L2→L3 流程）

**路径参数:**
- `email_id`: 邮件 ID

**请求体 (可选):**
```json
{
  "use_ceo_agent": false    // 是否使用 CEO Agent 分解任务
}
```

**响应:**
```json
{
  "status": "processing",
  "email_id": "email_001",
  "estimated_time_ms": 5000
}
```

**异步处理:**
- 处理完成后更新 `email.status` 为 `completed`
- 分析结果写入 `EmailAnalysis` 表
- 可通过 `/api/emails/{email_id}/analysis` 查询结果

---

#### `GET /api/emails/{email_id}/analysis`

获取邮件分析结果

**路径参数:**
- `email_id`: 邮件 ID

**响应:**
```json
{
  "email_id": "email_001",
  "layer1_classification": {
    "type": "inquiry",
    "priority_score": 0.8,
    "urgency": "high",
    "language": "en",
    "products_mentioned": ["Paracetamol 500mg"],
    "customer_region": "Europe",
    "suggested_route": "quote_flow"
  },
  "layer2_retrieval": {
    "similar_emails": {
      "documents": [["Previous quote..."]],
      "distances": [0.26]
    },
    "pricing_policy": {
      "policies": [
        {
          "product": "Paracetamol 500mg",
          "base_price": 2.80,
          "discount_rate": 0.05,
          "currency": "USD"
        }
      ]
    },
    "compliance": {
      "requirements": [
        {
          "type": "certification",
          "name": "CE Marking",
          "mandatory": true
        }
      ]
    }
  },
  "layer3_output": {
    "quote_id": "quote_001",
    "customer_email": "john@pharmacom.co.uk",
    "items": [
      {
        "product": "Paracetamol 500mg",
        "quantity": 1000,
        "unit_price": 2.80,
        "total": 2800.00
      }
    ],
    "total_amount": 2800.00,
    "valid_until": "2026-04-30",
    "shipping_port": "Shanghai",
    "payment_terms": "30% advance, 70% against B/L"
  },
  "processing_time_ms": 4523.45,
  "cost": 0.0234,
  "model_used": "sonnet-4"
}
```

---

#### `DELETE /api/emails/{email_id}`

删除邮件

**路径参数:**
- `email_id`: 邮件 ID

**响应:** `204 No Content`

---

### 客户管理

#### `GET /api/customers`

获取客户列表

**响应:**
```json
{
  "customers": [
    {
      "id": 1,
      "name": "PharmaCom UK",
      "email": "john@pharmacom.co.uk",
      "tier": "A",
      "region": "Europe"
    }
  ]
}
```

---

#### `GET /api/customers/{customer_id}`

获取客户详情

**路径参数:**
- `customer_id`: 客户 ID

**响应:**
```json
{
  "id": 1,
  "name": "PharmaCom UK",
  "email": "john@pharmacom.co.uk",
  "tier": "A",
  "region": "Europe",
  "total_orders": 15,
  "total_revenue": 125000,
  "order_history": [...]
}
```

---

### 可观测性

#### `GET /api/metrics`

获取系统指标

**响应:**
```json
{
  "api": {
    "requests_total": 1523,
    "requests_per_minute": 12.5,
    "error_rate": 0.02,
    "latency_p50_ms": 45.2,
    "latency_p99_ms": 234.5
  },
  "ai": {
    "layer1_calls_total": 523,
    "layer2_calls_total": 520,
    "layer3_calls_total": 518,
    "avg_layer1_latency_ms": 1234.5,
    "avg_layer3_latency_ms": 3456.7
  },
  "budget": {
    "daily_spent": 2.34,
    "daily_limit": 5.00,
    "remaining": 2.66
  }
}
```

---

#### `GET /api/traces`

获取分布式追踪记录

**参数:**
- `email_id` (可选): 按邮件 ID 过滤
- `limit` (可选): 返回数量限制

**响应:**
```json
{
  "traces": [
    {
      "trace_id": "trace_001",
      "email_id": "email_001",
      "spans": [
        {
          "span_id": "span_001",
          "operation": "layer1.classify",
          "start_time": "2026-03-30T10:00:00.000Z",
          "duration_ms": 1234.5,
          "status": "success",
          "metadata": {
            "model": "sonnet-4",
            "cost": 0.003
          }
        },
        {
          "span_id": "span_002",
          "operation": "layer2.retrieve",
          "start_time": "2026-03-30T10:00:01.235Z",
          "duration_ms": 567.8,
          "status": "success",
          "metadata": {
            "similar_emails": 3,
            "policies_found": 2
          }
        }
      ]
    }
  ]
}
```

---

#### `GET /api/budget/events`

获取预算事件历史

**参数:**
- `limit` (可选): 返回数量限制 (默认 100)

**响应:**
```json
{
  "events": [
    {
      "operation": "quote_generation",
      "cost": 0.0234,
      "cumulative_cost": 1.234,
      "timestamp": "2026-03-30T10:00:00Z",
      "event_type": "spending"
    }
  ]
}
```

---

### 健康检查

#### `GET /api/health`

健康检查

**响应:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "database": "connected",
  "chromadb": "connected",
  "ollama": "connected"
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "error": {
    "code": "CLASSIFICATION_FAILED",
    "message": "邮件分类失败",
    "details": {
      "retry_after_ms": 1000
    }
  }
}
```

### 错误代码

| 代码 | HTTP 状态码 | 描述 |
|------|----------|------|
| `EMAIL_NOT_FOUND` | 404 | 邮件不存在 |
| `CLASSIFICATION_FAILED` | 500 | L1 分类失败 |
| `RETRIEVAL_FAILED` | 500 | L2 检索失败 |
| `GENERATION_FAILED` | 500 | L3 生成失败 |
| `BUDGET_EXCEEDED` | 402 | 超出预算 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |

---

## 使用示例

### cURL 示例

```bash
# 创建邮件
curl -X POST http://localhost:8000/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "from_email": "john@pharmacom.co.uk",
    "subject": "RFQ: Paracetamol 500mg",
    "body": "Dear Supplier,\n\nWe are interested in Paracetamol 500mg 1000 boxes."
  }'

# 处理邮件
curl -X POST http://localhost:8000/api/emails/email_001/process

# 查询结果
curl http://localhost:8000/api/emails/email_001/analysis
```

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 创建邮件
response = requests.post(f"{BASE_URL}/api/emails", json={
    "from_email": "john@pharmacom.co.uk",
    "subject": "RFQ: Paracetamol 500mg",
    "body": "Dear Supplier,\n\nWe are interested in..."
})
email_id = response.json()["id"]

# 处理邮件
requests.post(f"{BASE_URL}/api/emails/{email_id}/process")

# 轮询结果
import time
while True:
    response = requests.get(f"{BASE_URL}/api/emails/{email_id}/analysis")
    if response.status_code == 200:
        analysis = response.json()
        print(f"报价总额：${analysis['layer3_output']['total_amount']}")
        break
    time.sleep(1)
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:8000';

// 创建邮件
const email = await fetch(`${BASE_URL}/api/emails`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    from_email: 'john@pharmacom.co.uk',
    subject: 'RFQ: Paracetamol 500mg',
    body: 'Dear Supplier,\n\nWe are interested in...'
  })
});
const { id: emailId } = await email.json();

// 处理邮件
await fetch(`${BASE_URL}/api/emails/${emailId}/process`, {
  method: 'POST'
});

// 查询结果
const analysis = await fetch(`${BASE_URL}/api/emails/${emailId}/analysis`);
const result = await analysis.json();
console.log(`Total: $${result.layer3_output.total_amount}`);
```

---

## 性能指标

### 延迟目标

| 操作 | P50 | P95 | P99 |
|------|-----|-----|-----|
| L1 分类 | 1.2s | 2.5s | 4.0s |
| L2 检索 | 0.5s | 1.0s | 2.0s |
| L3 生成 | 3.5s | 7.0s | 10.0s |
| 完整流程 | 5.2s | 10.5s | 16.0s |

### 成本目标

| 操作 | 目标成本 |
|------|---------|
| L1 分类 | ~$0.003/次 |
| L2 检索 | ~$0.001/次 (本地 Ollama) |
| L3 生成 (Sonnet) | ~$0.01-0.05/次 |
| L3 生成 (Opus) | ~$0.05-0.10/次 |
| 完整流程 (80% Sonnet) | ~$0.02-0.05/次 |

---

## 更新日志

### v1.0.0 (2026-03-31)

- 初始版本发布
- 完整的 L1→L2→L3 处理流程
- CEO Agent 任务分解
- 预算追踪和成本控制
- 可观测性指标和分布式追踪
