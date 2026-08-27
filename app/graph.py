from langgraph.graph import StateGraph, START, END

from app.database import SessionLocal
from app.intent import classify_intent
from app.reasoning import determine_resolution
from app.state import SupportState
from app.tools import get_customer, get_transactions


def classify_intent_node(state: SupportState) -> dict:
    result = classify_intent(state["message"])

    return {
        "intent": result.intent,
        "intent_confidence": result.confidence,
    }


def load_customer_node(state: SupportState) -> dict:
    db = SessionLocal()

    try:
        customer = get_customer(
            db=db,
            customer_id=state["customer_id"],
        )

        if customer is None:
            return {
                "error": "Customer not found",
            }

        return {
            "customer": customer,
        }

    finally:
        db.close()


def load_transactions_node(state: SupportState) -> dict:
    db = SessionLocal()

    try:
        transactions = get_transactions(
            db=db,
            customer_id=state["customer_id"],
        )

        return {
            "transactions": transactions,
        }

    finally:
        db.close()


def reason_node(state: SupportState) -> dict:
    result = determine_resolution(
        message=state["message"],
        intent=state["intent"],
        customer=state.get("customer"),
        transactions=state.get("transactions", []),
    )

    return {
        "action": result.action,
        "reason": result.reason,
        "requires_approval": result.requires_approval,
    }


builder = StateGraph(SupportState)


builder.add_node(
    "classify_intent",
    classify_intent_node,
)

builder.add_node(
    "load_customer",
    load_customer_node,
)

builder.add_node(
    "load_transactions",
    load_transactions_node,
)

builder.add_node(
    "reason",
    reason_node,
)


builder.add_edge(
    START,
    "classify_intent",
)

builder.add_edge(
    "classify_intent",
    "load_customer",
)

builder.add_edge(
    "load_customer",
    "load_transactions",
)

builder.add_edge(
    "load_transactions",
    "reason",
)

builder.add_edge(
    "reason",
    END,
)


support_graph = builder.compile()