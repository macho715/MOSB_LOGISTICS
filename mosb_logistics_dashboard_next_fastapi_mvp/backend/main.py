from __future__ import annotations

import csv
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Type

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from cache import CacheManager
from db import Database
from models import Event, Leg, Location, Shipment, LocationStatus, LocationStatusUpdate, derive_status_code
from auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    Token,
    User,
)
from rbac import require_role

DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
WS_PING_INTERVAL = int(os.getenv("WS_PING_INTERVAL", "10"))
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def read_csv(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def append_event(event: Dict[str, Any]) -> None:
    path = os.path.join(DATA_DIR, "events.csv")
    exists = os.path.exists(path)
    fieldnames = ["event_id", "ts", "shpt_no", "status", "location_id", "lat", "lon", "remark"]
    with open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            w.writeheader()
        w.writerow({k: event.get(k, "") for k in fieldnames})


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_iso_ts(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def parse_rows(rows: List[Dict[str, Any]], model: Type[BaseModel], label: str):
    parsed = []
    for row in rows:
        try:
            parsed.append(model.model_validate(row))
        except Exception as exc:
            logger.warning("Skipping %s row: %s", label, exc)
    return parsed


db = Database()
cache = CacheManager()

app = FastAPI(title="MOSB Logistics Live API", version="0.1.0")

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

# CORS for local dev (tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_log() -> None:
    """KR: 앱 시작 로그를 남깁니다. EN: Log application startup."""
    logger.info("MOSB Logistics API startup")


@app.on_event("shutdown")
async def shutdown_cleanup() -> None:
    """
    KR: 앱 종료 시 리소스를 정리합니다.
    - WebSocket 연결 종료
    - 캐시 정리
    - DB 연결 종료

    EN: Clean up resources on application shutdown.
    - Close WebSocket connections
    - Clear cache
    - Close DB connection
    """
    logger.info("MOSB Logistics API shutdown initiated")

    # 1. WebSocket 클라이언트 연결 종료
    try:
        if hub.clients:
            logger.info("Closing %d WebSocket client connections", len(hub.clients))
            disconnected = 0
            for ws in list(hub.clients):
                try:
                    await ws.close()
                    disconnected += 1
                except Exception as exc:
                    logger.debug("Error closing WebSocket: %s", exc)
            hub.clients.clear()
            logger.info("Closed %d WebSocket connections", disconnected)
    except Exception as exc:
        logger.warning("WebSocket cleanup failed on shutdown: %s", exc)

    # 2. 캐시 정리
    try:
        cache.invalidate_all()
        logger.debug("Cache cleared on shutdown")
    except Exception as exc:
        logger.warning("Cache cleanup failed on shutdown: %s", exc)

    # 3. DB 연결 종료
    try:
        db.close()
        logger.info("Database connection closed")
    except Exception as exc:
        logger.warning("DB close failed on shutdown: %s", exc)

    logger.info("MOSB Logistics API shutdown complete")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/api/locations", response_model=list[Location])
def get_locations(current_user: User = Depends(get_current_user)):
    cached = cache.get_cached_locations()
    if cached is not None:
        return cached
    try:
        locations = db.get_locations()
    except Exception as exc:
        logger.warning("DB locations fetch failed: %s", exc)
        rows = read_csv(os.path.join(DATA_DIR, "locations.csv"))
        locations = parse_rows(rows, Location, "location")
    cache.set_cached_locations("all", locations)
    return locations


@app.get("/api/legs", response_model=list[Leg])
def get_legs(current_user: User = Depends(get_current_user)):
    cached = cache.get_cached_legs()
    if cached is not None:
        return cached
    try:
        legs = db.get_legs()
    except Exception as exc:
        logger.warning("DB legs fetch failed: %s", exc)
        rows = read_csv(os.path.join(DATA_DIR, "legs.csv"))
        legs = parse_rows(rows, Leg, "leg")
    cache.set_cached_legs("all", legs)
    return legs


@app.get("/api/shipments", response_model=list[Shipment])
def get_shipments(current_user: User = Depends(require_role(["OPS", "FINANCE", "ADMIN"]))):
    cached = cache.get_cached_shipments()
    if cached is not None:
        return cached
    try:
        shipments = db.get_shipments()
    except Exception as exc:
        logger.warning("DB shipments fetch failed: %s", exc)
        rows = read_csv(os.path.join(DATA_DIR, "shipments.csv"))
        shipments = parse_rows(rows, Shipment, "shipment")
    cache.set_cached_shipments("all", shipments)
    return shipments


@app.get("/api/events", response_model=list[Event])
def get_events(since: Optional[str] = None, current_user: User = Depends(get_current_user)):
    cache_key = f"events:{since or 'all'}"
    cached = cache.get_cached_events(cache_key)
    if cached is not None:
        return cached
    try:
        events = db.get_events(since)
    except Exception as exc:
        logger.warning("DB events fetch failed: %s", exc)
        rows = read_csv(os.path.join(DATA_DIR, "events.csv"))
        if not since:
            events = parse_rows(rows, Event, "event")
        else:
            since_dt = parse_iso_ts(since)
            if not since_dt:
                events = parse_rows(rows, Event, "event")
            else:
                out = []
                for r in rows:
                    ts = parse_iso_ts(r.get("ts", ""))
                    if ts and ts >= since_dt:
                        out.append(r)
                events = parse_rows(out, Event, "event")
    cache.set_cached_events(cache_key, events)
    return events


# Location status endpoints


@app.get("/api/location-status", response_model=list[LocationStatus])
def get_location_status_api(current_user: User = Depends(get_current_user)):
    """
    Return the latest status for all locations.
    """
    cached = cache.get_cached_location_status()
    if cached is not None:
        return cached
    try:
        status_list = db.get_location_status()
    except Exception as exc:
        logger.warning("DB location status fetch failed: %s", exc)
        status_list = []
    cache.set_cached_location_status("all", status_list)
    return status_list


@app.post("/api/location-status/update")
async def update_location_status_api(
    update: LocationStatusUpdate, current_user: User = Depends(require_role(["OPS", "ADMIN"]))
) -> dict[str, bool]:
    """
    Update or insert a location status record.
    If status_code is omitted, it will be auto-derived from occupancy_rate.
    """
    try:
        location_ids = {loc.location_id for loc in db.get_locations()}
    except Exception as exc:
        logger.warning("Location validation failed: %s", exc)
        raise HTTPException(status_code=400, detail="Location validation failed") from exc
    if update.location_id not in location_ids:
        raise HTTPException(status_code=400, detail=f"Unknown location_id: {update.location_id}")

    # Ensure status_code is always set (auto-derive if None)
    status_code = update.status_code if update.status_code is not None else derive_status_code(update.occupancy_rate)

    # Create LocationStatus (output model) with guaranteed non-null status_code
    status = LocationStatus(
        location_id=update.location_id,
        occupancy_rate=update.occupancy_rate,
        status_code=status_code,
        last_updated=update.last_updated,
    )

    db.upsert_location_status(status)
    cache.invalidate_location_status()
    # broadcast update to websocket clients (always non-null status_code)
    await hub.broadcast({"type": "location_status", "payload": status.model_dump()})
    return {"ok": True}


# Simple websocket broadcaster
class Hub:
    def __init__(self):
        self.clients: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.clients.append(ws)

    def disconnect(self, ws: WebSocket):
        try:
            self.clients.remove(ws)
        except ValueError:
            pass

    async def broadcast(self, msg: Dict[str, Any]):
        dead = []
        for c in self.clients:
            try:
                await c.send_json(msg)
            except Exception:
                dead.append(c)
        for c in dead:
            self.disconnect(c)


hub = Hub()


@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await hub.connect(ws)
    try:
        # Send a hello payload
        await ws.send_json({"type": "hello", "ts": iso_now()})
        while True:
            # Keepalive ping; clients can ignore
            await ws.send_json({"type": "ping", "ts": iso_now()})
            await asyncio_sleep(WS_PING_INTERVAL)
    except WebSocketDisconnect:
        hub.disconnect(ws)


# Avoid importing asyncio at top for readability
async def asyncio_sleep(sec: int):
    import asyncio

    await asyncio.sleep(sec)


@app.post("/api/events/demo")
async def post_demo_event(current_user: User = Depends(require_role(["OPS", "ADMIN"]))):
    """
    Demo endpoint: appends a synthetic IN_TRANSIT update and broadcasts to WS clients.
    Replace with real integrations (WMS/ERP/Email/OCR/GPS).
    """
    event = Event(
        event_id=f"EV-{uuid.uuid4().hex[:8]}",
        ts=iso_now(),
        shpt_no="SHPT-AGI-0001",
        status="IN_TRANSIT",
        location_id="MOSB_ESNAAD",
        lat=24.328853,
        lon=54.458570,
        remark="Demo tick",
    )
    payload = event.model_dump()
    try:
        db.append_event(event)
    except Exception as exc:
        logger.warning("DB event append failed: %s", exc)
    append_event(payload)
    cache.invalidate_events()
    await hub.broadcast({"type": "event", "payload": payload})
    return {"ok": True, "event": event}
