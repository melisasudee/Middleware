import json


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["data"]["service"] == "middleware"


def test_export_endpoint_requires_format_limit(client):
    response = client.get("/export?format=json&limit=1")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert isinstance(payload["data"], list)


def test_unauthorized_process(client):
    response = client.post("/process", json={"transaction_id": "T1"})
    assert response.status_code == 401
    payload = response.get_json()
    assert payload["message"] == "Unauthorized"
