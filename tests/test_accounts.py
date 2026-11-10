from decimal import Decimal


def make_account(client, name="Aditi"):
    return client.post("/accounts", json={"owner_name": name}).json()


def test_create_account_starts_at_zero(client):
    response = client.post("/accounts", json={"owner_name": "Aditi"})
    assert response.status_code == 201
    assert Decimal(response.json()["balance"]) == 0


def test_get_missing_account_returns_404(client):
    assert client.get("/accounts/999").status_code == 404


def test_deposit_increases_balance(client):
    acc = make_account(client)
    response = client.post(f"/accounts/{acc['id']}/deposit", json={"amount": "150.50"})
    assert response.status_code == 201
    balance = client.get(f"/accounts/{acc['id']}").json()["balance"]
    assert Decimal(balance) == Decimal("150.50")


def test_withdraw_decreases_balance(client):
    acc = make_account(client)
    client.post(f"/accounts/{acc['id']}/deposit", json={"amount": "100"})
    response = client.post(f"/accounts/{acc['id']}/withdraw", json={"amount": "40"})
    assert response.status_code == 201
    balance = client.get(f"/accounts/{acc['id']}").json()["balance"]
    assert Decimal(balance) == Decimal("60")


def test_withdraw_more_than_balance_is_rejected(client):
    acc = make_account(client)
    client.post(f"/accounts/{acc['id']}/deposit", json={"amount": "50"})
    response = client.post(f"/accounts/{acc['id']}/withdraw", json={"amount": "80"})
    assert response.status_code == 400
    balance = client.get(f"/accounts/{acc['id']}").json()["balance"]
    assert Decimal(balance) == Decimal("50")


def test_negative_or_zero_amount_is_rejected(client):
    acc = make_account(client)
    for bad in ("-10", "0"):
        response = client.post(f"/accounts/{acc['id']}/deposit", json={"amount": bad})
        assert response.status_code == 422
