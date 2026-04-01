# Email Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现前端"创建新邮件"功能，支持批量生成和自动/手动处理切换，模板数据存储在数据库中

**Architecture:** 后端模板引擎从数据库读取模板配置，随机组合生成邮件内容，前端通过 Inbox 页面顶部按钮触发

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0 Async, React 18, TypeScript, aiosqlite

---

## File Structure

### Backend Files
- **Create:** `src/email_agent/generator/__init__.py` - 生成器模块导出
- **Create:** `src/email_agent/generator/template_service.py` - EmailTemplateService 服务
- **Create:** `src/email_agent/generator/email_generator.py` - EmailGenerator 生成器
- **Create:** `scripts/seed_email_templates.py` - 模板数据注入脚本
- **Modify:** `src/email_agent/storage/models.py` - 添加 EmailTemplate 模型
- **Modify:** `src/email_agent/storage/database.py` - 添加 get_or_create_customer 方法
- **Modify:** `src/email_agent/api/routes.py` - 添加 generate_emails 端点
- **Modify:** `src/email_agent/api/schemas.py` - 添加请求/响应模式

### Frontend Files
- **Create:** `frontend/src/components/GenerateEmailPanel.tsx` - 邮件生成面板组件
- **Create:** `frontend/src/services/emailGenerator.ts` - API 服务层
- **Create:** `frontend/src/types/generator.ts` - TypeScript 类型定义
- **Modify:** `frontend/src/App.tsx` - 集成 GenerateEmailPanel 到 InboxTab

### Test Files
- **Create:** `tests/generator/__init__.py`
- **Create:** `tests/generator/test_template_service.py`
- **Create:** `tests/generator/test_email_generator.py`
- **Create:** `tests/generator/test_generator_e2e.py`

---

## Task 1: EmailTemplate 数据模型

**Files:**
- Modify: `src/email_agent/storage/models.py`
- Test: `tests/storage/test_models.py` (如有)

- [ ] **Step 1: 添加 EmailTemplate 模型到 models.py**

在 models.py 文件末尾，Base 类定义之后，添加以下模型：

```python
class EmailTemplate(Base):
    """
    邮件模板模型
    
    作用:
        存储邮件生成模板配置。
        每个模板包含主题和正文模板，用于生成测试邮件。
    
    表名：email_templates
    
    字段说明:
        id: int 类型，主键 (自增)
        type: str 类型，邮件类型 (inquiry/rfq/complaint/status_check)
        product_name: str 类型，产品名称
        region: str 类型，目标地区
        quantity_range: str 类型，数量范围 (如 "100-500")
        subject_template: str 类型，主题模板
        body_template: str 类型，正文模板
        is_active: bool 类型，是否启用
        created_at: datetime 类型，创建时间
    """
    __tablename__ = "email_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    quantity_range: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_template: Mapped[str] = mapped_column(Text, nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type,
            "product_name": self.product_name,
            "region": self.region,
            "quantity_range": self.quantity_range,
            "subject_template": self.subject_template,
            "body_template": self.body_template,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
```

- [ ] **Step 2: 更新 models.py 导出**

修改 `src/email_agent/storage/__init__.py`，添加 EmailTemplate 导出：

```python
from email_agent.storage.models import (
    Base,
    Customer,
    Email,
    EmailAnalysis,
    AgentExecution,
    PromptVersion,
    EmailTemplate,  # 新增
    init_db_tables,
    drop_db_tables,
)
```

- [ ] **Step 3: 运行测试验证模型**

```bash
cd /data/resume/ai-product-dev-jd/.worktrees/ai-email-agent
python -c "from email_agent.storage.models import EmailTemplate; print('EmailTemplate 模型导入成功')"
```

预期输出：`EmailTemplate 模型导入成功`

- [ ] **Step 4: 提交**

```bash
git add src/email_agent/storage/models.py src/email_agent/storage/__init__.py
git commit -m "feat: add EmailTemplate model for email generator"
```

---

## Task 2: Database 辅助方法

**Files:**
- Modify: `src/email_agent/storage/database.py`
- Test: N/A (由后续任务测试)

- [ ] **Step 1: 添加 get_or_create_customer 方法**

在 database.py 文件中，添加以下方法：

```python
async def get_or_create_customer(
    self, 
    email: str, 
    defaults: dict = None
) -> Customer:
    """
    获取或创建客户
    
    参数:
        email: 客户邮箱地址
        defaults: 创建时使用的默认值 (name, region, tier 等)
    
    返回:
        Customer: 客户对象
    """
    async with self.session() as session:
        # 尝试查找现有客户
        result = await session.execute(
            select(Customer).where(Customer.email == email)
        )
        customer = result.scalar_one_or_none()
        
        if customer:
            return customer
        
        # 创建新客户
        if defaults is None:
            defaults = {}
        
        customer = Customer(
            email=email,
            name=defaults.get("name", "Unknown Customer"),
            region=defaults.get("region", "Unknown"),
            tier=defaults.get("tier", "C")
        )
        session.add(customer)
        await session.commit()
        await session.refresh(customer)
        return customer
```

- [ ] **Step 2: 导入 Customer 模型**

确保 database.py 文件顶部导入了 Customer：

```python
from email_agent.storage.models import (
    Base,
    Customer,
    Email,
    EmailAnalysis,
    # ... 其他导入
)
```

- [ ] **Step 3: 验证方法**

```bash
python -c "from email_agent.storage.database import Database; print('get_or_create_customer 方法已定义')"
```

- [ ] **Step 4: 提交**

```bash
git add src/email_agent/storage/database.py
git commit -m "feat: add get_or_create_customer method to Database"
```

---

## Task 3: EmailTemplateService 服务

**Files:**
- Create: `src/email_agent/generator/__init__.py`
- Create: `src/email_agent/generator/template_service.py`
- Test: `tests/generator/test_template_service.py`

- [ ] **Step 1: 创建 generator 模块目录和初始化文件**

```bash
mkdir -p src/email_agent/generator
```

创建 `src/email_agent/generator/__init__.py`:

```python
"""
邮件生成器模块

提供邮件模板服务和邮件生成功能。
"""
from email_agent.generator.template_service import EmailTemplateService
from email_agent.generator.email_generator import EmailGenerator

__all__ = ["EmailTemplateService", "EmailGenerator"]
```

- [ ] **Step 2: 创建 EmailTemplateService**

创建 `src/email_agent/generator/template_service.py`:

```python
"""
邮件模板服务模块

提供邮件模板的 CRUD 操作和随机选择功能。
"""
import random
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, delete

from email_agent.storage.database import Database
from email_agent.storage.models import EmailTemplate


class EmailTemplateService:
    """
    邮件模板服务
    
    作用:
        管理邮件模板的增删改查，
        支持随机选择模板用于邮件生成。
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    async def get_active_templates(self) -> List[EmailTemplate]:
        """
        获取所有活跃的模板
        
        返回:
            List[EmailTemplate]: 模板列表
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(EmailTemplate).where(EmailTemplate.is_active == True)
            )
            return list(result.scalars().all())
    
    async def get_random_template(
        self,
        template_type: Optional[str] = None,
        region: Optional[str] = None
    ) -> Optional[EmailTemplate]:
        """
        随机获取一个模板
        
        参数:
            template_type: 邮件类型过滤 (inquiry/rfq/complaint/status_check)
            region: 地区过滤 (Europe/Asia/South America/Middle East)
        
        返回:
            Optional[EmailTemplate]: 随机选中的模板，如果没有匹配则返回 None
        """
        templates = await self.get_active_templates()
        
        # 过滤
        if template_type:
            templates = [t for t in templates if t.type == template_type]
        if region:
            templates = [t for t in templates if t.region == region]
        
        return random.choice(templates) if templates else None
    
    async def get_template_by_id(self, template_id: int) -> Optional[EmailTemplate]:
        """
        根据 ID 获取模板
        
        参数:
            template_id: 模板 ID
        
        返回:
            Optional[EmailTemplate]: 模板对象，不存在则返回 None
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(EmailTemplate).where(EmailTemplate.id == template_id)
            )
            return result.scalar_one_or_none()
    
    async def deactivate_template(self, template_id: int) -> bool:
        """
        停用模板
        
        参数:
            template_id: 模板 ID
        
        返回:
            bool: 是否成功停用
        """
        async with self.db.session() as session:
            template = await self.get_template_by_id(template_id)
            if template:
                template.is_active = False
                await session.commit()
                return True
            return False
```

- [ ] **Step 3: 创建测试文件**

创建 `tests/generator/test_template_service.py`:

```python
"""
EmailTemplateService 单元测试
"""
import pytest
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from email_agent.config import settings
from email_agent.storage.database import get_database
from email_agent.storage.models import EmailTemplate
from email_agent.generator.template_service import EmailTemplateService


@pytest.fixture
async def db():
    """测试数据库 fixture"""
    database = get_database(settings)
    await database.init_tables()
    yield database
    # 清理测试数据
    async with database.session() as session:
        await session.execute(delete(EmailTemplate))
        await session.commit()


@pytest.fixture
def template_service(db):
    """模板服务 fixture"""
    return EmailTemplateService(db)


@pytest.mark.asyncio
async def test_get_active_templates_empty(template_service):
    """测试获取空模板列表"""
    templates = await template_service.get_active_templates()
    assert templates == []


@pytest.mark.asyncio
async def test_get_active_templates_with_data(template_service, db):
    """测试获取有数据的模板列表"""
    # 添加测试数据
    async with db.session() as session:
        template = EmailTemplate(
            type="rfq",
            product_name="Test Product",
            region="Europe",
            quantity_range="100-500",
            subject_template="Test Subject",
            body_template="Test Body",
            is_active=True
        )
        session.add(template)
        await session.commit()
    
    templates = await template_service.get_active_templates()
    assert len(templates) == 1
    assert templates[0].product_name == "Test Product"


@pytest.mark.asyncio
async def test_get_random_template_no_filters(template_service, db):
    """测试随机获取模板（无过滤）"""
    # 添加多个模板
    async with db.session() as session:
        for i in range(3):
            template = EmailTemplate(
                type="rfq",
                product_name=f"Product {i}",
                region="Europe",
                quantity_range="100-500",
                subject_template=f"Subject {i}",
                body_template=f"Body {i}",
                is_active=True
            )
            session.add(template)
        await session.commit()
    
    template = await template_service.get_random_template()
    assert template is not None
    assert template.type == "rfq"


@pytest.mark.asyncio
async def test_get_random_template_with_type_filter(template_service, db):
    """测试类型过滤"""
    # 添加不同类型模板
    async with db.session() as session:
        for template_type in ["rfq", "inquiry", "complaint"]:
            template = EmailTemplate(
                type=template_type,
                product_name="Test",
                region="Europe",
                quantity_range="100-500",
                subject_template="Test",
                body_template="Test",
                is_active=True
            )
            session.add(template)
        await session.commit()
    
    # 过滤 rfq 类型
    template = await template_service.get_random_template(template_type="rfq")
    assert template is not None
    assert template.type == "rfq"
    
    # 过滤 inquiry 类型
    template = await template_service.get_random_template(template_type="inquiry")
    assert template is not None
    assert template.type == "inquiry"


@pytest.mark.asyncio
async def test_get_random_template_no_match(template_service, db):
    """测试无匹配结果"""
    # 添加一个模板
    async with db.session() as session:
        template = EmailTemplate(
            type="rfq",
            product_name="Test",
            region="Europe",
            quantity_range="100-500",
            subject_template="Test",
            body_template="Test",
            is_active=True
        )
        session.add(template)
        await session.commit()
    
    # 请求不存在的类型
    result = await template_service.get_random_template(template_type="nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_deactivate_template(template_service, db):
    """测试停用模板"""
    # 添加模板
    async with db.session() as session:
        template = EmailTemplate(
            type="rfq",
            product_name="Test",
            region="Europe",
            quantity_range="100-500",
            subject_template="Test",
            body_template="Test",
            is_active=True
        )
        session.add(template)
        await session.commit()
        template_id = template.id
    
    # 停用
    result = await template_service.deactivate_template(template_id)
    assert result is True
    
    # 验证已停用
    templates = await template_service.get_active_templates()
    assert len(templates) == 0


@pytest.mark.asyncio
async def test_deactivate_template_not_found(template_service):
    """测试停用不存在的模板"""
    result = await template_service.deactivate_template(99999)
    assert result is False
```

- [ ] **Step 4: 运行测试**

```bash
cd /data/resume/ai-product-dev-jd/.worktrees/ai-email-agent
pytest tests/generator/test_template_service.py -v
```

预期：所有测试通过

- [ ] **Step 5: 提交**

```bash
git add src/email_agent/generator/ tests/generator/
git commit -m "feat: implement EmailTemplateService with unit tests"
```

---

## Task 4: EmailGenerator 生成器

**Files:**
- Create: `src/email_agent/generator/email_generator.py`
- Test: `tests/generator/test_email_generator.py`

- [ ] **Step 1: 创建 EmailGenerator**

创建 `src/email_agent/generator/email_generator.py`:

```python
"""
邮件生成器模块

根据模板生成随机邮件内容。
"""
import random
from datetime import datetime
from typing import Dict, List

from email_agent.storage.database import Database
from email_agent.generator.template_service import EmailTemplateService


class EmailGenerator:
    """
    邮件生成器
    
    作用:
        根据模板生成随机邮件内容，
        支持批量生成。
    """
    
    # 客户名称库（按地区）
    CUSTOMER_NAMES = {
        "Europe": [
            ("John Smith", "PharmaCom UK", "john.smith@pharmacom.co.uk"),
            ("Maria Garcia", "Salud ES", "maria.garcia@salud.es"),
            ("Pierre Dubois", "Pharma FR", "pierre.dubois@pharma.fr"),
            ("Hans Mueller", "Medi DE", "hans.mueller@medi.de"),
        ],
        "South America": [
            ("Ana Silva", "Pharma Brazil", "ana.silva@pharma.br"),
            ("Carlos Rodriguez", "Medicina AR", "carlos@medicina.ar"),
            ("Lucia Fernandez", "Salud CL", "lucia.fernandez@salud.cl"),
        ],
        "Asia": [
            ("Wei Chen", "MediCN", "wei.chen@medicn.com"),
            ("Yuki Tanaka", "Pharma JP", "yuki.tanaka@pharma.jp"),
            ("Kim Min-jun", "Health KR", "minjun.kim@health.kr"),
        ],
        "Middle East": [
            ("Ahmed Hassan", "MedPharm UAE", "ahmed.hassan@medpharm.ae"),
            ("Fatima Al-Zahra", "Gulf Med", "fatima@gulfmed.com"),
        ],
    }
    
    # 默认包装和标准
    PACKING_OPTIONS = [
        "Blister, 10x10 tablets",
        "Blister, 20x5 tablets",
        "Bottle, 100 capsules",
        "Box, 50 tablets",
    ]
    
    STANDARDS = ["USP/BP", "USP", "BP", "EP", "GMP"]
    
    def __init__(self, template_service: EmailTemplateService, db: Database):
        self.template_service = template_service
        self.db = db
    
    def _generate_customer_name(self, region: str) -> Dict[str, str]:
        """
        生成指定地区的随机客户信息
        
        参数:
            region: 地区名称
        
        返回:
            dict: 包含 name, company, email 的字典
        """
        names = self.CUSTOMER_NAMES.get(region, self.CUSTOMER_NAMES["Europe"])
        name, company, email = random.choice(names)
        return {"name": name, "company": company, "email": email}
    
    def _generate_quantity(self, quantity_range: str) -> int:
        """
        根据范围生成随机数量
        
        参数:
            quantity_range: 数量范围字符串 (如 "100-500")
        
        返回:
            int: 随机数量
        """
        try:
            min_q, max_q = map(int, quantity_range.split("-"))
            return random.randint(min_q, max_q)
        except (ValueError, AttributeError):
            return 500  # 默认值
    
    def _generate_email_id(self) -> str:
        """
        生成唯一邮件 ID
        
        返回:
            str: 邮件 ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = random.randint(1000, 9999)
        return f"email_{timestamp}_{random_suffix}"
    
    async def generate_email(self) -> Dict:
        """
        生成单封邮件
        
        返回:
            dict: 包含邮件所有字段的字典
        """
        # 获取随机模板
        template = await self.template_service.get_random_template()
        if not template:
            raise ValueError("No active templates found")
        
        # 生成客户信息
        customer = self._generate_customer_name(template.region)
        
        # 生成数量
        quantity = self._generate_quantity(template.quantity_range)
        
        # 随机选择包装和标准
        packing = random.choice(self.PACKING_OPTIONS)
        standard = random.choice(self.STANDARDS)
        
        # 填充主题模板
        subject = template.subject_template.format(
            product=template.product_name,
            quantity=quantity
        )
        
        # 填充正文模板
        body = template.body_template.format(
            product=template.product_name,
            quantity=quantity,
            customer_name=customer["name"],
            company_name=customer["company"],
            email=customer["email"],
            region=template.region,
            destination=customer["company"],
            packing=packing,
            standard=standard,
            batch_number=f"BATCH{random.randint(10000, 99999)}",
            order_number=f"ORD{random.randint(100000, 999999)}"
        )
        
        # 根据数量决定优先级
        priority = "high" if quantity > 1000 else "medium"
        
        return {
            "id": self._generate_email_id(),
            "from_address": customer["email"],
            "subject": subject,
            "body": body,
            "priority": priority,
            "region": template.region,
            "customer": customer,
            "quantity": quantity,
            "product": template.product_name
        }
    
    async def generate_emails(self, count: int) -> List[Dict]:
        """
        批量生成邮件
        
        参数:
            count: 生成数量
        
        返回:
            List[Dict]: 邮件列表
        """
        return [await self.generate_email() for _ in range(count)]
```

- [ ] **Step 2: 创建测试文件**

创建 `tests/generator/test_email_generator.py`:

```python
"""
EmailGenerator 单元测试
"""
import pytest
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from email_agent.config import settings
from email_agent.storage.database import get_database
from email_agent.storage.models import EmailTemplate
from email_agent.generator.template_service import EmailTemplateService
from email_agent.generator.email_generator import EmailGenerator


@pytest.fixture
async def db():
    """测试数据库 fixture"""
    database = get_database(settings)
    await database.init_tables()
    yield database


@pytest.fixture
def template_service(db):
    """模板服务 fixture"""
    return EmailTemplateService(db)


@pytest.fixture
def generator(template_service, db):
    """生成器 fixture"""
    return EmailGenerator(template_service, db)


@pytest.fixture
async def setup_templates(db):
    """设置测试模板"""
    templates_data = [
        {
            "type": "rfq",
            "product_name": "Paracetamol 500mg",
            "region": "Europe",
            "quantity_range": "500-1000",
            "subject_template": "Request for Quote - {product}",
            "body_template": "Dear Supplier, We need {quantity} boxes of {product}."
        },
        {
            "type": "inquiry",
            "product_name": "Ibuprofen 400mg",
            "region": "Asia",
            "quantity_range": "100-500",
            "subject_template": "Product Inquiry - {product}",
            "body_template": "Hello, Tell me about {product}."
        }
    ]
    
    async with db.session() as session:
        for data in templates_data:
            template = EmailTemplate(**data, is_active=True)
            session.add(template)
        await session.commit()


@pytest.mark.asyncio
async def test_generate_single_email(generator, setup_templates):
    """测试生成单封邮件"""
    email = await generator.generate_email()
    
    assert email["id"] is not None
    assert email["from_address"] is not None
    assert "@" in email["from_address"]
    assert email["subject"] != ""
    assert email["body"] != ""
    assert email["priority"] in ["high", "medium"]
    assert email["region"] in ["Europe", "Asia", "South America", "Middle East"]


@pytest.mark.asyncio
async def test_generate_email_id_format(generator, setup_templates):
    """测试邮件 ID 格式"""
    email = await generator.generate_email()
    
    # ID 格式：email_YYYYMMDDHHMMSS_XXXX
    pattern = r"email_\d{14}_\d{4}"
    assert re.match(pattern, email["id"])


@pytest.mark.asyncio
async def test_generate_email_quantity_in_range(generator, setup_templates):
    """测试生成数量在范围内"""
    email = await generator.generate_email()
    
    # Europe 模板范围是 500-1000
    if email["region"] == "Europe":
        assert 500 <= email["quantity"] <= 1000
    elif email["region"] == "Asia":
        assert 100 <= email["quantity"] <= 500


@pytest.mark.asyncio
async def test_generate_email_priority_logic(generator, setup_templates):
    """测试优先级逻辑"""
    email = await generator.generate_email()
    
    if email["quantity"] > 1000:
        assert email["priority"] == "high"
    else:
        assert email["priority"] in ["high", "medium"]


@pytest.mark.asyncio
async def test_generate_batch_emails(generator, setup_templates):
    """测试批量生成"""
    emails = await generator.generate_emails(5)
    
    assert len(emails) == 5
    
    # 验证所有 ID 唯一
    ids = [e["id"] for e in emails]
    assert len(ids) == len(set(ids))
    
    # 验证每个邮件都有必要字段
    for email in emails:
        assert email["id"] is not None
        assert "@" in email["from_address"]
        assert email["subject"] != ""


@pytest.mark.asyncio
async def test_generate_no_templates(generator, db):
    """测试没有模板时抛出错误"""
    # 确保没有模板
    async with db.session() as session:
        await session.execute(delete(EmailTemplate))
        await session.commit()
    
    with pytest.raises(ValueError, match="No active templates found"):
        await generator.generate_email()
```

- [ ] **Step 3: 添加必要的导入**

确保 test 文件顶部有必要的导入：

```python
from sqlalchemy import delete
```

- [ ] **Step 4: 运行测试**

```bash
cd /data/resume/ai-product-dev-jd/.worktrees/ai-email-agent
pytest tests/generator/test_email_generator.py -v
```

预期：所有测试通过

- [ ] **Step 5: 提交**

```bash
git add src/email_agent/generator/email_generator.py tests/generator/test_email_generator.py
git commit -m "feat: implement EmailGenerator with batch generation and unit tests"
```

---

## Task 5: API Schemas 和端点

**Files:**
- Modify: `src/email_agent/api/schemas.py`
- Modify: `src/email_agent/api/routes.py`
- Test: `tests/api/test_generator_api.py`

- [ ] **Step 1: 添加 API Schema**

修改 `src/email_agent/api/schemas.py`，添加以下模式：

```python
# 邮件生成相关 Schema
class GenerateEmailsRequest(BaseModel):
    """生成邮件请求"""
    count: int = Field(1, ge=1, le=100, description="生成数量")
    auto_process: bool = Field(False, description="是否自动触发处理流程")
    filters: Optional[Dict[str, str]] = Field(None, description="过滤条件 (type, region)")


class GeneratedEmailCustomer(BaseModel):
    """生成的邮件客户信息"""
    name: str
    company: str
    email: str


class GeneratedEmail(BaseModel):
    """生成的单封邮件"""
    id: str
    from_address: str
    subject: str
    preview: str
    priority: str
    status: str
    region: str
    customer: GeneratedEmailCustomer


class GeneratedEmailsResponse(BaseModel):
    """生成邮件响应"""
    generated_emails: List[GeneratedEmail]
    total: int
    auto_process_started: bool


class EmailTemplateResponse(BaseModel):
    """模板响应"""
    id: int
    type: str
    product_name: str
    region: str
    quantity_range: str
    is_active: bool
    created_at: str


class EmailTemplatesResponse(BaseModel):
    """模板列表响应"""
    templates: List[EmailTemplateResponse]
    total: int
```

- [ ] **Step 2: 更新 routes.py 导入**

修改 `src/email_agent/api/routes.py`，添加导入：

```python
from email_agent.generator import EmailTemplateService, EmailGenerator
from email_agent.api.schemas import (
    # ... 现有导入
    GenerateEmailsRequest,
    GeneratedEmailsResponse,
    GeneratedEmail,
    GeneratedEmailCustomer,
    EmailTemplatesResponse,
    EmailTemplateResponse,
)
```

- [ ] **Step 3: 添加生成邮件端点**

在 routes.py 中添加：

```python
@router.post("/emails/generate", response_model=GeneratedEmailsResponse)
async def generate_emails(request: GenerateEmailsRequest):
    """
    生成并创建新的测试邮件
    
    参数:
        count: 生成数量 (1-100)
        auto_process: 是否自动触发处理流程
        filters: 可选的过滤条件（类型、地区）
    
    返回:
        GeneratedEmailsResponse: 生成的邮件列表
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
                customer_id=customer.id,
                status="pending"
            )
            session.add(email)
            
            # 添加到返回结果
            generated_emails.append(
                GeneratedEmail(
                    id=email.id,
                    from_address=email.from_address,
                    subject=email.subject,
                    preview=email.body[:100] + "..." if len(email.body) > 100 else email.body,
                    priority=email.priority,
                    status="pending",
                    region=email.region,
                    customer=GeneratedEmailCustomer(
                        name=customer.name,
                        company=customer.name,
                        email=customer.email
                    )
                )
            )
        
        await session.commit()
    
    # 如果启用自动处理，异步触发处理流程
    if request.auto_process:
        from email_agent.layer1.classifier import EmailClassifier
        from email_agent.config import settings
        
        classifier = EmailClassifier(settings)
        
        for email_data in email_data_list:
            # 异步触发分类（触发完整 L1→L2→L3 流程）
            asyncio.create_task(
                classifier.classify(
                    email_id=email_data["id"],
                    email_body=email_data["body"],
                    subject=email_data["subject"]
                )
            )
    
    return GeneratedEmailsResponse(
        generated_emails=generated_emails,
        total=len(generated_emails),
        auto_process_started=request.auto_process
    )


@router.get("/emails/templates", response_model=EmailTemplatesResponse)
async def list_templates():
    """
    获取所有活跃的邮件模板
    
    返回:
        EmailTemplatesResponse: 模板列表
    """
    template_service = EmailTemplateService(db)
    templates = await template_service.get_active_templates()
    
    return EmailTemplatesResponse(
        templates=[
            EmailTemplateResponse(
                id=t.id,
                type=t.type,
                product_name=t.product_name,
                region=t.region,
                quantity_range=t.quantity_range,
                is_active=t.is_active,
                created_at=t.created_at.isoformat() if t.created_at else None
            )
            for t in templates
        ],
        total=len(templates)
    )
```

- [ ] **Step 4: 创建 API 测试**

创建 `tests/api/test_generator_api.py`:

```python
"""
邮件生成 API 端到端测试
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from email_agent.main import app
from email_agent.storage.database import get_database
from email_agent.storage.models import EmailTemplate


client = TestClient(app)


@pytest.fixture
async def setup_templates():
    """设置测试模板"""
    db = get_database()
    await db.init_tables()
    
    async with db.session() as session:
        template = EmailTemplate(
            type="rfq",
            product_name="Paracetamol 500mg",
            region="Europe",
            quantity_range="500-1000",
            subject_template="Request for Quote - {product}",
            body_template="Dear Supplier, We need {quantity} boxes.",
            is_active=True
        )
        session.add(template)
        await session.commit()


@pytest.mark.asyncio
def test_generate_emails_no_auth(setup_templates):
    """测试生成邮件（无认证）"""
    response = client.post("/api/emails/generate", json={"count": 2})
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["generated_emails"]) == 2


@pytest.mark.asyncio
def test_generate_emails_with_auto_process(setup_templates):
    """测试带自动处理的生成"""
    response = client.post("/api/emails/generate", json={
        "count": 1,
        "auto_process": True
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["auto_process_started"] is True


@pytest.mark.asyncio
def test_generate_emails_invalid_count(setup_templates):
    """测试无效数量"""
    response = client.post("/api/emails/generate", json={"count": 0})
    assert response.status_code == 422  # Validation error
    
    response = client.post("/api/emails/generate", json={"count": 101})
    assert response.status_code == 422


@pytest.mark.asyncio
def test_list_templates(setup_templates):
    """测试获取模板列表"""
    response = client.get("/api/emails/templates")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["templates"]) >= 1
```

- [ ] **Step 5: 运行测试**

```bash
cd /data/resume/ai-product-dev-jd/.worktrees/ai-email-agent
pytest tests/api/test_generator_api.py -v
```

- [ ] **Step 6: 提交**

```bash
git add src/email_agent/api/schemas.py src/email_agent/api/routes.py tests/api/test_generator_api.py
git commit -m "feat: add /api/emails/generate and /api/emails/templates endpoints"
```

---

## Task 6: 模板种子脚本

**Files:**
- Create: `scripts/seed_email_templates.py`

- [ ] **Step 1: 创建种子脚本**

创建 `scripts/seed_email_templates.py`:

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
  - Packing: {packing}
  - Standard: {standard}

Please provide your best quote for delivery to {destination}.

We are a leading pharmaceutical distributor in {region} and this is a potential long-term partnership.

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

Please provide your best CIF Santos price including:
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
    # RFQ 类型 - Middle East
    {
        "type": "rfq",
        "product_name": "Amoxicillin 250mg",
        "region": "Middle East",
        "quantity_range": "500-1000",
        "subject_template": "New Partnership Opportunity - {product}",
        "body_template": """Dear Valued Supplier,

We are a leading pharmaceutical distributor in the Middle East region.

We are interested in establishing a long-term partnership with your company for:

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
    # Inquiry 类型 - South America
    {
        "type": "inquiry",
        "product_name": "Omeprazole 20mg",
        "region": "South America",
        "quantity_range": "200-1000",
        "subject_template": "Information Request - {product}",
        "body_template": """Dear Supplier,

We are interested in learning more about your {product}.

Could you please provide:
- Technical specifications
- Registration status in South America
- Pricing information for {quantity} boxes
- Estimated delivery time to Argentina

Thank you for your assistance.

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
    # Complaint 类型 - Asia
    {
        "type": "complaint",
        "product_name": "Ibuprofen 400mg",
        "region": "Asia",
        "quantity_range": "50-200",
        "subject_template": "Damaged Shipment - Order #{order_number}",
        "body_template": """Dear Supplier,

We received our shipment but found some damaged products.

Order Number: {order_number}
Product: {product}
Damage Description: [Details of damage]
Photos: [Attached]

We request your support for replacement or refund.

Please respond within 3 business days.

Best regards,
{customer_name}
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
    # Status Check 类型 - South America
    {
        "type": "status_check",
        "product_name": "Amoxicillin 500mg",
        "region": "South America",
        "quantity_range": "200-1000",
        "subject_template": "Shipment Tracking - {product}",
        "body_template": """Dear Supplier,

Could you please provide tracking information for our order?

Product: {product}
Quantity: {quantity} boxes
Destination: Buenos Aires, Argentina

We need to coordinate with our warehouse for receipt.

Looking forward to your reply.

Best regards,
{customer_name}
{company_name}
{email}
        """
    },
    # Status Check 类型 - Middle East
    {
        "type": "status_check",
        "product_name": "Omeprazole 40mg",
        "region": "Middle East",
        "quantity_range": "100-500",
        "subject_template": "Delivery Confirmation Required - {product}",
        "body_template": """Dear Supplier,

We need confirmation of the expected delivery date for:

Product: {product}
Quantity: {quantity} boxes
Destination: Dubai, UAE

Please provide:
- Expected shipping date
- Estimated arrival
- Tracking number (if available)

Thank you.

Best regards,
{customer_name}
{company_name}
{email}
        """
    },
    # Inquiry 类型 - Asia (Additional)
    {
        "type": "inquiry",
        "product_name": "Metformin 500mg",
        "region": "Asia",
        "quantity_range": "500-2000",
        "subject_template": "Partnership Inquiry - {product}",
        "body_template": """Dear Sir/Madam,

We are a pharmaceutical distributor based in Southeast Asia.

We are interested in distributing your {product} in our region.

Could you please provide:
- Product catalog
- Pricing for bulk orders ({quantity}+ boxes)
- Distribution agreement terms
- Marketing support available

Looking forward to a fruitful partnership.

Best regards,
{customer_name}
Business Development Manager
{company_name}
{email}
        """
    },
]


async def inject_templates():
    """注入模板数据到数据库"""
    print("=" * 60)
    print("邮件模板数据注入脚本")
    print("=" * 60)
    print("\n开始注入邮件模板数据...")
    
    db = get_database(settings)
    await db.init_tables()
    
    # 清除现有模板数据
    print("\n[1/3] 清除现有模板数据...")
    async with db.session() as session:
        from sqlalchemy import delete
        await session.execute(delete(EmailTemplate))
        await session.commit()
    print("      现有数据已清除")
    
    # 注入新模板
    print("\n[2/3] 注入新模板数据...")
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
    
    print(f"      成功注入 {len(TEMPLATES)} 个邮件模板")
    
    # 验证
    print("\n[3/3] 验证注入数据...")
    async with db.session() as session:
        from sqlalchemy import select, func
        result = await session.execute(select(func.count()).select_from(EmailTemplate))
        count = result.scalar()
    print(f"      数据库中共有 {count} 个模板")
    
    print("\n" + "=" * 60)
    print("模板注入完成！")
    print("=" * 60)
    print("\n使用示例:")
    print("  # 前端点击'创建新邮件'按钮")
    print("  # 或调用 API: POST /api/emails/generate")
    print("  curl -X POST http://localhost:8000/api/emails/generate \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"count\": 5, \"auto_process\": false}'")


if __name__ == "__main__":
    asyncio.run(inject_templates())
```

- [ ] **Step 2: 运行种子脚本**

```bash
cd /data/resume/ai-product-dev-jd/.worktrees/ai-email-agent
python scripts/seed_email_templates.py
```

预期输出：成功注入 12 个模板

- [ ] **Step 3: 验证数据**

```bash
python -c "
import asyncio
from email_agent.storage.database import get_database
from email_agent.storage.models import EmailTemplate

async def check():
    db = get_database()
    async with db.session() as session:
        from sqlalchemy import select
        result = await session.execute(select(EmailTemplate))
        templates = result.scalars().all()
        print(f'数据库中有 {len(templates)} 个模板')
        for t in templates[:3]:
            print(f'  - [{t.type}] {t.product_name} ({t.region})')

asyncio.run(check())
```

- [ ] **Step 4: 提交**

```bash
git add scripts/seed_email_templates.py
git commit -m "scripts: add email template seed script with 12 templates"
```

---

## Task 7: 前端 TypeScript 类型定义

**Files:**
- Create: `frontend/src/types/generator.ts`

- [ ] **Step 1: 创建类型定义**

创建 `frontend/src/types/generator.ts`:

```typescript
/**
 * 邮件生成器相关类型定义
 */

/** 邮件生成请求 */
export interface GenerateEmailsRequest {
  /** 生成数量 (1-100) */
  count: number;
  /** 是否自动触发处理流程 */
  auto_process: boolean;
  /** 可选的过滤条件 */
  filters?: {
    type?: string;
    region?: string;
  };
}

/** 生成的客户信息 */
export interface GeneratedCustomer {
  /** 客户名称 */
  name: string;
  /** 公司名称 */
  company: string;
  /** 邮箱地址 */
  email: string;
}

/** 生成的邮件 */
export interface GeneratedEmail {
  /** 邮件 ID */
  id: string;
  /** 发件人邮箱 */
  from_address: string;
  /** 邮件主题 */
  subject: string;
  /** 邮件预览 */
  preview: string;
  /** 优先级 */
  priority: 'low' | 'medium' | 'high';
  /** 状态 */
  status: string;
  /** 地区 */
  region: string;
  /** 客户信息 */
  customer: GeneratedCustomer;
}

/** 邮件生成响应 */
export interface GenerateEmailsResponse {
  /** 生成的邮件列表 */
  generated_emails: GeneratedEmail[];
  /** 总数 */
  total: number;
  /** 是否开始自动处理 */
  auto_process_started: boolean;
}

/** 模板响应 */
export interface EmailTemplate {
  /** 模板 ID */
  id: number;
  /** 邮件类型 */
  type: string;
  /** 产品名称 */
  product_name: string;
  /** 地区 */
  region: string;
  /** 数量范围 */
  quantity_range: string;
  /** 是否启用 */
  is_active: boolean;
  /** 创建时间 */
  created_at: string;
}

/** 模板列表响应 */
export interface EmailTemplatesResponse {
  /** 模板列表 */
  templates: EmailTemplate[];
  /** 总数 */
  total: number;
}
```

- [ ] **Step 2: 更新类型导出**

修改 `frontend/src/types/api.ts`（如存在），添加导出：

```typescript
export * from './generator';
```

或者直接更新主类型文件。

- [ ] **Step 3: 验证 TypeScript 编译**

```bash
cd frontend
npm run build
```

确保没有类型错误。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/types/generator.ts
git commit -m "feat(types): add TypeScript types for email generator"
```

---

## Task 8: 前端 API 服务层

**Files:**
- Create: `frontend/src/services/emailGenerator.ts`

- [ ] **Step 1: 创建 API 服务**

创建 `frontend/src/services/emailGenerator.ts`:

```typescript
/**
 * 邮件生成器 API 服务
 */

import type {
  GenerateEmailsRequest,
  GenerateEmailsResponse,
  EmailTemplatesResponse,
  GeneratedEmail,
} from '../types/generator';

const API_BASE_URL = '/api';

/**
 * 生成测试邮件
 * @param request 生成请求
 * @returns 生成的邮件列表
 */
export async function generateEmails(
  request: GenerateEmailsRequest
): Promise<GenerateEmailsResponse> {
  const response = await fetch(`${API_BASE_URL}/emails/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '生成失败' }));
    throw new Error(error.detail || '生成邮件失败');
  }

  return response.json();
}

/**
 * 获取邮件模板列表
 * @returns 模板列表响应
 */
export async function getEmailTemplates(): Promise<EmailTemplatesResponse> {
  const response = await fetch(`${API_BASE_URL}/emails/templates`);

  if (!response.ok) {
    throw new Error('获取模板列表失败');
  }

  return response.json();
}

/**
 * 快速生成单封邮件
 * @param autoProcess 是否自动处理
 * @returns 生成的邮件
 */
export async function generateSingleEmail(
  autoProcess: boolean = false
): Promise<GeneratedEmail> {
  const response = await generateEmails({
    count: 1,
    auto_process: autoProcess,
  });

  return response.generated_emails[0];
}
```

- [ ] **Step 2: 更新服务导出**

修改 `frontend/src/services/index.ts`（如存在）：

```typescript
export * from './emailGenerator';
```

- [ ] **Step 3: 验证 TypeScript 编译**

```bash
cd frontend
npm run build
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/services/emailGenerator.ts
git commit -m "feat(services): add email generator API service"
```

---

## Task 9: GenerateEmailPanel 组件

**Files:**
- Create: `frontend/src/components/GenerateEmailPanel.tsx`

- [ ] **Step 1: 创建组件**

创建 `frontend/src/components/GenerateEmailPanel.tsx`:

```tsx
/**
 * 邮件生成面板组件
 * 
 * 用于在 Inbox 页面顶部创建新的测试邮件
 */

import React, { useState, useCallback } from 'react';
import { generateEmails } from '../services/emailGenerator';
import type { GeneratedEmail } from '../types/generator';

interface GenerateEmailPanelProps {
  /** 邮件生成成功回调 */
  onEmailsGenerated?: (emails: GeneratedEmail[]) => void;
}

export const GenerateEmailPanel: React.FC<GenerateEmailPanelProps> = ({
  onEmailsGenerated,
}) => {
  const [count, setCount] = useState<number>(1);
  const [autoProcess, setAutoProcess] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = useCallback(async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await generateEmails({
        count,
        auto_process: autoProcess,
      });

      // 通知父组件
      onEmailsGenerated?.(response.generated_emails);

      // 如果启用自动处理，显示提示
      if (autoProcess) {
        console.log(`已生成 ${response.total} 封邮件，处理流程已启动`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '生成失败';
      setError(message);
    } finally {
      setIsGenerating(false);
    }
  }, [count, autoProcess, onEmailsGenerated]);

  return (
    <div className="flex items-center gap-3 bg-[#1e293b] p-3 rounded-lg border border-[#334155]">
      {/* 生成按钮 */}
      <button
        onClick={handleGenerate}
        disabled={isGenerating}
        className="px-4 py-2 bg-[#3b82f6] text-white rounded-md hover:bg-[#2563eb] disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors"
      >
        {isGenerating ? (
          <span className="flex items-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            生成中...
          </span>
        ) : (
          '➕ 创建新邮件'
        )}
      </button>

      {/* 数量选择 */}
      <select
        value={count}
        onChange={(e) => setCount(Number(e.target.value))}
        disabled={isGenerating}
        className="px-3 py-2 bg-[#0f172a] text-[#e2e8f0] rounded-md border border-[#334155] text-sm focus:outline-none focus:ring-2 focus:ring-[#3b82f6] disabled:opacity-50"
      >
        <option value={1}>1 封</option>
        <option value={3}>3 封</option>
        <option value={5}>5 封</option>
        <option value={10}>10 封</option>
        <option value={20}>20 封</option>
        <option value={50}>50 封</option>
      </select>

      {/* 自动处理开关 */}
      <label className="flex items-center gap-2 text-sm text-[#94a3b8] cursor-pointer">
        <input
          type="checkbox"
          checked={autoProcess}
          onChange={(e) => setAutoProcess(e.target.checked)}
          disabled={isGenerating}
          className="w-4 h-4 rounded border-[#334155] bg-[#0f172a] text-[#3b82f6] focus:ring-[#3b82f6] focus:ring-2 disabled:opacity-50"
        />
        自动处理
      </label>

      {/* 错误提示 */}
      {error && (
        <span className="text-red-400 text-sm ml-2">
          {error}
        </span>
      )}

      {/* 帮助提示 */}
      <div className="ml-auto text-xs text-[#64748b]">
        {autoProcess ? '生成后自动进入 AI 处理流程' : '生成后需手动点击处理'}
      </div>
    </div>
  );
};

export default GenerateEmailPanel;
```

- [ ] **Step 2: 验证 TypeScript 编译**

```bash
cd frontend
npm run build
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/GenerateEmailPanel.tsx
git commit -m "feat(components): add GenerateEmailPanel component"
```

---

## Task 10: 集成到 Inbox 页面

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 导入组件**

修改 `frontend/src/App.tsx`，在文件顶部添加导入：

```typescript
import { GenerateEmailPanel } from './components/GenerateEmailPanel';
import type { GeneratedEmail } from './types/generator';
```

- [ ] **Step 2: 添加回调处理**

在 App 组件中添加处理函数：

```typescript
const handleNewEmailsGenerated = useCallback((emails: GeneratedEmail[]) => {
  console.log('新邮件已生成:', emails);
  // 刷新邮件列表
  refetch(); // 假设使用了 react-query 的 refetch
}, [refetch]);
```

- [ ] **Step 3: 在 InboxTab 中添加组件**

找到 Inbox 页面渲染部分，在顶部添加：

```tsx
{activeTab === 'inbox' && (
  <InboxTab
    selectedEmail={selectedEmail}
    onSelectEmail={setSelectedEmail}
    onEmailsGenerated={handleNewEmailsGenerated}
  />
)}
```

- [ ] **Step 4: 更新 InboxTab 组件**

修改或创建 InboxTab 组件，接收新 props：

```typescript
interface InboxTabProps {
  selectedEmail: string | null;
  onSelectEmail: (id: string | null) => void;
  onEmailsGenerated?: (emails: GeneratedEmail[]) => void;
}
```

在组件渲染中添加：

```tsx
<div className="mb-4 flex justify-between items-center">
  <h2 className="text-xl font-bold text-[#e2e8f0]">📨 收件箱 | Inbox</h2>
  <GenerateEmailPanel onEmailsGenerated={onEmailsGenerated} />
</div>
```

- [ ] **Step 5: 验证 TypeScript 编译**

```bash
cd frontend
npm run build
```

- [ ] **Step 6: 提交**

```bash
git add frontend/src/App.tsx
git commit -m "feat: integrate GenerateEmailPanel into Inbox page"
```

---

## Task 11: E2E 测试

**Files:**
- Create: `tests/generator/test_generator_e2e.py`

- [ ] **Step 1: 创建 E2E 测试**

创建 `tests/generator/test_generator_e2e.py`:

```python
"""
邮件生成器端到端测试
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from email_agent.config import settings
from email_agent.storage.database import get_database
from email_agent.storage.models import EmailTemplate, Email, Customer
from email_agent.generator import EmailTemplateService, EmailGenerator


@pytest.fixture
async def db():
    """测试数据库 fixture"""
    database = get_database(settings)
    await database.init_tables()
    yield database
    # 清理
    async with database.session() as session:
        from sqlalchemy import delete
        await session.execute(delete(Email))
        await session.execute(delete(EmailTemplate))
        await session.commit()


@pytest.fixture
async def setup_templates(db):
    """设置测试模板"""
    templates_data = [
        {"type": "rfq", "product_name": "Paracetamol 500mg", "region": "Europe", "quantity_range": "500-1000", "subject_template": "RFQ: {product}", "body_template": "Need {quantity} boxes", "is_active": True},
        {"type": "inquiry", "product_name": "Ibuprofen 400mg", "region": "Asia", "quantity_range": "100-500", "subject_template": "Inquiry: {product}", "body_template": "Tell me about {product}", "is_active": True},
        {"type": "complaint", "product_name": "Amoxicillin 500mg", "region": "South America", "quantity_range": "200-1000", "subject_template": "Complaint: {product}", "body_template": "Issue with {product}", "is_active": True},
    ]
    
    async with db.session() as session:
        for data in templates_data:
            template = EmailTemplate(**data)
            session.add(template)
        await session.commit()


@pytest.mark.asyncio
async def test_full_generation_flow(db, setup_templates):
    """测试完整生成流程"""
    template_service = EmailTemplateService(db)
    generator = EmailGenerator(template_service, db)
    
    # 生成 5 封邮件
    emails = await generator.generate_emails(5)
    
    assert len(emails) == 5
    
    # 验证每封邮件都有必要字段
    for email in emails:
        assert email["id"] is not None
        assert "@" in email["from_address"]
        assert email["subject"] != ""
        assert email["body"] != ""
        assert email["region"] in ["Europe", "Asia", "South America", "Middle East"]


@pytest.mark.asyncio
async def test_database_persistence(db, setup_templates):
    """测试数据库持久化"""
    template_service = EmailTemplateService(db)
    generator = EmailGenerator(template_service, db)
    
    # 生成并保存到数据库
    email_data = await generator.generate_email()
    
    async with db.session() as session:
        # 创建客户
        customer = await db.get_or_create_customer(
            email=email_data["from_address"],
            defaults={"name": "Test Customer", "region": email_data["region"]}
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
        await session.commit()
    
    # 验证已保存
    async with db.session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Email).where(Email.id == email_data["id"]))
        saved_email = result.scalar_one_or_none()
        
        assert saved_email is not None
        assert saved_email.subject == email_data["subject"]


@pytest.mark.asyncio
async def test_batch_generation_performance(db, setup_templates):
    """测试批量生成性能"""
    import time
    
    template_service = EmailTemplateService(db)
    generator = EmailGenerator(template_service, db)
    
    start = time.time()
    emails = await generator.generate_emails(20)
    elapsed = time.time() - start
    
    assert len(emails) == 20
    assert elapsed < 5.0  # 20 封邮件应在 5 秒内生成
    
    # 验证所有 ID 唯一
    ids = [e["id"] for e in emails]
    assert len(ids) == len(set(ids))
```

- [ ] **Step 2: 运行 E2E 测试**

```bash
cd /data/resume/ai-product-dev-jd/.worktrees/ai-email-agent
pytest tests/generator/test_generator_e2e.py -v
```

- [ ] **Step 3: 提交**

```bash
git add tests/generator/test_generator_e2e.py
git commit -m "test: add E2E tests for email generator"
```

---

## Task 12: 文档更新

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新 README 使用示例**

在 README.md 中添加：

```markdown
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

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: update README with email generator usage"
```

---

## Summary Checklist

- [ ] Task 1: EmailTemplate 数据模型
- [ ] Task 2: Database 辅助方法
- [ ] Task 3: EmailTemplateService 服务
- [ ] Task 4: EmailGenerator 生成器
- [ ] Task 5: API Schemas 和端点
- [ ] Task 6: 模板种子脚本
- [ ] Task 7: 前端 TypeScript 类型定义
- [ ] Task 8: 前端 API 服务层
- [ ] Task 9: GenerateEmailPanel 组件
- [ ] Task 10: 集成到 Inbox 页面
- [ ] Task 11: E2E 测试
- [ ] Task 12: 文档更新

---

**Plan complete.** Two execution options:

**1. Subagent-Driven (recommended)** - Dispatch fresh subagent per task with review between tasks

**2. Inline Execution** - Execute tasks in this session using executing-plans

**Which approach?**
