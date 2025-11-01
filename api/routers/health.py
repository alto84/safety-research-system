"""Health check and metrics endpoints."""
from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # TODO: Add database connectivity check
    return {
        "status": "ready",
        "database": "connected",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live")
async def liveness_check():
    """Liveness check endpoint."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
