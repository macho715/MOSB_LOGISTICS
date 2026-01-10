from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import pytest
from fastapi.testclient import TestClient
from main import cache


def _auth_header(token_factory: Callable[..., str]) -> dict[str, str]:
    """KR: 인증 헤더를 구성합니다. EN: Build an auth header."""
    token = token_factory()
    return {"Authorization": f"Bearer {token}"}


def _now_iso() -> str:
    """KR: 현재 UTC 시간을 ISO 문자열로 반환합니다. EN: Return current UTC ISO string."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def test_location_status_cache_miss_sets_cache(
    client: TestClient,
    token_factory: Callable[..., str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KR: 캐시 미스 시 캐시 저장 호출을 검증합니다. EN: Verify cache set on miss."""
    set_called = {"value": False}

    def fake_get_cached_location_status(key: str = "all") -> Any:
        return None

    def fake_set_cached_location_status(key: str, value: list[Any]) -> None:
        set_called["value"] = True

    monkeypatch.setattr(cache, "get_cached_location_status", fake_get_cached_location_status)
    monkeypatch.setattr(cache, "set_cached_location_status", fake_set_cached_location_status)

    response = client.get("/api/location-status", headers=_auth_header(token_factory))
    assert response.status_code == 200
    assert set_called["value"] is True


def test_location_status_cache_hit_uses_cache(
    client: TestClient,
    token_factory: Callable[..., str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KR: 캐시 히트 시 캐시 결과를 반환합니다. EN: Return cached payload on hit."""
    cached_payload = [
        {
            "location_id": "MOSB_ESNAAD",
            "ts": "2024-01-01T00:00:00+00:00",
            "status": "OK",
            "status_code": "GREEN",
            "remark": "",
        },
    ]

    def fake_get_cached_location_status(key: str = "all") -> list[dict[str, Any]]:
        return cached_payload

    def fake_set_cached_location_status(key: str, value: list[Any]) -> None:
        raise AssertionError("cache set should not be called on hit")

    monkeypatch.setattr(cache, "get_cached_location_status", fake_get_cached_location_status)
    monkeypatch.setattr(cache, "set_cached_location_status", fake_set_cached_location_status)

    response = client.get("/api/location-status", headers=_auth_header(token_factory))
    assert response.status_code == 200
    assert response.json() == cached_payload


def test_location_status_status_code_is_server_derived(
    client: TestClient,
    token_factory: Callable[..., str],
) -> None:
    """KR: status_code는 서버에서 파생됩니다. EN: status_code is server-derived."""
    payload = {
        "location_id": "MOSB_ESNAAD",
        "ts": _now_iso(),
        "status": "CRITICAL",
        "status_code": "GREEN",
        "remark": "override check",
    }

    response = client.post(
        "/api/location-status",
        json=payload,
        headers=_auth_header(token_factory),
    )
    assert response.status_code == 200
    assert response.json()["status_code"] == "RED"


def test_location_status_rejects_invalid_location_id(
    client: TestClient,
    token_factory: Callable[..., str],
) -> None:
    """KR: 잘못된 location_id를 거부합니다. EN: Reject invalid location_id."""
    payload = {"location_id": "UNKNOWN", "ts": _now_iso(), "status": "OK"}
    response = client.post(
        "/api/location-status",
        json=payload,
        headers=_auth_header(token_factory),
    )
    assert response.status_code in {400, 404}


def test_location_status_rejects_future_ts(
    client: TestClient,
    token_factory: Callable[..., str],
) -> None:
    """KR: 미래 타임스탬프를 거부합니다. EN: Reject future timestamps."""
    future_ts = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {"location_id": "MOSB_ESNAAD", "ts": future_ts, "status": "OK"}
    response = client.post(
        "/api/location-status",
        json=payload,
        headers=_auth_header(token_factory),
    )
    assert response.status_code == 400


def test_location_status_requires_ops_or_admin(
    client: TestClient,
    token_factory: Callable[..., str],
) -> None:
    """KR: OPS/ADMIN 권한만 업데이트 가능합니다. EN: Only OPS/ADMIN can update."""
    token = token_factory("compliance_user", "compliance123")
    payload = {"location_id": "MOSB_ESNAAD", "ts": _now_iso(), "status": "OK"}
    response = client.post(
        "/api/location-status",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_location_status_rejects_out_of_order_ts(
    client: TestClient,
    token_factory: Callable[..., str],
) -> None:
    """KR: 과거 타임스탬프 업데이트를 거부합니다. EN: Reject out-of-order ts."""
    now_ts = datetime.now(timezone.utc).replace(microsecond=0)
    payload = {
        "location_id": "MOSB_ESNAAD",
        "ts": now_ts.isoformat(),
        "status": "OK",
    }
    response = client.post(
        "/api/location-status",
        json=payload,
        headers=_auth_header(token_factory),
    )
    assert response.status_code == 200

    past_payload = {
        "location_id": "MOSB_ESNAAD",
        "ts": (now_ts - timedelta(hours=1)).isoformat(),
        "status": "WARN",
    }
    response = client.post(
        "/api/location-status",
        json=past_payload,
        headers=_auth_header(token_factory),
    )
    assert response.status_code == 409
