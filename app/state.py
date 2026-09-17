from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class SupportState(TypedDict, total=False):
    # Request
    customer_id: str
    message: str

    # Intent classification
    intent: str
    intent_confidence: float

    # Agent tool-calling scratchpad
    messages: Annotated[list[AnyMessage], add_messages]

    # Enterprise data
    customer: dict
    transactions: list[dict]

    # Agent decision
    action: str
    reason: str
    requires_approval: bool

    # Deterministic routing outcome
    status: str

    # Error handling
    error: str | None
