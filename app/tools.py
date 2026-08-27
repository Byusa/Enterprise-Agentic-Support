from sqlalchemy.orm import Session

from app.repositories import (
    get_customer_by_customer_id,
    get_transactions_by_customer_id,
)


def get_customer(db: Session, customer_id: str) -> dict | None:
    customer = get_customer_by_customer_id(
        db=db,
        customer_id=customer_id,
    )

    if not customer:
        return None

    return {
        "id": customer.customer_id,
        "name": customer.name,
        "email": customer.email,
        "status": customer.status,
    }


def get_transactions(
    db: Session,
    customer_id: str,
) -> list[dict]:
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