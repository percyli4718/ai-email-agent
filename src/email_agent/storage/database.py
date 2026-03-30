"""
数据库模块

模块作用:
    本模块封装数据库连接管理和会话工厂。
    使用 SQLAlchemy 异步引擎提供数据库访问功能，
    支持上下文管理器的会话管理方式。

使用场景:
    - 应用启动时初始化数据库连接
    - 在各业务模块中获取数据库会话
    - 查询客户信息、定价政策、合规要求等

在项目中的位置:
    位于 src/email_agent/storage/database.py，
    是应用存储层的核心组件，
    被 retriever.py 等模块调用进行数据查询。
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)

from email_agent.config import Settings
from email_agent.logging_config import get_logger

# 获取当前模块的日志记录器
logger = get_logger(__name__)


class Database:
    """
    数据库连接管理器

    作用:
        管理数据库引擎和会话工厂。
        使用懒加载初始化，避免应用启动时不必要的连接。

    使用场景:
        - 应用启动时创建实例
        - 通过上下文管理器获取会话
        - 应用关闭时清理连接

    主要方法:
        session: 获取数据库会话 (上下文管理器)
        close: 关闭数据库连接
        query_customer: 查询客户信息
        query_pricing: 查询定价政策
        query_compliance: 查询合规要求

    属性:
        settings: Settings 类型，应用配置
        _engine: Optional[AsyncEngine] 类型，数据库引擎 (懒加载)
        _session_factory: Optional[async_sessionmaker] 类型，会话工厂

    懒加载说明:
        engine 和 session_factory 都在首次访问时创建，
        避免应用启动时立即建立数据库连接
    """

    def __init__(self, settings: Settings):
        """
        初始化数据库

        参数:
            settings: Settings 类型，应用配置对象

        返回值:
            无

        异常:
            无
        """
        self.settings = settings
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None

    @property
    def engine(self) -> AsyncEngine:
        """
        数据库引擎属性 (懒加载)

        功能描述:
            按需创建异步数据库引擎。
            开发环境下启用 SQL 日志输出。

        参数:
            无

        返回值:
            AsyncEngine: SQLAlchemy 异步引擎实例

        异常:
            无

        配置说明:
            - echo=True (开发环境): 输出 SQL 日志
            - echo=False (生产环境): 禁用 SQL 日志
        """
        if self._engine is None:
            # 首次访问时创建引擎
            self._engine = create_async_engine(
                # 数据库连接 URL，如：sqlite+aiosqlite:///./data/email_agent.db
                self.settings.database_url,
                # 开发环境下启用 SQL 日志
                echo=self.settings.env == "development"
            )
            logger.info("database_initialized", url=self.settings.database_url)
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker:
        """
        会话工厂属性

        功能描述:
            创建或获取会话工厂。
            用于生成数据库会话。

        参数:
            无

        返回值:
            async_sessionmaker: SQLAlchemy 异步会话工厂

        异常:
            无

        配置说明:
            - class_=AsyncSession: 使用异步会话类
            - expire_on_commit=False: 提交后不过期对象属性
        """
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                # 绑定数据库引擎
                self.engine,
                # 使用异步会话类
                class_=AsyncSession,
                # 提交后不过期对象属性，便于后续访问
                expire_on_commit=False
            )
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话 (上下文管理器)

        功能描述:
            使用上下文管理器自动管理会话生命周期。
            成功时自动提交，异常时自动回滚。

        参数:
            无

        返回值:
            AsyncSession: SQLAlchemy 异步会话

        异常:
            Exception: 任何异常都会触发回滚

        使用示例:
            async with db.session() as session:
                # 执行数据库操作
                session.add(model)
            # 自动提交
        """
        # 创建新会话
        async with self.session_factory() as session:
            try:
                # yield 会话给调用者使用
                yield session
                # 成功则提交
                await session.commit()
            except Exception:
                # 异常则回滚
                await session.rollback()
                # 重新抛出异常
                raise

    async def close(self) -> None:
        """
        关闭数据库连接

        功能描述:
            释放数据库引擎占用的资源。
            在应用关闭时调用。

        参数:
            无

        返回值:
            无

        异常:
            无
        """
        if self._engine:
            # 释放引擎资源
            await self._engine.dispose()
            logger.info("database_closed")

    async def query_customer(self, email: str = None, region: str = None) -> dict:
        """
        查询客户历史记录

        功能描述:
            根据邮箱或区域查询客户信息。
            当前返回模拟数据，后续将对接真实数据库。

        参数:
            email: Optional[str] 类型，客户邮箱 (可选)
            region: Optional[str] 类型，客户区域 (可选)

        返回值:
            dict: 客户信息字典
                - name: 客户名称
                - tier: 客户等级 (A/B/C)
                - region: 所在区域

        异常:
            无

        TODO:
            实现真实的数据库查询逻辑
        """
        # 返回模拟数据
        return {"name": "Test Customer", "tier": "B", "region": region}

    async def query_pricing(self, products: list, region: str) -> dict:
        """
        查询产品定价政策

        功能描述:
            根据产品列表和区域查询适用定价。
            当前返回模拟数据，后续将对接真实数据库。

        参数:
            products: list 类型，产品名称列表
            region: str 类型，客户区域

        返回值:
            dict: 定价政策字典
                - base_price: 基础价格
                - discount: 折扣率
                - region: 适用区域

        异常:
            无

        TODO:
            实现真实的数据库查询逻辑
        """
        # 返回模拟数据
        return {"base_price": 2.0, "discount": 0.1, "region": region}

    async def query_compliance(self, products: list, destination: str) -> dict:
        """
        查询合规要求

        功能描述:
            根据产品和目的地查询合规要求。
            不同国家/地区有不同的认证要求。

        参数:
            products: list 类型，产品名称列表
            destination: str 类型，目的地国家/区域

        返回值:
            dict: 合规要求字典
                - required: 必需认证列表

        异常:
            无

        合规示例:
            - brazil: ANVISA 认证
            - eu: CE 认证，GMP 合规
            - us: FDA 认证

        TODO:
            实现真实的数据库查询逻辑
        """
        # 定义区域到认证要求的映射
        compliance_map = {
            "brazil": ["ANVISA"],
            "eu": ["CE", "GMP"],
            "us": ["FDA"]
        }
        # 返回对应区域的合规要求，如果没有则返回空列表
        return {"required": compliance_map.get(destination, [])}


# 全局数据库实例 (延迟初始化)
_db_instance: Optional[Database] = None


def get_database(settings: Settings) -> Database:
    """
    获取或创建数据库实例

    功能描述:
        使用全局变量模式确保单例访问。
        首次调用时创建实例，后续调用复用。

    参数:
        settings: Settings 类型，应用配置对象

    返回值:
        Database: 数据库实例

    异常:
        无

    使用示例:
        db = get_database(settings)
        async with db.session() as session:
            # 执行数据库操作
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(settings)
    return _db_instance
