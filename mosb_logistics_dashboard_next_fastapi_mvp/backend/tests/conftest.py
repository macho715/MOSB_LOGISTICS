import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ.setdefault("LOGISTICS_DB_PATH", ":memory:")

from main import app, cache, LOCATION_STATUS_STORE


@pytest.fixture()
def client() -> TestClient:
    """KR: FastAPI 테스트 클라이언트를 제공합니다. EN: Provide FastAPI test client."""
    return TestClient(app)


def _get_token(client: TestClient, username: str, password: str) -> str:
    """KR: 테스트 토큰을 발급합니다. EN: Issue a test token."""
    response = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def ops_token(client: TestClient) -> str:
    """KR: OPS 권한 토큰을 제공합니다. EN: Provide OPS role token."""
    return _get_token(client, "ops_user", "ops123")


@pytest.fixture()
def finance_token(client: TestClient) -> str:
    """KR: FINANCE 권한 토큰을 제공합니다. EN: Provide FINANCE role token."""
    return _get_token(client, "finance_user", "finance123")


@pytest.fixture()
def admin_token(client: TestClient) -> str:
    """KR: ADMIN 권한 토큰을 제공합니다. EN: Provide ADMIN role token."""
    return _get_token(client, "admin", "admin123")


@pytest.fixture(autouse=True)
def reset_location_status_state() -> None:
    """KR: 위치 상태 캐시를 초기화합니다. EN: Reset location status cache."""
    LOCATION_STATUS_STORE.clear()
    cache.invalidate_location_status()
    yield
    LOCATION_STATUS_STORE.clear()
    cache.invalidate_location_status()
