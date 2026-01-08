from __future__ import annotations

import csv
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from cache import CacheManager, cache_response
from db import DB
from models import Location, Shipment, Leg, Event, EventCreate

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
LOGISTICS_DB_PATH = os.getenv("LOGISTICS_DB_PATH", os.path.join(DATA_DIR, "logistics.db"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")
WS_PING_INTERVAL = int(os.getenv("WS_PING_INTERVAL", "10"))

db = DB(path=LOGISTICS_DB_PATH, data_dir=DATA_DIR)
cache = CacheManager()

app = FastAPI(title="MOSB Logistics Live API", version="0.3.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def append_event_csv(event: Event) -> None:
    path = os.path.join(DATA_DIR, "events.csv")
    exists = os.path.exists(path)
    fieldnames = ["event_id","ts","shpt_no","status","location_id","lat","lon","remark"]
    with open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            w.writeheader()
        w.writerow({k: getattr(event, k) for k in fieldnames})

@cache_response(cache.locations)
def get_locations_cached() -> List[Location]:
    return db.get_locations()

@cache_response(cache.shipments)
def get_shipments_cached() -> List[Shipment]:
    return db.get_shipments()

@cache_response(cache.legs)
def get_legs_cached() -> List[Leg]:
    return db.get_legs()

@cache_response(cache.events)
def get_events_cached(since: Optional[str]=None) -> List[Event]:
    return db.get_events(since=since)

@app.get("/api/locations", response_model=List[Location])
def api_locations():
    return get_locations_cached()

@app.get("/api/shipments", response_model=List[Shipment])
def api_shipments():
    return get_shipments_cached()

@app.get("/api/legs", response_model=List[Leg])
def api_legs():
    return get_legs_cached()

@app.get("/api/events", response_model=List[Event])
def api_events(since: Optional[str] = None):
    return get_events_cached(since=since)

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

    async def broadcast(self, msg: dict):
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
        await ws.send_json({"type":"hello","ts":iso_now()})
        import asyncio
        while True:
            await ws.send_json({"type":"ping","ts":iso_now()})
            await asyncio.sleep(WS_PING_INTERVAL)
    except WebSocketDisconnect:
        hub.disconnect(ws)

@app.post("/api/events", response_model=Event)
async def api_create_event(payload: EventCreate):
    event_id = f"EV-{uuid.uuid4().hex[:8]}"
    ts = iso_now()
    try:
        event = db.add_event(event_id=event_id, ts=ts, payload=payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    cache.invalidate_events()
    append_event_csv(event)

    await hub.broadcast({"type":"event","payload":event.model_dump()})
    return event

@app.post("/api/events/demo", response_model=Event)
async def api_demo_event():
    payload = EventCreate(
        shpt_no="SHPT-AGI-0001",
        status="IN_TRANSIT",
        location_id="MOSB_ESNAAD",
        lat=24.328853,
        lon=54.45857,
        remark="Demo tick",
    )
    return await api_create_event(payload)
