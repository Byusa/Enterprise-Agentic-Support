from dotenv import load_dotenv

from app.llm import get_chat_model
from app.schemas import ResolutionDecision

load_dotenv()

REASONING_SYSTEM_PROMPT = """
You are a support resolution component in an enterprise customer support system.

Your job is to recommend the next action based only on the provided:
- customer message
- classified intent
- customer data
- transaction data

Rules:
- Do not invent customer or transaction data.
- If duplicate completed charges clearly exist, a refund may be recommended.
- If there is not enough evidence to make a decision, request more information.
- If the situation cannot be safely handled automatically, escalate.
- A refund over $100 must require human approval.
- Return only the structured result required by the schema.
"""

llm = get_chat_model()

reasoning_llm = llm.with_structured_output(ResolutionDecision)


def determine_resolution(
    message: str,
    intent: str,
    customer: dict | None,
    transactions: list[dict],
) -> ResolutionDecision:
    context = f"""
Customer message:
{message}

Intent:
{intent}

Customer:
{customer}

Transactions:
{transactions}
"""

    return reasoning_llm.invoke(
        [
            ("system", REASONING_SYSTEM_PROMPT),
            ("human", context),
        ]
    )