from decimal import Decimal

import pytest
from sqlalchemy.orm import Session


def make_account(client, name, deposit=None):
    acc = client.post("/accounts", json={"owner_name": name}).json()
    if deposit:
        client.post(f"/accounts/{acc['id']}/deposit", json={"amount": deposit})
    return acc


def balance(client, account_id):
    return Decimal(client.get(f"/accounts/{account_id}").json()["balance"])


def test_transfer_moves_money(client):
    a = make_account(client, "A", "100")
    b = make_account(client, "B")
    response = client.post(
        "/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": "30"},
    )
    assert response.status_code == 201
    assert balance(client, a["id"]) == Decimal("70")
    assert balance(client, b["id"]) == Decimal("30")


def test_transfer_with_insufficient_funds_changes_nothing(client):
    a = make_account(client, "A", "20")
    b = make_account(client, "B")
    response = client.post(
        "/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": "50"},
    )
    assert response.status_code == 400
    assert balance(client, a["id"]) == Decimal("20")
    assert balance(client, b["id"]) == Decimal("0")


def test_transfer_to_same_account_is_rejected(client):
    a = make_account(client, "A", "100")
    response = client.post(
        "/transfers",
        json={"from_account_id": a["id"], "to_account_id": a["id"], "amount": "10"},
    )
    assert response.status_code == 400


def test_transfer_to_missing_account_returns_404(client):
    a = make_account(client, "A", "100")
    response = client.post(
        "/transfers",
        json={"from_account_id": a["id"], "to_account_id": 999, "amount": "10"},
    )
    assert response.status_code == 404
    assert balance(client, a["id"]) == Decimal("100")


def test_failed_transfer_rolls_back_both_balances(client, monkeypatch):
    a = make_account(client, "A", "100")
    b = make_account(client, "B", "10")

    def crash(self):
        raise RuntimeError("simulated database failure")

    with monkeypatch.context() as m:
        m.setattr(Session, "commit", crash)
        with pytest.raises(RuntimeError):
            client.post(
                "/transfers",
                json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": "40"},
            )

    # commit is restored here; neither balance should have changed
    assert balance(client, a["id"]) == Decimal("100")
    assert balance(client, b["id"]) == Decimal("10")
