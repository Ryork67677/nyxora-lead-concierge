from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class Intent(StrEnum):
    BOOKING = "booking"
    PRICING = "pricing"
    SERVICES = "services"
    PREPARATION = "preparation"
    AFTERCARE = "aftercare"
    CANCELLATION = "cancellation"
    GENERAL = "general"
    SAFETY = "safety"


class RecommendedAction(StrEnum):
    ANSWER = "answer"
    BOOK_CONSULTATION = "book_consultation"
    HUMAN_HANDOFF = "human_handoff"
    EMERGENCY_HELP = "emergency_help"


class LeadContext(BaseModel):
    service_interest: str | None = Field(default=None, max_length=100)
    timeline: str | None = Field(default=None, max_length=80)
    contact_preference: str | None = Field(default=None, max_length=30)
    first_visit: bool | None = None


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    message: str = Field(min_length=1, max_length=1500)
    context: LeadContext = Field(default_factory=LeadContext)
    consent_to_store: bool = False

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("message cannot be blank")
        return normalized


class ChatResponse(BaseModel):
    response: str
    intent: Intent
    qualification_score: int = Field(ge=0, le=100)
    recommended_action: RecommendedAction
    requires_human: bool
    safety_flags: list[str] = Field(default_factory=list)
    knowledge_sources: list[str] = Field(default_factory=list)
    stored: bool = False


class HealthResponse(BaseModel):
    status: str
    version: str

