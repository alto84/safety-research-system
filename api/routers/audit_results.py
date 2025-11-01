"""Audit results API endpoints."""
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.auth import get_current_active_user, User

router = APIRouter()


class AuditResultResponse(BaseModel):
    """Response model for audit result."""
    audit_id: str
    task_id: str
    status: str
    score: float = None


@router.get("/audit-results", response_model=List[AuditResultResponse])
async def list_audit_results(
    task_id: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """List all audit results with optional filters."""
    # TODO: Implement audit results listing from database
    return []
