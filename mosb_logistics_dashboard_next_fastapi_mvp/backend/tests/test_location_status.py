import os
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

os.environ.setdefault("LOGISTICS_DB_PATH", ":memory:")

from main import app, db


client = TestClient(app)


def get_token(username: str = "ops_user", password: str = "ops123") -> str:
    response = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_get_location_status_returns_list():
    token = get_token()
    response = client.get(
        "/api/location-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_location_status_empty_returns_empty_list():
    token = get_token()
    db.conn.execute("DELETE FROM location_status")
    response = client.get(
        "/api/location-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_update_location_status_and_fetch():
    token = get_token()
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.72,
        "status_code": "WARNING",
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True

    response = client.get(
        "/api/location-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    rows = response.json()
    assert any(row["location_id"] == "MOSB_ESNAAD" for row in rows)


def test_update_location_status_unknown_location():
    token = get_token()
    payload = {
        "location_id": "UNKNOWN_SITE",
        "occupancy_rate": 0.2,
        "status_code": "OK",
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 400


def test_update_location_status_requires_authentication():
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.5,
        "status_code": "OK",
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post("/api/location-status/update", json=payload)
    assert response.status_code == 401


def test_update_location_status_invalid_occupancy_rate():
    token = get_token()
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 1.5,
        "status_code": "OK",
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 422


def test_update_location_status_future_timestamp():
    token = get_token()
    future = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=10)
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.2,
        "status_code": "OK",
        "last_updated": future.isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 422


def test_get_location_status_requires_authentication():
    """GET 엔드포인트도 인증이 필요함을 확인"""
    response = client.get("/api/location-status")
    assert response.status_code == 401


def test_update_location_status_role_based_access_ops_allowed():
    """OPS 역할 사용자는 업데이트 가능"""
    token = get_token("ops_user", "ops123")
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.5,
        "status_code": "OK",
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200


def test_update_location_status_role_based_access_admin_allowed():
    """ADMIN 역할 사용자는 업데이트 가능"""
    token = get_token("admin", "admin123")
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.5,
        "status_code": "OK",
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200


def test_update_location_status_role_based_access_finance_denied():
    """FINANCE 역할 사용자는 업데이트 불가"""
    token = get_token("finance_user", "finance123")
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.5,
        "status_code": "OK",
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 403


def test_update_location_status_role_based_access_compliance_denied():
    """COMPLIANCE 역할 사용자는 업데이트 불가"""
    token = get_token("compliance_user", "compliance123")
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.5,
        "status_code": "OK",
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 403


def test_update_location_status_auto_derive_status_code_ok():
    """점유율 < 0.7일 때 status_code 자동 유도: OK"""
    token = get_token()
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.5,
        "status_code": None,
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200

    # 조회하여 자동 유도된 status_code 확인
    response = client.get(
        "/api/location-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    rows = response.json()
    mosb_status = next((r for r in rows if r["location_id"] == "MOSB_ESNAAD"), None)
    assert mosb_status is not None
    assert mosb_status["status_code"] == "OK"
    assert mosb_status["occupancy_rate"] == 0.5


def test_update_location_status_auto_derive_status_code_warning():
    """점유율 0.7 <= rate < 0.9일 때 status_code 자동 유도: WARNING"""
    token = get_token()
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.75,
        "status_code": None,
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200

    response = client.get(
        "/api/location-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    rows = response.json()
    mosb_status = next((r for r in rows if r["location_id"] == "MOSB_ESNAAD"), None)
    assert mosb_status is not None
    assert mosb_status["status_code"] == "WARNING"
    assert mosb_status["occupancy_rate"] == 0.75


def test_update_location_status_auto_derive_status_code_critical():
    """점유율 >= 0.9일 때 status_code 자동 유도: CRITICAL"""
    token = get_token()
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.95,
        "status_code": None,
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200

    response = client.get(
        "/api/location-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    rows = response.json()
    mosb_status = next((r for r in rows if r["location_id"] == "MOSB_ESNAAD"), None)
    assert mosb_status is not None
    assert mosb_status["status_code"] == "CRITICAL"
    assert mosb_status["occupancy_rate"] == 0.95


def test_update_location_status_upsert_behavior():
    """같은 location_id로 두 번 업데이트하면 UPSERT 동작 확인"""
    token = get_token()

    # 첫 번째 업데이트
    now1 = datetime.now(timezone.utc).replace(microsecond=0)
    payload1 = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.5,
        "status_code": "OK",
        "last_updated": now1.isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload1,
    )
    assert response.status_code == 200

    # 두 번째 업데이트 (같은 location_id) - 현재 시간 사용 (미래 시간 검증 방지)
    import time
    time.sleep(1)  # 1초 대기하여 타임스탬프 차이 보장
    now2 = datetime.now(timezone.utc).replace(microsecond=0)
    payload2 = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.8,
        "status_code": "WARNING",
        "last_updated": now2.isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload2,
    )
    assert response.status_code == 200

    # 조회하여 마지막 업데이트 내용이 반영되었는지 확인
    response = client.get(
        "/api/location-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    rows = response.json()
    mosb_statuses = [r for r in rows if r["location_id"] == "MOSB_ESNAAD"]
    assert len(mosb_statuses) == 1  # 중복 없음
    assert mosb_statuses[0]["occupancy_rate"] == 0.8
    assert mosb_statuses[0]["status_code"] == "WARNING"


def test_update_location_status_multiple_locations():
    """여러 location에 대한 status 업데이트 및 조회"""
    token = get_token()

    # 테스트용 location_id 목록 (실제 존재하는 location_id 사용)
    locations = ["MOSB_ESNAAD", "DSV_M19"]
    import time
    for i, loc_id in enumerate(locations):
        if i > 0:
            time.sleep(1)  # 타임스탬프 차이 보장
        now = datetime.now(timezone.utc).replace(microsecond=0)
        payload = {
            "location_id": loc_id,
            "occupancy_rate": 0.3 + (i * 0.2),
            "status_code": "OK",
            "last_updated": now.isoformat(),
        }
        response = client.post(
            "/api/location-status/update",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        assert response.status_code == 200, f"Failed for {loc_id}: {response.json()}"

    # 모든 location status 조회
    response = client.get(
        "/api/location-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    rows = response.json()
    location_ids = {r["location_id"] for r in rows}
    for loc_id in locations:
        assert loc_id in location_ids


def test_update_location_status_invalid_status_code():
    """잘못된 status_code 값 거부"""
    token = get_token()
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.5,
        "status_code": "INVALID_STATUS",
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 422  # Validation error


def test_update_location_status_invalid_iso8601_timestamp():
    """완전히 잘못된 ISO8601 타임스탬프 형식 거부"""
    token = get_token()
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.5,
        "status_code": "OK",
        "last_updated": "not-a-timestamp",
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 422


def test_update_location_status_with_z_suffix():
    """Z suffix를 가진 ISO8601 타임스탬프 허용"""
    token = get_token()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.5,
        "status_code": "OK",
        "last_updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),  # Z suffix
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200


def test_get_location_status_caching():
    """GET 엔드포인트의 캐싱 동작 확인 (간접 테스트 - 업데이트 후 캐시 무효화 확인)"""
    token = get_token()

    # 초기 상태 설정
    now1 = datetime.now(timezone.utc).replace(microsecond=0)
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.5,
        "status_code": "OK",
        "last_updated": now1.isoformat(),
    }
    client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    # 첫 번째 조회
    response1 = client.get(
        "/api/location-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response1.status_code == 200
    rows1 = response1.json()

    # 업데이트 후 캐시 무효화 확인 (시간 경과 후 새로운 타임스탬프 사용)
    import time
    time.sleep(1)
    now2 = datetime.now(timezone.utc).replace(microsecond=0)
    payload["occupancy_rate"] = 0.8
    payload["last_updated"] = now2.isoformat()
    client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    # 두 번째 조회 (캐시 무효화 후 새로운 값 반환)
    response2 = client.get(
        "/api/location-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response2.status_code == 200
    rows2 = response2.json()
    mosb_status = next((r for r in rows2 if r["location_id"] == "MOSB_ESNAAD"), None)
    assert mosb_status is not None
    assert mosb_status["occupancy_rate"] == 0.8  # 업데이트된 값 반영


def test_update_location_status_negative_occupancy_rate():
    """음수 occupancy_rate 거부"""
    token = get_token()
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": -0.1,
        "status_code": "OK",
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 422


def test_update_location_status_boundary_values():
    """경계값 테스트: occupancy_rate = 0.0, 0.7, 0.9, 1.0"""
    token = get_token()
    import time

    # 0.0 -> OK
    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload = {
        "location_id": "MOSB_ESNAAD",
        "occupancy_rate": 0.0,
        "status_code": None,
        "last_updated": now.isoformat(),
    }
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200
    response = client.get("/api/location-status", headers={"Authorization": f"Bearer {token}"})
    rows = response.json()
    status = next((r for r in rows if r["location_id"] == "MOSB_ESNAAD"), None)
    assert status["status_code"] == "OK"

    # 0.7 -> WARNING (경계값)
    time.sleep(1)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload["occupancy_rate"] = 0.7
    payload["last_updated"] = now.isoformat()
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200
    response = client.get("/api/location-status", headers={"Authorization": f"Bearer {token}"})
    rows = response.json()
    status = next((r for r in rows if r["location_id"] == "MOSB_ESNAAD"), None)
    assert status["status_code"] == "WARNING"

    # 0.9 -> CRITICAL (경계값)
    time.sleep(1)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload["occupancy_rate"] = 0.9
    payload["last_updated"] = now.isoformat()
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200
    response = client.get("/api/location-status", headers={"Authorization": f"Bearer {token}"})
    rows = response.json()
    status = next((r for r in rows if r["location_id"] == "MOSB_ESNAAD"), None)
    assert status["status_code"] == "CRITICAL"

    # 1.0 -> CRITICAL
    time.sleep(1)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload["occupancy_rate"] = 1.0
    payload["last_updated"] = now.isoformat()
    response = client.post(
        "/api/location-status/update",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200
    response = client.get("/api/location-status", headers={"Authorization": f"Bearer {token}"})
    rows = response.json()
    status = next((r for r in rows if r["location_id"] == "MOSB_ESNAAD"), None)
    assert status["status_code"] == "CRITICAL"
