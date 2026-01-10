from __future__ import annotations

import csv
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from auth import (
    Token,
    User,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from cache import CacheManager
from db import Database
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from models import Event, Leg, Location, LocationStatus, LocationStatusUpdate, Shipment
from pydantic import BaseModel
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
    fieldnames = ["event_id","ts","shpt_no","status","location_id","lat","lon","remark"]
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


def fetch_locations() -> list[Location]:
    """KR: 위치 목록을 조회합니다. EN: Fetch location list."""
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


def derive_status_code(status_value: str) -> str:
    """KR: 상태 값을 코드로 변환합니다. EN: Derive status code from status."""
    mapping = {
        "OK": "GREEN",
        "WARN": "AMBER",
        "CRITICAL": "RED",
    }
    return mapping[status_value]

db = Database()
cache = CacheManager()
location_status_store: Dict[str, LocationStatus] = {}

app = FastAPI(title="MOSB Logistics Live API", version="0.1.0")

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
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
    """KR: 앱 종료 시 DB 연결을 닫습니다. EN: Close DB connection on shutdown."""
    logger.info("MOSB Logistics API shutdown")
    try:
        db.close()
    except Exception as exc:
        logger.warning("DB close failed on shutdown: %s", exc)

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
    return fetch_locations()

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


@app.get("/api/location-status", response_model=list[LocationStatus])
def get_location_status(current_user: User = Depends(get_current_user)):
    """KR: 위치 상태 목록을 반환합니다. EN: Return location status list."""
    cached = cache.get_cached_location_status()
    if cached is not None:
        return cached
    statuses = list(location_status_store.values())
    cache.set_cached_location_status("all", statuses)
    return statuses


@app.post("/api/location-status", response_model=LocationStatus)
def post_location_status(
    payload: LocationStatusUpdate,
    current_user: User = Depends(require_role(["OPS", "ADMIN"])),
):
    """KR: 위치 상태를 업데이트합니다. EN: Update location status."""
    locations = fetch_locations()
    location_ids = {location.location_id for location in locations}
    if payload.location_id not in location_ids:
        raise HTTPException(status_code=404, detail="Unknown location_id")
    ts = parse_iso_ts(payload.ts)
    if not ts:
        raise HTTPException(status_code=400, detail="Invalid ts format")
    if ts > datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Future ts is not allowed")
    existing = location_status_store.get(payload.location_id)
    if existing:
        existing_ts = parse_iso_ts(existing.ts)
        if existing_ts and ts <= existing_ts:
            raise HTTPException(status_code=409, detail="Out-of-order ts update")
    status_code = derive_status_code(payload.status)
    record = LocationStatus(
        location_id=payload.location_id,
        ts=payload.ts,
        status=payload.status,
        status_code=status_code,
        remark=payload.remark,
    )
    location_status_store[payload.location_id] = record
    cache.invalidate_location_status()
    return record

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
        await ws.send_json({"type":"hello","ts":iso_now()})
        while True:
            # Keepalive ping; clients can ignore
            await ws.send_json({"type":"ping","ts":iso_now()})
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
    await hub.broadcast({"type":"event","payload":payload})
    return {"ok": True, "event": event}
