from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def _auth_headers(token: str) -> dict[str, str]:
    """KR: 인증 헤더를 생성합니다. EN: Build auth headers."""
    return {"Authorization": f"Bearer {token}"}


def _iso_now() -> str:
    """KR: 현재 UTC 시간을 ISO로 반환합니다. EN: Return ISO UTC now."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _location_id(client: TestClient, token: str) -> str:
    """KR: 테스트용 위치 ID를 조회합니다. EN: Fetch a test location id."""
    response = client.get("/api/locations", headers=_auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    if data:
        return data[0]["location_id"]
    return "MOSB_ESNAAD"


def test_location_status_cache_hit_miss(client: TestClient, ops_token: str) -> None:
    response = client.get("/api/location-status", headers=_auth_headers(ops_token))
    assert response.status_code == 200
    assert response.headers.get("x-cache") == "MISS"

    response = client.get("/api/location-status", headers=_auth_headers(ops_token))
    assert response.status_code == 200
    assert response.headers.get("x-cache") == "HIT"


def test_location_status_status_code_derived(client: TestClient, ops_token: str) -> None:
    location_id = _location_id(client, ops_token)
    payload = {
        "location_id": location_id,
        "ts": _iso_now(),
        "status": "WARN",
        "status_code": 999,
    }
    response = client.post(
        "/api/location-status",
        headers=_auth_headers(ops_token),
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "WARN"
    assert data["status_code"] == 200


def test_location_status_rejects_invalid_location(client: TestClient, ops_token: str) -> None:
    payload = {
        "location_id": "INVALID_LOCATION",
        "ts": _iso_now(),
        "status": "OK",
    }
    response = client.post(
        "/api/location-status",
        headers=_auth_headers(ops_token),
        json=payload,
    )
    assert response.status_code == 404


def test_location_status_rejects_future_ts(client: TestClient, ops_token: str) -> None:
    location_id = _location_id(client, ops_token)
    future_ts = (datetime.now(timezone.utc) + timedelta(hours=1)).replace(
        microsecond=0,
    )
    payload = {
        "location_id": location_id,
        "ts": future_ts.isoformat(),
        "status": "OK",
    }
    response = client.post(
        "/api/location-status",
        headers=_auth_headers(ops_token),
        json=payload,
    )
    assert response.status_code == 400


def test_location_status_requires_role(client: TestClient, finance_token: str) -> None:
    payload = {
        "location_id": "MOSB_ESNAAD",
        "ts": _iso_now(),
        "status": "OK",
    }
    response = client.post(
        "/api/location-status",
        headers=_auth_headers(finance_token),
        json=payload,
    )
    assert response.status_code == 403


def test_location_status_rejects_monotonic_update(client: TestClient, ops_token: str) -> None:
    location_id = _location_id(client, ops_token)
    first_ts = datetime.now(timezone.utc).replace(microsecond=0)
    payload = {
        "location_id": location_id,
        "ts": first_ts.isoformat(),
        "status": "OK",
    }
    response = client.post(
        "/api/location-status",
        headers=_auth_headers(ops_token),
        json=payload,
    )
    assert response.status_code == 200

    older_ts = (first_ts - timedelta(minutes=5)).isoformat()
    response = client.post(
        "/api/location-status",
        headers=_auth_headers(ops_token),
        json={**payload, "ts": older_ts},
    )
    assert response.status_code == 409
