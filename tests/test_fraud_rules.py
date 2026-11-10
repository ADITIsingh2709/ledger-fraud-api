from sqlalchemy import select

from app import models


def make_account(client, name="A"):
    return client.post("/accounts", json={"owner_name": name}).json()


def deposit(client, account_id, amount):
    return client.post(f"/accounts/{account_id}/deposit", json={"amount": amount}).json()


def withdraw(client, account_id, amount):
    return client.post(f"/accounts/{account_id}/withdraw", json={"amount": amount}).json()


def get_flags(session_factory):
    with session_factory() as db:
        return db.scalars(select(models.Flag)).all()


def test_large_deposit_is_flagged(client, session_factory):
    acc = make_account(client)
    txn = deposit(client, acc["id"], "10000")
    flags = get_flags(session_factory)
    assert [f.rule for f in flags] == ["LARGE_AMOUNT"]
    assert flags[0].transaction_id == txn["id"]
    assert flags[0].status == "pending"


def test_amount_below_threshold_is_not_flagged(client, session_factory):
    acc = make_account(client)
    deposit(client, acc["id"], "9999.99")
    assert get_flags(session_factory) == []


def test_high_velocity_is_flagged_on_the_sixth_transaction(client, session_factory):
    acc = make_account(client)
    for _ in range(5):
        deposit(client, acc["id"], "1")
    assert get_flags(session_factory) == []

    sixth = deposit(client, acc["id"], "1")
    flags = get_flags(session_factory)
    assert [f.rule for f in flags] == ["HIGH_VELOCITY"]
    assert flags[0].transaction_id == sixth["id"]


def test_unusual_withdrawal_is_flagged(client, session_factory):
    acc = make_account(client)
    deposit(client, acc["id"], "1000")
    for _ in range(3):
        withdraw(client, acc["id"], "10")
    big = withdraw(client, acc["id"], "100")  # 10x the usual 10

    flags = get_flags(session_factory)
    assert [f.rule for f in flags] == ["UNUSUAL_WITHDRAWAL"]
    assert flags[0].transaction_id == big["id"]


def test_large_transfer_is_flagged(client, session_factory):
    a = make_account(client, "A")
    b = make_account(client, "B")
    deposit(client, a["id"], "9000")
    deposit(client, a["id"], "9000")  # balance 18000, each deposit below threshold
    transfer = client.post(
        "/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": "12000"},
    ).json()

    flags = get_flags(session_factory)
    assert [f.rule for f in flags] == ["LARGE_AMOUNT"]
    assert flags[0].transaction_id == transfer["id"]
