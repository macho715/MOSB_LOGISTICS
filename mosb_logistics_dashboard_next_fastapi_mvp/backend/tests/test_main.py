import os

from fastapi.testclient import TestClient

os.environ.setdefault("LOGISTICS_DB_PATH", ":memory:")

from main import app


client = TestClient(app)

def get_token(username: str = "ops_user", password: str = "ops123") -> str:
    response = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_get_locations():
    token = get_token()
    response = client.get(
        "/api/locations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "location_id" in data[0]
        assert "type" in data[0]


def test_get_shipments():
    token = get_token()
    response = client.get(
        "/api/shipments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_legs():
    token = get_token()
    response = client.get(
        "/api/legs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_events():
    token = get_token()
    response = client.get(
        "/api/events",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_events_with_since():
    token = get_token()
    response = client.get(
        "/api/events?since=2026-01-01T00:00:00Z",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_post_demo_event():
    token = get_token()
    response = client.post(
        "/api/events/demo",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "event" in data
    assert data["event"]["shpt_no"] == "SHPT-AGI-0001"
    assert "event_id" in data["event"]
    assert "ts" in data["event"]
