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

logger = get_logger(__name__)


class Database:
    """Database connection manager and session factory."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None

    @property
    def engine(self) -> AsyncEngine:
        """Lazy initialization of database engine."""
        if self._engine is None:
            self._engine = create_async_engine(
                self.settings.database_url,
                echo=self.settings.env == "development"
            )
            logger.info("database_initialized", url=self.settings.database_url)
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker:
        """Get session factory."""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session context manager."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("database_closed")

    async def query_customer(self, email: str = None, region: str = None) -> dict:
        """Query customer history by email or region."""
        return {"name": "Test Customer", "tier": "B", "region": region}

    async def query_pricing(self, products: list, region: str) -> dict:
        """Query pricing policy for products and region."""
        return {"base_price": 2.0, "discount": 0.1, "region": region}

    async def query_compliance(self, products: list, destination: str) -> dict:
        """Query compliance requirements for products and destination."""
        compliance_map = {
            "brazil": ["ANVISA"],
            "eu": ["CE", "GMP"],
            "us": ["FDA"]
        }
        return {"required": compliance_map.get(destination, [])}


_db_instance: Optional[Database] = None


def get_database(settings: Settings) -> Database:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(settings)
    return _db_instance
