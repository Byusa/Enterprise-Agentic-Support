from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer, Transaction


def get_customer_by_customer_id(
    db: Session,
    customer_id: str,
) -> Customer | None:
    statement = select(Customer).where(
        Customer.customer_id == customer_id
    )

    return db.scalar(statement)


def get_transactions_by_customer_id(
    db: Session,
    customer_id: str,
) -> list[Transaction]:
    statement = (
        select(Transaction)
        .join(Customer)
        .where(Customer.customer_id == customer_id)
        .order_by(Transaction.created_at.desc())
    )

    return list(db.scalars(statement).all())