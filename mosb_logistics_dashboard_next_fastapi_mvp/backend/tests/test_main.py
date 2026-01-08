import os

from fastapi.testclient import TestClient

os.environ.setdefault("LOGISTICS_DB_PATH", ":memory:")

from main import app


client = TestClient(app)


def test_get_locations():
    response = client.get("/api/locations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "location_id" in data[0]
        assert "type" in data[0]


def test_get_shipments():
    response = client.get("/api/shipments")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_legs():
    response = client.get("/api/legs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_events():
    response = client.get("/api/events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_events_with_since():
    response = client.get("/api/events?since=2026-01-01T00:00:00Z")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_post_demo_event():
    response = client.post("/api/events/demo")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "event" in data
    assert data["event"]["shpt_no"] == "SHPT-AGI-0001"
    assert "event_id" in data["event"]
    assert "ts" in data["event"]
