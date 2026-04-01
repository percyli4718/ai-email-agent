"""
EmailTemplateService - 邮件模板服务

模块作用:
    本模块提供邮件模板的数据库操作服务。
    支持查询、随机选择和管理邮件模板。

使用场景:
    - 邮件生成器随机选择模板生成测试邮件
    - 管理后台查询和停用模板
    - 根据类型和区域过滤模板

在项目中的位置:
    位于 src/email_agent/generator/template_service.py，
    是邮件生成器的核心服务组件，
    依赖 storage 模块的 Database 和 EmailTemplate 模型。
"""
import random
from typing import Optional, List
from sqlalchemy import select

from email_agent.storage.database import Database
from email_agent.storage.models import EmailTemplate


class EmailTemplateService:
    """
    邮件模板服务类

    作用:
        提供邮件模板的 CRUD 操作。
        封装数据库查询逻辑，供邮件生成器使用。

    使用场景:
        - 获取所有可用模板
        - 随机选择模板生成测试邮件
        - 根据 ID 查询模板
        - 停用模板

    主要方法:
        get_active_templates: 获取所有启用的模板
        get_random_template: 随机获取一个模板（可选类型和区域过滤）
        get_template_by_id: 根据 ID 获取模板
        deactivate_template: 停用模板
    """

    def __init__(self, db: Database):
        """
        初始化模板服务

        参数:
            db: Database 类型，数据库实例
        """
        self.db = db

    async def get_active_templates(self) -> List[EmailTemplate]:
        """
        获取所有启用的模板

        功能描述:
            查询数据库中所有 is_active=True 的模板。

        参数:
            无

        返回值:
            List[EmailTemplate]: 启用的模板列表

        异常:
            SQLAlchemy 异常
        """
        async with self.db.session() as session:
            stmt = select(EmailTemplate).where(EmailTemplate.is_active == True)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_templates(self) -> List[EmailTemplate]:
        """
        获取所有模板（包括已停用的）

        功能描述:
            查询数据库中所有模板，不分是否启用。
            用于管理后台展示完整模板列表。

        参数:
            无

        返回值:
            List[EmailTemplate]: 所有模板列表

        异常:
            SQLAlchemy 异常
        """
        async with self.db.session() as session:
            stmt = select(EmailTemplate).order_by(EmailTemplate.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_random_template(
        self,
        template_type: Optional[str] = None,
        region: Optional[str] = None
    ) -> Optional[EmailTemplate]:
        """
        随机获取一个模板

        功能描述:
            从数据库中随机选择一个模板。
            支持按类型和区域过滤。

        参数:
            template_type: Optional[str] 类型，模板类型（可选）
                inquiry/rfq/complaint/status_check
            region: Optional[str] 类型，区域（可选）
                Europe/Asia/South America/Middle East

        返回值:
            Optional[EmailTemplate]: 随机选择的模板，如果没有匹配则返回 None

        异常:
            SQLAlchemy 异常
        """
        async with self.db.session() as session:
            stmt = select(EmailTemplate).where(EmailTemplate.is_active == True)

            if template_type:
                stmt = stmt.where(EmailTemplate.type == template_type)

            if region:
                stmt = stmt.where(EmailTemplate.region == region)

            result = await session.execute(stmt)
            templates = list(result.scalars().all())

            if not templates:
                return None

            return random.choice(templates)

    async def get_template_by_id(self, template_id: int) -> Optional[EmailTemplate]:
        """
        根据 ID 获取模板

        功能描述:
            根据模板 ID 查询模板详情。

        参数:
            template_id: int 类型，模板 ID

        返回值:
            Optional[EmailTemplate]: 模板对象，如果不存在则返回 None

        异常:
            SQLAlchemy 异常
        """
        async with self.db.session() as session:
            stmt = select(EmailTemplate).where(EmailTemplate.id == template_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def deactivate_template(self, template_id: int) -> bool:
        """
        停用模板

        功能描述:
            将模板的 is_active 字段设置为 False。

        参数:
            template_id: int 类型，模板 ID

        返回值:
            bool: 是否成功停用（如果模板不存在返回 False）

        异常:
            SQLAlchemy 异常
        """
        async with self.db.session() as session:
            stmt = select(EmailTemplate).where(EmailTemplate.id == template_id)
            result = await session.execute(stmt)
            template = result.scalars().first()

            if template:
                template.is_active = False
                await session.commit()
                return True

            return False
