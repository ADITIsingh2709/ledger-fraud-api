def make_account(client, name="A"):
    return client.post("/accounts", json={"owner_name": name}).json()


def test_statement_lists_transactions_newest_first(client):
    acc = make_account(client)
    client.post(f"/accounts/{acc['id']}/deposit", json={"amount": "100"})
    client.post(f"/accounts/{acc['id']}/withdraw", json={"amount": "30"})

    response = client.get(f"/accounts/{acc['id']}/statement")
    assert response.status_code == 200
    entries = response.json()
    assert [e["type"] for e in entries] == ["withdrawal", "deposit"]


def test_transfer_appears_in_both_statements(client):
    a = make_account(client, "A")
    b = make_account(client, "B")
    client.post(f"/accounts/{a['id']}/deposit", json={"amount": "100"})
    client.post(
        "/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": "40"},
    )

    a_types = [e["type"] for e in client.get(f"/accounts/{a['id']}/statement").json()]
    b_types = [e["type"] for e in client.get(f"/accounts/{b['id']}/statement").json()]
    assert a_types == ["transfer", "deposit"]
    assert b_types == ["transfer"]


def test_statement_for_missing_account_returns_404(client):
    assert client.get("/accounts/999/statement").status_code == 404
