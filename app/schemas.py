from typing import Literal

from pydantic import BaseModel, Field


class SupportRequest(BaseModel):
    customer_id: str
    message: str = Field(min_length=1)


class IntentResult(BaseModel):
    intent: Literal[
        "billing_issue",
        "refund_request",
        "technical_issue",
        "account_issue",
        "unknown",
    ]

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class ResolutionDecision(BaseModel):
    action: Literal[
        "refund",
        "request_more_information",
        "escalate",
        "no_action",
    ]

    reason: str
    requires_approval: bool


class SupportResponse(BaseModel):
    intent: str
    confidence: float
    action: str
    reason: str
    requires_approval: bool