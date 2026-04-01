# AI Email Agent 邮件生成器设计文档

**创建日期:** 2026-04-01  
**状态:** 待审批  
**作者:** AI Assistant

---

## 1. 概述

### 1.1 目标

实现前端"创建新邮件"功能，允许用户通过 Inbox 页面顶部按钮创建新的测试邮件，支持批量生成，模板数据存储在数据库中，可动态配置。

### 1.2 使用场景

1. **演示场景**: 面试或 Demo 展示时，实时创建新邮件并展示完整处理流程
2. **测试场景**: 开发测试时快速生成大量测试数据
3. **压力测试**: 批量生成邮件测试系统性能

### 1.3 数据流

```
用户点击"创建新邮件"
       ↓
选择生成数量 (1/5/10/自定义)
       ↓
POST /api/emails/generate (后端模板引擎)
       ↓
从数据库读取模板配置
       ↓
随机组合生成邮件
       ↓
创建 Customer + Email 记录
       ↓
(可选) 自动触发处理流程
       ↓
返回生成的邮件列表
```

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│ 前端 (React + TypeScript)                                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Inbox 页面顶部                                               │ │
│ │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │ │
│ │ │ ➕ 创建新邮件 │ │ 数量：[1 ▼]  │ │ ⚙️ 自动处理   │        │ │
│ │ └───────┬──────┘ └───────┬──────┘ └───────┬──────┘        │ │
│ │         │                │                │                │ │
│ │         └────────────────┴────────────────┘                │ │
│ │                           │                                 │ │
│ │                   onClick: handleCreateEmail()              │ │
│ └───────────────────────────┼─────────────────────────────────┘ │
│                             │                                   │
│                    POST /api/emails/generate                    │
│                    { count: 5, auto_process: true }             │
└─────────────────────────────┼───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│ 后端 (FastAPI)                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ POST /api/emails/generate                                   │ │
│ │                                                              │ │
│ │ 1. EmailTemplateService.get_templates()                      │ │
│ │    - 从数据库读取模板配置                                    │ │
│ │                                                              │ │
│ │ 2. EmailGenerator.generate(count)                            │ │
│ │    - 随机组合产品、客户、地区、数量                          │ │
│ │    - 生成邮件主题和正文                                      │ │
│ │                                                              │ │
│ │ 3. Database.create_customer() + create_email()               │ │
│ │    - 创建客户记录 (如不存在)                                 │ │
│ │    - 创建邮件记录                                            │ │
│ │                                                              │ │
│ │ 4. if auto_process:                                          │ │
│ │    - POST /api/emails/{id}/process                           │ │
│ │                                                              │ │
│ │ 5. return GeneratedEmailsResponse                            │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│ 数据库 (SQLite)                                                   │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│ │ email_templates │  │ customers       │  │ emails          │  │
│ │ - id            │  │ - id            │  │ - id            │  │
│ │ - type          │  │ - name          │  │ - from_address  │  │
│ │ - product       │  │ - email         │  │ - subject       │  │
│ │ - region        │  │ - region        │  │ - body          │  │
│ │ - quantity      │  │ - tier          │  │ - status        │  │
│ │ - subject_tpl   │  └─────────────────┘  └─────────────────┘  │
│ │ - body_tpl      │                                            │
│ └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型

### 3.1 新增 EmailTemplate 模型

```python
class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # inquiry, rfq, complaint, status_check
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    quantity_range: Mapped[str] = mapped_column(String(50), nullable=False)  # "100-500", "500-1000", "1000-5000"
    subject_template: Mapped[str] = mapped_column(Text, nullable=False)  # "RFQ: {product} - {quantity} boxes"
    body_template: Mapped[str] = mapped_column(Text, nullable=False)  # 包含占位符的邮件正文模板
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### 3.2 模板数据结构

```python
# 模板数据示例
TEMPLATES = [
    {
        "type": "rfq",
        "product_name": "Paracetamol 500mg",
        "region": "Europe",
        "quantity_range": "500-1000",
        "subject_template": "Request for Quote - {product}",
        "body_template": """Dear Supplier,

We are interested in purchasing the following products:

- {product}: {quantity} boxes
  - Packing: {packing}
  - Standard: {standard}

Please provide your best quote for delivery to {destination}.

We are a leading pharmaceutical distributor in {region} and this is a potential
long-term partnership.

Best regards,
{customer_name}
{position}
{company_name}
{email}
        """
    },
    # ... 更多模板
]
```

---

## 4. API 端点设计

### 4.1 POST /api/emails/generate

**请求:**
```json
{
  "count": 5,
  "auto_process": true,
  "filters": {
    "type": "rfq",
    "region": "Europe"
  }
}
```

**响应:**
```json
{
  "generated_emails": [
    {
      "id": "email_20260401_001",
      "from_address": "john.smith@pharmacom.co.uk",
      "subject": "Request for Quote - Paracetamol 500mg",
      "preview": "Dear Supplier, We are interested in purchasing...",
      "priority": "high",
      "status": "pending",
      "region": "Europe",
      "customer": {
        "name": "PharmaCom UK",
        "email": "john.smith@pharmacom.co.uk"
      }
    }
  ],
  "total": 5,
  "auto_process_started": true
}
```

### 4.2 GET /api/emails/templates

**请求:** 无

**响应:**
```json
{
  "templates": [
    {
      "id": 1,
      "type": "rfq",
      "product_name": "Paracetamol 500mg",
      "region": "Europe",
      "is_active": true
    }
  ],
  "total": 12
}
```

### 4.3 PUT /api/emails/templates/{id}

**用途:** 更新模板配置（管理后台使用）

---

## 5. 前端组件设计

### 5.1 GenerateEmailPanel 组件

```tsx
interface GenerateEmailPanelProps {
  onEmailsGenerated: (emails: EmailInbox[]) => void;
}

const GenerateEmailPanel: React.FC<GenerateEmailPanelProps> = ({ onEmailsGenerated }) => {
  const [count, setCount] = useState<number>(1);
  const [autoProcess, setAutoProcess] = useState<boolean>(true);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const response = await generateEmails({ count, auto_process: autoProcess });
      onEmailsGenerated(response.generated_emails);
    } catch (error) {
      // 错误处理
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex items-center gap-4 bg-[#1e293b] p-3 rounded-lg">
      <button
        onClick={handleGenerate}
        disabled={isGenerating}
        className="px-4 py-2 bg-[#3b82f6] text-white rounded hover:bg-[#2563eb]"
      >
        {isGenerating ? '生成中...' : '➕ 创建新邮件'}
      </button>
      
      <select
        value={count}
        onChange={(e) => setCount(Number(e.target.value))}
        className="px-3 py-2 bg-[#0f172a] rounded border border-[#334155]"
      >
        <option value={1}>1 封</option>
        <option value={5}>5 封</option>
        <option value={10}>10 封</option>
        <option value={20}>20 封</option>
        <option value={50}>50 封</option>
      </select>
      
      <label className="flex items-center gap-2 text-sm text-[#94a3b8]">
        <input
          type="checkbox"
          checked={autoProcess}
          onChange={(e) => setAutoProcess(e.target.checked)}
          className="rounded"
        />
        自动处理
      </label>
    </div>
  );
};
```

### 5.2 集成到 Inbox 页面

```tsx
// 在 InboxTab 组件顶部添加
<div className="mb-4 flex justify-between items-center">
  <h2 className="text-xl font-bold">📨 收件箱 | Inbox</h2>
  <GenerateEmailPanel onEmailsGenerated={handleNewEmails} />
</div>
```

---

## 6. 后端服务设计

### 6.1 EmailTemplateService

```python
class EmailTemplateService:
    """邮件模板服务"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def get_active_templates(self) -> List[EmailTemplate]:
        """获取所有活跃的模板"""
        async with self.db.session() as session:
            result = await session.execute(
                select(EmailTemplate).where(EmailTemplate.is_active == True)
            )
            return list(result.scalars().all())
    
    async def get_random_template(
        self, 
        template_type: str = None, 
        region: str = None
    ) -> EmailTemplate:
        """随机获取一个模板，支持类型和地区过滤"""
        templates = await self.get_active_templates()
        
        if template_type:
            templates = [t for t in templates if t.type == template_type]
        if region:
            templates = [t for t in templates if t.region == region]
        
        return random.choice(templates) if templates else None
```

### 6.2 EmailGenerator

```python
class EmailGenerator:
    """邮件生成器"""
    
    def __init__(self, template_service: EmailTemplateService, db: Database):
        self.template_service = template_service
        self.db = db
    
    def _generate_customer_name(self, region: str) -> dict:
        """生成指定地区的随机客户信息"""
        customer_names = {
            "Europe": [
                ("John Smith", "PharmaCom UK", "john.smith@pharmacom.co.uk"),
                ("Maria Garcia", "Salud ES", "maria.garcia@salud.es"),
            ],
            "South America": [
                ("Ana Silva", "Pharma Brazil", "ana.silva@pharma.br"),
                ("Carlos Rodriguez", "Medicina AR", "carlos@medicina.ar"),
            ],
            # ... 更多地区
        }
        names = customer_names.get(region, customer_names["Europe"])
        name, company, email = random.choice(names)
        return {"name": name, "company": company, "email": email}
    
    def _generate_quantity(self, quantity_range: str) -> int:
        """根据范围生成随机数量"""
        min_q, max_q = map(int, quantity_range.split("-"))
        return random.randint(min_q, max_q)
    
    async def generate_email(self) -> dict:
        """生成单封邮件"""
        template = await self.template_service.get_random_template()
        customer = self._generate_customer_name(template.region)
        quantity = self._generate_quantity(template.quantity_range)
        
        # 填充模板
        subject = template.subject_template.format(
            product=template.product_name,
            quantity=quantity
        )
        
        body = template.body_template.format(
            product=template.product_name,
            quantity=quantity,
            customer_name=customer["name"],
            company_name=customer["company"],
            email=customer["email"],
            region=template.region,
            destination=customer["company"],
            packing="Blister, 10x10",
            standard="USP/BP"
        )
        
        return {
            "id": f"email_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            "from_address": customer["email"],
            "subject": subject,
            "body": body,
            "priority": "high" if quantity > 1000 else "medium",
            "region": template.region,
            "customer": customer
        }
    
    async def generate_emails(self, count: int) -> List[dict]:
        """批量生成邮件"""
        return [await self.generate_email() for _ in range(count)]
```

### 6.3 API Route Handler

```python
@router.post("/emails/generate", response_model=GeneratedEmailsResponse)
async def generate_emails(request: GenerateEmailsRequest):
    """
    生成并创建新的测试邮件
    
    参数:
        count: 生成数量
        auto_process: 是否自动触发处理流程
        filters: 可选的过滤条件（类型、地区）
    """
    template_service = EmailTemplateService(db)
    generator = EmailGenerator(template_service, db)
    
    # 生成邮件数据
    email_data_list = await generator.generate_emails(request.count)
    
    generated_emails = []
    
    async with db.session() as session:
        for email_data in email_data_list:
            # 创建或查找客户
            customer = await db.get_or_create_customer(
                email=email_data["from_address"],
                defaults={
                    "name": email_data["customer"]["company"],
                    "region": email_data["region"],
                    "tier": "A"
                }
            )
            
            # 创建邮件
            email = Email(
                id=email_data["id"],
                from_address=email_data["from_address"],
                subject=email_data["subject"],
                body=email_data["body"],
                priority=email_data["priority"],
                region=email_data["region"],
                customer_id=customer.id
            )
            session.add(email)
            generated_emails.append(email)
        
        await session.commit()
    
    # 如果启用自动处理，触发处理流程
    if request.auto_process:
        for email in generated_emails:
            # 异步触发处理，不阻塞返回
            asyncio.create_task(process_email(email.id))
    
    return GeneratedEmailsResponse(
        generated_emails=generated_emails,
        total=len(generated_emails),
        auto_process_started=request.auto_process
    )
```

---

## 7. 模板初始化数据

### 7.1 种子脚本 scripts/seed_email_templates.py

```python
#!/usr/bin/env python3
"""
邮件模板数据注入脚本

注入 12 个基础模板，覆盖 4 种邮件类型 x 3 个地区
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from email_agent.config import settings
from email_agent.storage.database import get_database
from email_agent.storage.models import EmailTemplate


TEMPLATES = [
    # RFQ 类型 - Europe
    {
        "type": "rfq",
        "product_name": "Paracetamol 500mg",
        "region": "Europe",
        "quantity_range": "500-1000",
        "subject_template": "Request for Quote - {product}",
        "body_template": """Dear Supplier,

We are interested in purchasing the following products:

- {product}: {quantity} boxes
  - Packing: Blister, 10x10 tablets
  - Standard: USP/BP

Please provide your best quote for delivery to {destination}.

We are a leading pharmaceutical distributor in {region} and this is a potential
long-term partnership.

Best regards,
{customer_name}
{position}
{company_name}
{email}
        """
    },
    # RFQ 类型 - South America
    {
        "type": "rfq",
        "product_name": "Amoxicillin 500mg",
        "region": "South America",
        "quantity_range": "1000-5000",
        "subject_template": "RFQ: {product} - {quantity} boxes to Brazil",
        "body_template": """Good day,

We would like to request a quote for:

Product: {product}
Quantity: {quantity} boxes
Packing: Blister packing, 10 capsules per blister
Standard: USP/BP/EP
Destination: Sao Paulo, Brazil
Required delivery: Within 30 days

We are a large distributor in Brazil and this is a potential long-term partnership.
Please provide your best CIF Santos price.

Required documents:
- Certificate of Analysis
- GMP Certificate
- Free Sale Certificate
- ANVISA registration

Best regards,
{customer_name}
Director of Procurement
{company_name}
{email}
        """
    },
    # RFQ 类型 - Asia
    {
        "type": "rfq",
        "product_name": "Ibuprofen 400mg",
        "region": "Asia",
        "quantity_range": "100-500",
        "subject_template": "Inquiry: {product} for Taiwan",
        "body_template": """Dear Sir/Madam,

We are writing to inquire about your {product}.

Required quantity: {quantity} boxes
Destination: Taipei, Taiwan
Packing: Standard blister packing

Please send us your quotation including:
- FOB price
- Minimum order quantity
- Lead time
- Available certifications

Thank you for your attention.

Best regards,
{customer_name}
{company_name}
{email}
        """
    },
    # Inquiry 类型 - Europe
    {
        "type": "inquiry",
        "product_name": "Paracetamol 1000mg",
        "region": "Europe",
        "quantity_range": "100-500",
        "subject_template": "Product Inquiry - {product}",
        "body_template": """Hello,

We found your company through the pharmaceutical trade directory.

Could you please provide more information about your {product}?

We are particularly interested in:
- Product specifications
- Available packing options
- Certification status for EU market
- Sample availability

Looking forward to your reply.

Best regards,
{customer_name}
{company_name}
{email}
        """
    },
    # Complaint 类型 - Europe
    {
        "type": "complaint",
        "product_name": "Paracetamol 500mg",
        "region": "Europe",
        "quantity_range": "100-500",
        "subject_template": "Product Quality Complaint - Batch #{batch_number}",
        "body_template": """Dear Supplier,

We regret to inform you that we have encountered an issue with our recent order.

Product: {product}
Batch Number: {batch_number}
Quantity Received: {quantity} boxes
Issue Description: [Customer describes the problem]

We kindly request your immediate attention to this matter.

Please advise on the next steps for:
- Return/replacement process
- Credit note issuance
- Investigation timeline

Best regards,
{customer_name}
Quality Manager
{company_name}
{email}
        """
    },
    # Status Check 类型 - Europe
    {
        "type": "status_check",
        "product_name": "Paracetamol 500mg",
        "region": "Europe",
        "quantity_range": "500-1000",
        "subject_template": "Order Status Inquiry - Order #{order_number}",
        "body_template": """Hello,

Could you please provide an update on our order status?

Order Number: {order_number}
Product: {product}
Quantity: {quantity} boxes
Order Date: [Date]

We need to plan our inventory and would appreciate your prompt response.

Thank you for your assistance.

Best regards,
{customer_name}
{company_name}
{email}
        """
    },
    # RFQ - Middle East
    {
        "type": "rfq",
        "product_name": "Amoxicillin 250mg",
        "region": "Middle East",
        "quantity_range": "500-1000",
        "subject_template": "New Partnership Opportunity - {product}",
        "body_template": """Dear Valued Supplier,

We are a leading pharmaceutical distributor in the Middle East region.

We are interested in establishing a long-term partnership with your company
for the supply of:

- {product}: {quantity} boxes

Please provide your best offer including:
- CIF Jebel Ali pricing
- Available quantities
- Delivery timeline
- GCC certification status

Best regards,
{customer_name}
{company_name}
{email}
        """
    },
]


async def inject_templates():
    """注入模板数据到数据库"""
    print("开始注入邮件模板数据...")
    
    db = get_database(settings)
    await db.init_tables()
    
    # 清除现有模板数据
    print("\n清除现有模板数据...")
    async with db.session() as session:
        from sqlalchemy import delete
        await session.execute(delete(EmailTemplate))
        await session.commit()
    
    # 注入新模板
    print("\n注入新模板数据...")
    async with db.session() as session:
        for template_data in TEMPLATES:
            template = EmailTemplate(
                type=template_data["type"],
                product_name=template_data["product_name"],
                region=template_data["region"],
                quantity_range=template_data["quantity_range"],
                subject_template=template_data["subject_template"].strip(),
                body_template=template_data["body_template"].strip(),
                is_active=True
            )
            session.add(template)
        await session.commit()
    
    print(f"成功注入 {len(TEMPLATES)} 个邮件模板")
    print("模板注入完成！")


if __name__ == "__main__":
    asyncio.run(inject_templates())
```

---

## 8. 测试计划

### 8.1 单元测试

```python
# tests/generator/test_email_generator.py

async def test_generate_single_email():
    """测试生成单封邮件"""
    generator = EmailGenerator(template_service, db)
    email = await generator.generate_email()
    assert email["id"] is not None
    assert "@" in email["from_address"]
    assert email["subject"] != ""

async def test_generate_batch_emails():
    """测试批量生成"""
    generator = EmailGenerator(template_service, db)
    emails = await generator.generate_emails(10)
    assert len(emails) == 10

async def test_template_filters():
    """测试模板过滤"""
    template = await template_service.get_random_template(
        template_type="rfq",
        region="Europe"
    )
    assert template.type == "rfq"
    assert template.region == "Europe"
```

### 8.2 E2E 测试

```python
# tests/generator/test_generator_e2e.py

async def test_full_generation_flow():
    """测试完整生成流程"""
    # 1. 调用 API 生成邮件
    response = client.post("/api/emails/generate", json={
        "count": 5,
        "auto_process": False
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["generated_emails"]) == 5
    
    # 2. 验证数据库中有新邮件
    emails = await db.get_all_emails(limit=10)
    assert len(emails) >= 5
```

---

## 9. 预算估算

| 操作 | 成本 |
|------|------|
| 生成邮件 (模板引擎) | $0 (本地生成) |
| 自动触发处理 | ~$0.02-0.05/封 (L1+L3 API 调用) |
| 批量生成 10 封 + 自动处理 | ~$0.20-0.50 |

**建议:**
- 演示时先用 `auto_process=false` 快速生成邮件
- 选择 1-2 封邮件手动触发处理流程展示完整效果

---

## 10. 实施清单

- [ ] 创建 EmailTemplate 模型
- [ ] 实现 EmailTemplateService
- [ ] 实现 EmailGenerator
- [ ] 添加 POST /api/emails/generate 端点
- [ ] 添加 GET /api/emails/templates 端点
- [ ] 创建种子脚本 seed_email_templates.py
- [ ] 创建 GenerateEmailPanel 组件
- [ ] 集成到 Inbox 页面
- [ ] 添加单元测试
- [ ] 添加 E2E 测试
- [ ] 更新 README 文档

---

## 11. 后续扩展

1. **模板管理后台**: 允许管理员通过 UI 添加/编辑模板
2. **模板变量验证**: 确保模板中的占位符都能正确填充
3. **多语言支持**: 不同地区的邮件使用不同语言
4. **邮件签名库**: 不同地区的签名格式
5. **附件支持**: 生成带附件的测试邮件
