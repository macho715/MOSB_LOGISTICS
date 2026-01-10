import os
import sys
from pathlib import Path
from typing import Callable

import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ.setdefault("LOGISTICS_DB_PATH", ":memory:")

from main import app, cache, db


@pytest.fixture()
def client() -> TestClient:
    """KR: 테스트 클라이언트를 제공합니다. EN: Provide a test client."""
    return TestClient(app)


@pytest.fixture()
def token_factory(client: TestClient) -> Callable[..., str]:
    """KR: 토큰 발급 헬퍼입니다. EN: Helper for issuing auth tokens."""

    def _factory(username: str = "ops_user", password: str = "ops123") -> str:
        response = client.post(
            "/api/auth/login",
            data={"username": username, "password": password},
        )
        assert response.status_code == 200
        return response.json()["access_token"]

    return _factory


@pytest.fixture(autouse=True)
def reset_location_status() -> None:
    """KR: 위치 상태 테이블을 초기화합니다. EN: Reset location status table."""
    # Clear location_status table before each test
    db.conn.execute("DELETE FROM location_status")
    cache.invalidate_location_status()
    yield
    # Cleanup after test
    db.conn.execute("DELETE FROM location_status")
    cache.invalidate_location_status()
