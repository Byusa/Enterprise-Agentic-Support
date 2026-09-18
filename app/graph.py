import json

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.intent import classify_intent
from app.llm import get_chat_model
from app.reasoning import determine_resolution
from app.state import SupportState
from app.tools import SUPPORT_TOOLS

AGENT_SYSTEM_PROMPT = """
You are a data-gathering assistant in an enterprise customer support workflow.

You have tools to look up a customer's account info and their transaction
history. Before you can help resolve the customer's request, call
`lookup_customer` and `lookup_transactions` for the given customer_id to
gather the facts you need.

Do not fabricate customer or transaction data - only rely on what the tools
return. Once you have called the tools you need, reply with a brief
confirmation and stop.
"""

agent_llm = get_chat_model().bind_tools(SUPPORT_TOOLS)


def classify_intent_node(state: SupportState) -> dict:
    result = classify_intent(state["message"])

    return {
        "intent": result.intent,
        "intent_confidence": result.confidence,
    }


def agent_node(state: SupportState) -> dict:
    existing_messages = state.get("messages", [])

    if not existing_messages:
        existing_messages = [
            SystemMessage(content=AGENT_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Customer ID: {state['customer_id']}\n"
                    f"Customer message: {state['message']}\n"
                    f"Classified intent: {state.get('intent', 'unknown')}\n\n"
                    "Use the available tools to look up this customer's "
                    "account and transaction history."
                )
            ),
        ]

    ai_message = agent_llm.invoke(existing_messages)

    if state.get("messages"):
        return {"messages": [ai_message]}

    return {"messages": existing_messages + [ai_message]}


def _parse_tool_message_content(content):
    # ToolNode returns a JSON string for non-empty dict/list tool results,
    # but an empty list is passed through as-is (it already satisfies the
    # "list of content blocks" check trivially), so accept both shapes.
    if isinstance(content, str):
        return json.loads(content)
    return content


def extract_data_node(state: SupportState) -> dict:
    customer = None
    transactions: list[dict] = []

    for message in state.get("messages", []):
        if not isinstance(message, ToolMessage):
            continue

        if message.name == "lookup_customer":
            payload = _parse_tool_message_content(message.content)
            if payload.get("found"):
                customer = {
                    key: value
                    for key, value in payload.items()
                    if key != "found"
                }

        elif message.name == "lookup_transactions":
            transactions = _parse_tool_message_content(message.content)

    if customer is None:
        return {"error": "Customer not found"}

    return {"customer": customer, "transactions": transactions}


def handle_missing_customer_node(state: SupportState) -> dict:
    return {"status": "customer_not_found"}


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


def await_approval_node(state: SupportState) -> dict:
    return {"status": "awaiting_approval"}


def finalize_node(state: SupportState) -> dict:
    return {"status": "resolved"}


def route_after_extract(state: SupportState) -> str:
    return "handle_missing_customer" if state.get("error") else "reason"


def route_after_reason(state: SupportState) -> str:
    return "await_approval" if state.get("requires_approval") else "finalize"


builder = StateGraph(SupportState)

builder.add_node("classify_intent", classify_intent_node)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(SUPPORT_TOOLS))
builder.add_node("extract_data", extract_data_node)
builder.add_node("handle_missing_customer", handle_missing_customer_node)
builder.add_node("reason", reason_node)
builder.add_node("await_approval", await_approval_node)
builder.add_node("finalize", finalize_node)

builder.add_edge(START, "classify_intent")
builder.add_edge("classify_intent", "agent")

builder.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "tools", "__end__": "extract_data"},
)
builder.add_edge("tools", "agent")

builder.add_conditional_edges(
    "extract_data",
    route_after_extract,
    {
        "handle_missing_customer": "handle_missing_customer",
        "reason": "reason",
    },
)
builder.add_edge("handle_missing_customer", END)

builder.add_conditional_edges(
    "reason",
    route_after_reason,
    {
        "await_approval": "await_approval",
        "finalize": "finalize",
    },
)
builder.add_edge("await_approval", END)
builder.add_edge("finalize", END)


support_graph = builder.compile()
