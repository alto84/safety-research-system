"""Tasks API endpoints."""
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.auth import get_current_active_user, User

router = APIRouter()


class TaskResponse(BaseModel):
    """Response model for task."""
    task_id: str
    case_id: str
    title: str
    task_type: str
    status: str


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    case_id: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """List all tasks with optional filters."""
    # TODO: Implement task listing from database
    return []
