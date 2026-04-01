"""
EmailGenerator - 邮件生成器

模块作用:
    本模块提供邮件内容生成功能。
    基于模板随机生成测试邮件，支持批量生成。

使用场景:
    - 生成测试邮件用于系统测试
    - 批量生成模拟邮件数据
    - 根据区域和产品生成定制化邮件

在项目中的位置:
    位于 src/email_agent/generator/email_generator.py，
    依赖 EmailTemplateService 获取模板，
    使用 Database 存储生成的邮件。
"""
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from email_agent.generator.template_service import EmailTemplateService
from email_agent.storage.database import Database
from email_agent.storage.models import EmailTemplate


class EmailGenerator:
    """
    邮件生成器类

    作用:
        基于模板生成测试邮件。
        支持单个生成和批量生成模式。

    使用场景:
        - generate_email: 生成单封测试邮件
        - generate_emails: 批量生成多封测试邮件

    主要方法:
        generate_email: 生成单封邮件
        generate_emails: 批量生成邮件

    类属性:
        CUSTOMER_NAMES: 按区域划分的客户名称字典
        PACKING_OPTIONS: 包装选项列表
        STANDARDS: 标准认证列表
    """

    # 按区域划分的客户名称
    CUSTOMER_NAMES: Dict[str, List[Dict[str, str]]] = {
        "Europe": [
            {"name": "PharmaCom UK Ltd", "email": "orders@pharmacom-uk.com"},
            {"name": "EuroMed Supplies", "email": "procurement@euromed.de"},
            {"name": "HealthCare Partners", "email": "supply@hcp-france.fr"},
            {"name": "Nordic Pharma AB", "email": "orders@nordicpharma.se"},
        ],
        "South America": [
            {"name": "Brasil Medicamentos", "email": "compras@brasilmeds.com.br"},
            {"name": "Argentina Health", "email": "ventas@arghealth.com.ar"},
            {"name": "Chile Farma", "email": "compras@chilefarma.cl"},
            {"name": "Colombia Medical", "email": "pedidos@colombiamed.co"},
        ],
        "Asia": [
            {"name": "Singapore Pharma Pte Ltd", "email": "procurement@sgpharma.sg"},
            {"name": "India Medicines Pvt Ltd", "email": "orders@indiameds.in"},
            {"name": "Thailand Health Products", "email": "supply@thaihealth.co.th"},
            {"name": "Vietnam Medical JSC", "email": "purchasing@vietmed.vn"},
        ],
        "Middle East": [
            {"name": "Dubai Pharma Trading", "email": "orders@dubaipharma.ae"},
            {"name": "Saudi Health Supplies", "email": "procurement@saudihealth.sa"},
            {"name": "Qatar Medical Co", "email": "supply@qatarmed.qa"},
            {"name": "Israel Pharma Ltd", "email": "orders@israpharma.co.il"},
        ],
    }

    # 包装选项
    PACKING_OPTIONS: List[str] = [
        "Standard export carton",
        "Blister pack + carton",
        "Bulk drum packaging",
        "Bottle + master carton",
        "Alu-Alu blister pack",
    ]

    # 标准认证
    STANDARDS: List[str] = [
        "GMP certified",
        "ISO 9001:2015",
        "FDA approved facility",
        "CE marked",
        "WHO-GMP compliant",
    ]

    def __init__(self, template_service: EmailTemplateService, db: Database):
        """
        初始化邮件生成器

        参数:
            template_service: EmailTemplateService 类型，邮件模板服务
            db: Database 类型，数据库实例
        """
        self.template_service = template_service
        self.db = db

    def _generate_customer_name(self, region: str) -> Dict[str, str]:
        """
        为指定区域生成随机客户信息

        功能描述:
            从预定义的客户名称列表中随机选择一个客户。

        参数:
            region: str 类型，区域名称 (Europe/South America/Asia/Middle East)

        返回值:
            Dict[str, str]: 包含 name 和 email 的客户信息字典

        异常:
            如果区域无预定义客户，返回默认客户
        """
        if region in self.CUSTOMER_NAMES and self.CUSTOMER_NAMES[region]:
            return random.choice(self.CUSTOMER_NAMES[region])

        # 默认客户
        return {
            "name": "Global Trading Co",
            "email": "orders@globaltrading.com"
        }

    def _generate_quantity(self, quantity_range: str) -> int:
        """
        根据数量范围生成随机数量

        功能描述:
            解析数量范围字符串 (如 "100-500") 并生成范围内的随机整数。

        参数:
            quantity_range: str 类型，数量范围字符串 (格式："min-max")

        返回值:
            int: 范围内的随机整数

        异常:
            如果格式无效，返回 100
        """
        try:
            parts = quantity_range.split("-")
            if len(parts) == 2:
                min_qty = int(parts[0].strip())
                max_qty = int(parts[1].strip())
                return random.randint(min_qty, max_qty)
        except (ValueError, IndexError):
            pass

        # 默认返回 100
        return 100

    def _generate_email_id(self) -> str:
        """
        生成唯一的邮件 ID

        功能描述:
            生成格式为 email_YYYYMMDDHHMMSS_XXXX 的唯一 ID。
            其中 XXXX 是 4 位随机数。

        返回值:
            str: 唯一的邮件 ID

        示例:
            email_20260401143022_5847
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = random.randint(1000, 9999)
        return f"email_{timestamp}_{random_suffix}"

    def _determine_priority(self, quantity: int) -> str:
        """
        根据数量确定邮件优先级

        功能描述:
            数量 > 1000 为 high，否则为 medium。

        参数:
            quantity: int 类型，订单数量

        返回值:
            str: "high" 或 "medium"
        """
        return "high" if quantity > 1000 else "medium"

    async def generate_email(self) -> Dict[str, Any]:
        """
        生成单封邮件

        功能描述:
            随机选择一个模板，生成包含所有字段的邮件数据。
            包括客户信息、产品、数量、优先级等。

        参数:
            无

        返回值:
            Dict[str, Any]: 邮件数据字典，包含:
                - email_id: str, 邮件 ID
                - from_name: str, 发件人名称
                - from_email: str, 发件人邮箱
                - region: str, 区域
                - product_name: str, 产品名称
                - quantity: int, 数量
                - packing: str, 包装方式
                - standard: str, 标准认证
                - subject: str, 邮件主题
                - body: str, 邮件正文
                - priority: str, 优先级 (high/medium)

        异常:
            ValueError: 如果没有可用模板
        """
        # 随机选择模板
        template = await self.template_service.get_random_template()

        if not template:
            raise ValueError("No email templates available")

        # 生成客户信息
        customer = self._generate_customer_name(template.region)

        # 生成数量
        quantity = self._generate_quantity(template.quantity_range)

        # 生成邮件 ID
        email_id = self._generate_email_id()

        # 生成包装和标准
        packing = random.choice(self.PACKING_OPTIONS)
        standard = random.choice(self.STANDARDS)

        # 生成辅助数据
        batch_number = f"BATCH{random.randint(100000, 999999)}"
        order_number = f"ORD{random.randint(100000, 999999)}"
        destination = template.region  # 默认目的地为区域

        # 生成主题和正文
        subject = template.subject_template.format(
            product=template.product_name,
            quantity=quantity,
            packing=packing,
            standard=standard,
            customer_name=customer["name"],
            email=customer["email"],
            region=template.region,
            destination=destination,
            batch_number=batch_number,
            order_number=order_number,
        )
        body = template.body_template.format(
            product=template.product_name,
            quantity=quantity,
            packing=packing,
            standard=standard,
            customer_name=customer["name"],
            email=customer["email"],
            region=template.region,
            destination=destination,
            batch_number=batch_number,
            order_number=order_number,
        )

        # 确定优先级
        priority = self._determine_priority(quantity)

        return {
            "email_id": email_id,
            "from_name": customer["name"],
            "from_email": customer["email"],
            "region": template.region,
            "product_name": template.product_name,
            "quantity": quantity,
            "packing": packing,
            "standard": standard,
            "subject": subject,
            "body": body,
            "priority": priority,
            "template_type": template.type,
        }

    async def generate_emails(self, count: int) -> List[Dict[str, Any]]:
        """
        批量生成多封邮件

        功能描述:
            生成指定数量的邮件。
            每封邮件独立生成，可能使用不同的模板。

        参数:
            count: int 类型，要生成的邮件数量

        返回值:
            List[Dict[str, Any]]: 邮件数据列表

        异常:
            ValueError: 如果没有可用模板
            ValueError: 如果 count <= 0
        """
        if count <= 0:
            raise ValueError("Count must be a positive integer")

        emails = []
        for _ in range(count):
            email = await self.generate_email()
            emails.append(email)

        return emails
