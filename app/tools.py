from langchain_core.tools import tool

from app.database import SessionLocal
from app.repositories import (
    get_customer_by_customer_id,
    get_transactions_by_customer_id,
)


@tool
def lookup_customer(customer_id: str) -> dict:
    """Look up an enterprise customer's account info by customer_id.

    Returns a dict with "found": False if no such customer exists, otherwise
    "found": True plus the customer's id, name, email, and status.
    """
    db = SessionLocal()

    try:
        customer = get_customer_by_customer_id(
            db=db,
            customer_id=customer_id,
        )

        if not customer:
            return {"found": False}

        return {
            "found": True,
            "id": customer.customer_id,
            "name": customer.name,
            "email": customer.email,
            "status": customer.status,
        }

    finally:
        db.close()


@tool
def lookup_transactions(customer_id: str) -> list[dict]:
    """List an enterprise customer's transaction history by customer_id.

    Returns an empty list if the customer has no transactions (or does not exist).
    """
    db = SessionLocal()

    try:
        transactions = get_transactions_by_customer_id(
            db=db,
            customer_id=customer_id,
        )

        return [
            {
                "id": transaction.transaction_id,
                "amount": float(transaction.amount),
                "type": transaction.transaction_type,
                "status": transaction.status,
                "created_at": transaction.created_at.isoformat(),
            }
            for transaction in transactions
        ]

    finally:
        db.close()


SUPPORT_TOOLS = [lookup_customer, lookup_transactions]
