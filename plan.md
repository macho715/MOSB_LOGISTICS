# plan.md (SoT)

## Tests

### Backend API Tests (mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_main.py)
- [x] test: get locations (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_main.py, name: test_get_locations) # passed @2026-01-08
- [x] test: get shipments (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_main.py, name: test_get_shipments) # passed @2026-01-08
- [x] test: get legs (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_main.py, name: test_get_legs) # passed @2026-01-08
- [x] test: get events (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_main.py, name: test_get_events) # passed @2026-01-08
- [x] test: get events with since filter (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_main.py, name: test_get_events_with_since) # passed @2026-01-08
- [x] test: post demo event (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_main.py, name: test_post_demo_event) # passed @2026-01-08

### Authentication Tests (mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_auth.py)
- [x] test: login success (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_auth.py, name: test_login_success) # passed @2026-01-08
- [x] test: login failure (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_auth.py, name: test_login_failure) # passed @2026-01-08
- [x] test: get me with token (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_auth.py, name: test_get_me_with_token) # passed @2026-01-08
- [x] test: protected endpoint without token (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_auth.py, name: test_protected_endpoint_without_token) # passed @2026-01-08
- [x] test: protected endpoint with token (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_auth.py, name: test_protected_endpoint_with_token) # passed @2026-01-08
- [x] test: RBAC access denied (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_auth.py, name: test_rbac_access_denied) # passed @2026-01-08

### Database Tests (mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_db.py)
- [x] test: DB connection (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_db.py, name: test_db_connection) # passed @2026-01-08
- [x] test: DB get locations (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_db.py, name: test_db_get_locations) # passed @2026-01-08
- [x] test: DB get events with since (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_db.py, name: test_db_get_events_with_since) # passed @2026-01-08
- [x] test: DB append event (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_db.py, name: test_db_append_event) # passed @2026-01-08

### Cache Tests (mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_cache.py)
- [x] test: cache hit (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_cache.py, name: test_cache_hit) # passed @2026-01-08
- [x] test: cache miss (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_cache.py, name: test_cache_miss) # passed @2026-01-08
- [x] test: cache TTL (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_cache.py, name: test_cache_ttl) # passed @2026-01-08
- [x] test: cache invalidation (file: mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_cache.py, name: test_cache_invalidation) # passed @2026-01-08

## Notes
- All 20 tests are passing as of Phase 3.2 implementation
- Mark passed tests as: `- [x] ... # passed @YYYY-MM-DD <commit:hash>`
- Test execution: `cd mosb_logistics_dashboard_next_fastapi_mvp/backend && pytest -q -v`
