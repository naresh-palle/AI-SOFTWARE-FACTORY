"""
Main FastAPI Application Entrypoint.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from factory.api.routes import router
from factory.core.config import settings
from factory.core.database import get_db_session, init_db
from factory.agents.registry import AgentRegistry
from factory.core.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database tables and sync 97 agent definitions
    logger.info("Initializing Factory Database and Agent Catalog...")
    await init_db()
    async with get_db_session() as session:
        await AgentRegistry.sync_with_db(session)
    logger.info("Factory Backend Startup Complete.")
    yield
    # Shutdown
    logger.info("Factory Backend Shutting Down.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Autonomous AI Software Development Factory - Core Master Orchestrator API",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("factory.api.main:app", host="0.0.0.0", port=8000, reload=True)
