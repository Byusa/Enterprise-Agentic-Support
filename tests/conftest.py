from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Customer, Transaction  # noqa: F401 - register models on Base


@pytest.fixture()
def test_sessionmaker():
    # StaticPool + check_same_thread=False: a single shared SQLite
    # in-memory connection, reachable from LangGraph's tool-execution
    # thread as well as the test thread.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    yield SessionLocal

    engine.dispose()


@pytest.fixture()
def seeded_sessionmaker(test_sessionmaker):
    db = test_sessionmaker()

    try:
        customer = Customer(
            customer_id="C1001",
            name="Alice Smith",
            email="alice@example.com",
            status="active",
        )
        db.add(customer)
        db.flush()

        db.add_all(
            [
                Transaction(
                    transaction_id="T1001",
                    customer_db_id=customer.id,
                    amount=Decimal("49.99"),
                    transaction_type="subscription",
                    status="completed",
                ),
                Transaction(
                    transaction_id="T1002",
                    customer_db_id=customer.id,
                    amount=Decimal("49.99"),
                    transaction_type="subscription",
                    status="completed",
                ),
            ]
        )
        db.commit()

    finally:
        db.close()

    return test_sessionmaker
