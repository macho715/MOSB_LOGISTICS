from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_locations():
    r = client.get("/api/locations")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_shipments():
    r = client.get("/api/shipments")
    assert r.status_code == 200

def test_legs():
    r = client.get("/api/legs")
    assert r.status_code == 200

def test_events():
    r = client.get("/api/events")
    assert r.status_code == 200

def test_demo_event():
    r = client.post("/api/events/demo")
    assert r.status_code == 200
    body = r.json()
    assert body["shpt_no"] == "SHPT-AGI-0001"
