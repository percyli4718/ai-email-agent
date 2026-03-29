from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from email_agent.config import settings, get_settings
from email_agent.logging_config import setup_logging, get_logger
from email_agent.storage.database import get_database
from email_agent.api.routes import router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    setup_logging(settings.log_level)
    logger.info("application_starting", env=settings.env)

    db = get_database(settings)

    yield

    await db.close()
    logger.info("application_shutdown")


app = FastAPI(
    title="AI Email Agent",
    description="AI-powered email processing for pharmaceutical distribution",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI Email Agent",
        "version": "0.1.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "email_agent.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.env == "development"
    )
