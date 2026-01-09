import os

from fastapi.testclient import TestClient

os.environ.setdefault("LOGISTICS_DB_PATH", ":memory:")

from main import app


client = TestClient(app)


def test_login_success():
    response = client.post(
        "/api/auth/login",
        data={"username": "ops_user", "password": "ops123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure():
    response = client.post(
        "/api/auth/login",
        data={"username": "ops_user", "password": "wrong"},
    )
    assert response.status_code == 401


def test_get_me_with_token():
    login_response = client.post(
        "/api/auth/login",
        data={"username": "ops_user", "password": "ops123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "ops_user"
    assert data["role"] == "OPS"


def test_protected_endpoint_without_token():
    response = client.get("/api/shipments")
    assert response.status_code == 401


def test_protected_endpoint_with_token():
    login_response = client.post(
        "/api/auth/login",
        data={"username": "ops_user", "password": "ops123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/shipments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_rbac_access_denied():
    login_response = client.post(
        "/api/auth/login",
        data={"username": "compliance_user", "password": "compliance123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/shipments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
