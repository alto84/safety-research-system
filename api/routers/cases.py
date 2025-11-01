"""Cases API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.auth import get_current_active_user, User

router = APIRouter()


class CaseCreate(BaseModel):
    """Request model for creating a case."""
    title: str
    description: str
    question: str
    priority: str = "medium"
    submitter: str


class CaseResponse(BaseModel):
    """Response model for case."""
    case_id: str
    title: str
    description: str
    question: str
    status: str
    priority: str
    submitter: str
    created_at: str


@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case: CaseCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new safety research case."""
    # TODO: Implement case creation with database
    return {
        "case_id": "case-123",
        "title": case.title,
        "description": case.description,
        "question": case.question,
        "status": "submitted",
        "priority": case.priority,
        "submitter": case.submitter,
        "created_at": "2025-11-01T00:00:00Z"
    }


@router.get("/cases", response_model=List[CaseResponse])
async def list_cases(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """List all cases with optional filters."""
    # TODO: Implement case listing from database
    return []


@router.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific case by ID."""
    # TODO: Implement case retrieval from database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Case {case_id} not found"
    )
