def make_flagged_deposit(client):
    acc = client.post("/accounts", json={"owner_name": "A"}).json()
    txn = client.post(f"/accounts/{acc['id']}/deposit", json={"amount": "10000"}).json()
    return acc, txn


def test_flagged_transaction_appears_in_queue(client):
    _, txn = make_flagged_deposit(client)
    response = client.get("/flags")
    assert response.status_code == 200
    flags = response.json()
    assert len(flags) == 1
    assert flags[0]["rule"] == "LARGE_AMOUNT"
    assert flags[0]["transaction_id"] == txn["id"]
    assert flags[0]["status"] == "pending"
    assert "threshold" in flags[0]["reason"]


def test_queue_is_empty_when_nothing_is_flagged(client):
    acc = client.post("/accounts", json={"owner_name": "A"}).json()
    client.post(f"/accounts/{acc['id']}/deposit", json={"amount": "50"})
    assert client.get("/flags").json() == []


def test_review_flag_updates_status_and_filter(client):
    make_flagged_deposit(client)
    flag_id = client.get("/flags").json()[0]["id"]

    response = client.patch(f"/flags/{flag_id}", json={"status": "reviewed"})
    assert response.status_code == 200
    assert response.json()["status"] == "reviewed"

    assert client.get("/flags?status=pending").json() == []
    assert len(client.get("/flags?status=reviewed").json()) == 1


def test_invalid_review_status_is_rejected(client):
    make_flagged_deposit(client)
    flag_id = client.get("/flags").json()[0]["id"]
    response = client.patch(f"/flags/{flag_id}", json={"status": "approved-maybe"})
    assert response.status_code == 422


def test_review_missing_flag_returns_404(client):
    response = client.patch("/flags/999", json={"status": "reviewed"})
    assert response.status_code == 404
