import json


def test_login_success(client):
    payload = {"username": "admin", "password": "secret"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "access_token" in data["data"]


def test_api_key_access(client):
    response = client.post(
        "/process",
        json={"transaction_id": "T1", "sender_id": "BANK_A", "amount": 100.0, "error_level": "INFO"},
        headers={"X-API-KEY": "test-api-key"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["data"]["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
