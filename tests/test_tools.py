from app import tools


def test_lookup_customer_found(monkeypatch, seeded_sessionmaker):
    monkeypatch.setattr(tools, "SessionLocal", seeded_sessionmaker)

    result = tools.lookup_customer.invoke({"customer_id": "C1001"})

    assert result == {
        "found": True,
        "id": "C1001",
        "name": "Alice Smith",
        "email": "alice@example.com",
        "status": "active",
    }


def test_lookup_customer_not_found(monkeypatch, seeded_sessionmaker):
    monkeypatch.setattr(tools, "SessionLocal", seeded_sessionmaker)

    result = tools.lookup_customer.invoke({"customer_id": "UNKNOWN"})

    assert result == {"found": False}


def test_lookup_transactions_found(monkeypatch, seeded_sessionmaker):
    monkeypatch.setattr(tools, "SessionLocal", seeded_sessionmaker)

    result = tools.lookup_transactions.invoke({"customer_id": "C1001"})

    assert len(result) == 2
    assert {transaction["id"] for transaction in result} == {"T1001", "T1002"}
    assert all(transaction["status"] == "completed" for transaction in result)


def test_lookup_transactions_empty_for_unknown_customer(
    monkeypatch, seeded_sessionmaker
):
    monkeypatch.setattr(tools, "SessionLocal", seeded_sessionmaker)

    result = tools.lookup_transactions.invoke({"customer_id": "UNKNOWN"})

    assert result == []
