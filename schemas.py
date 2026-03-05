"""
Travel Research Agency — API Schemas
Pydantic models for FastAPI request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional


class TripRequest(BaseModel):
    """User's trip planning request."""
    query: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        examples=["Plan a 7-day trip to Tokyo"],
    )
    destination: Optional[str] = None
    budget: Optional[float] = Field(None, gt=0, le=100000)
    num_travelers: int = Field(default=1, ge=1, le=20)
    thread_id: Optional[str] = None  # for continuing conversations


class TripResponse(BaseModel):
    """Agent's response."""
    thread_id: str
    status: str  # "complete" | "awaiting_approval" | "cancelled"
    itinerary: Optional[str] = None
    estimated_total: Optional[float] = None
    message_count: int = 0


class ResumeRequest(BaseModel):
    """Resume from HITL interrupt."""
    thread_id: str
    decision: str = Field(
        ...,
        pattern="^(approve|approve_anyway|reject|find_cheaper|request_changes|cancel)$",
    )


class StatusResponse(BaseModel):
    """Trip planning status check."""
    thread_id: str
    status: str
    estimated_total: Optional[float] = None
    awaiting_approval: bool = False
    message_count: int = 0


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
