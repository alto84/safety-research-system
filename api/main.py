"""Main FastAPI application."""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from api.auth import get_current_active_user, User
from api.routers import cases, tasks, audit_results, health

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Safety Research System API")
    yield
    logger.info("Shutting down Safety Research System API")


# Create FastAPI application
app = FastAPI(
    title="Safety Research System API",
    description="API for pharmaceutical safety research with AI-powered evidence synthesis",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(cases.router, prefix="/api/v1", tags=["Cases"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
app.include_router(audit_results.router, prefix="/api/v1", tags=["Audit Results"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Safety Research System API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/api/v1/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user
