import pytest
from langchain_core.messages import AIMessage

from app import graph, tools
from app.schemas import IntentResult, ResolutionDecision


class _ScriptedLLM:
    """Stands in for the real tool-calling ChatOpenAI in tests."""

    def __init__(self, responses):
        self._responses = list(responses)

    def invoke(self, messages):
        return self._responses.pop(0)


def _tool_call_message(customer_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "lookup_customer",
                "args": {"customer_id": customer_id},
                "id": "call_customer",
            },
            {
                "name": "lookup_transactions",
                "args": {"customer_id": customer_id},
                "id": "call_transactions",
            },
        ],
    )


_FINAL_AGENT_MESSAGE = AIMessage(content="Gathered the data I need.")


@pytest.fixture(autouse=True)
def _patch_db(monkeypatch, seeded_sessionmaker):
    monkeypatch.setattr(tools, "SessionLocal", seeded_sessionmaker)


@pytest.fixture(autouse=True)
def _patch_intent(monkeypatch):
    monkeypatch.setattr(
        graph,
        "classify_intent",
        lambda message: IntentResult(intent="billing_issue", confidence=0.9),
    )


def test_missing_customer_routes_to_error_without_reasoning(monkeypatch):
    monkeypatch.setattr(
        graph,
        "agent_llm",
        _ScriptedLLM([_tool_call_message("UNKNOWN"), _FINAL_AGENT_MESSAGE]),
    )

    def _fail_if_called(**kwargs):
        pytest.fail("determine_resolution should not run for a missing customer")

    monkeypatch.setattr(graph, "determine_resolution", _fail_if_called)

    result = graph.support_graph.invoke(
        {"customer_id": "UNKNOWN", "message": "I was charged twice"}
    )

    assert result["error"] == "Customer not found"
    assert result["status"] == "customer_not_found"
    assert "action" not in result


def test_normal_resolution_finalizes(monkeypatch):
    monkeypatch.setattr(
        graph,
        "agent_llm",
        _ScriptedLLM([_tool_call_message("C1001"), _FINAL_AGENT_MESSAGE]),
    )
    monkeypatch.setattr(
        graph,
        "determine_resolution",
        lambda **kwargs: ResolutionDecision(
            action="no_action",
            reason="No billing issue found.",
            requires_approval=False,
        ),
    )

    result = graph.support_graph.invoke(
        {"customer_id": "C1001", "message": "Question about my account"}
    )

    assert result["status"] == "resolved"
    assert result["action"] == "no_action"
    assert result["requires_approval"] is False
    assert result["customer"]["id"] == "C1001"
    assert len(result["transactions"]) == 2


def test_approval_required_routes_to_await_approval(monkeypatch):
    monkeypatch.setattr(
        graph,
        "agent_llm",
        _ScriptedLLM([_tool_call_message("C1001"), _FINAL_AGENT_MESSAGE]),
    )
    monkeypatch.setattr(
        graph,
        "determine_resolution",
        lambda **kwargs: ResolutionDecision(
            action="refund",
            reason="Two duplicate completed charges were found.",
            requires_approval=True,
        ),
    )

    result = graph.support_graph.invoke(
        {"customer_id": "C1001", "message": "I was charged twice"}
    )

    assert result["status"] == "awaiting_approval"
    assert result["action"] == "refund"
    assert result["requires_approval"] is True
