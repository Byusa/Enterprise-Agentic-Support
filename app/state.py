from typing import TypedDict


class SupportState(TypedDict, total=False):
    # Request
    customer_id: str
    message: str

    # Intent classification
    intent: str
    intent_confidence: float

    # Enterprise data
    customer: dict
    transactions: list[dict]

    # Agent decision
    action: str
    reason: str
    requires_approval: bool

    # Error handling
    error: str | None