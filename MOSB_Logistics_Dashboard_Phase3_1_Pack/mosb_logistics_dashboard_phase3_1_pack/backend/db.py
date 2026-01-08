from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional, Sequence, Type, TypeVar

import duckdb

from models import Location, Shipment, Leg, Event, EventCreate

T = TypeVar("T")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS locations (
  location_id VARCHAR PRIMARY KEY,
  type VARCHAR,
  name VARCHAR,
  lat DOUBLE,
  lon DOUBLE
);

CREATE TABLE IF NOT EXISTS shipments (
  shpt_no VARCHAR PRIMARY KEY,
  bl_no VARCHAR,
  incoterm VARCHAR,
  hs_code VARCHAR,
  priority VARCHAR,
  vendor VARCHAR
);

CREATE TABLE IF NOT EXISTS legs (
  leg_id VARCHAR PRIMARY KEY,
  shpt_no VARCHAR,
  from_location_id VARCHAR,
  to_location_id VARCHAR,
  mode VARCHAR,
  planned_etd VARCHAR,
  planned_eta VARCHAR
);

CREATE TABLE IF NOT EXISTS events (
  event_id VARCHAR PRIMARY KEY,
  ts VARCHAR,
  shpt_no VARCHAR,
  status VARCHAR,
  location_id VARCHAR,
  lat DOUBLE,
  lon DOUBLE,
  remark VARCHAR
);
"""

@dataclass
class DB:
    path: str
    data_dir: str

    def __post_init__(self):
        self.con = duckdb.connect(self.path)
        self.con.execute(SCHEMA_SQL)
        self._load_csv_fallback()

    def _csv(self, name: str) -> str:
        return os.path.join(self.data_dir, f"{name}.csv")

    def _coltype(self, col: str) -> str:
        return {"lat":"DOUBLE","lon":"DOUBLE"}.get(col, "VARCHAR")

    def _load_csv_fallback(self) -> None:
        for table in ["locations","shipments","legs","events"]:
            csv_path = self._csv(table)
            if not os.path.exists(csv_path):
                continue
            self.con.execute(
                f"""
                CREATE OR REPLACE TEMP VIEW v_{table} AS
                SELECT * FROM read_csv('{csv_path}', all_varchar=true, strict_mode=false);
                """
            )
            cols = [c[1] for c in self.con.execute(f"PRAGMA table_info('{table}')").fetchall()]
            select_cols = ",".join([f"try_cast({c} AS {self._coltype(c)}) AS {c}" for c in cols])
            self.con.execute(
                f"""
                INSERT OR IGNORE INTO {table}
                SELECT {select_cols} FROM v_{table};
                """
            )

    def _fetch_models(self, sql: str, model: Type[T], params: Optional[Sequence]=None) -> List[T]:
        rows = self.con.execute(sql, params or []).fetchall()
        cols = [d[0] for d in self.con.description]
        out: List[T] = []
        for r in rows:
            out.append(model.model_validate(dict(zip(cols, r))))
        return out

    def get_locations(self) -> List[Location]:
        return self._fetch_models("SELECT * FROM locations ORDER BY type, name", Location)

    def get_shipments(self) -> List[Shipment]:
        return self._fetch_models("SELECT * FROM shipments ORDER BY shpt_no", Shipment)

    def get_legs(self) -> List[Leg]:
        return self._fetch_models("SELECT * FROM legs ORDER BY shpt_no, leg_id", Leg)

    def get_events(self, since: Optional[str]=None) -> List[Event]:
        if since:
            return self._fetch_models("SELECT * FROM events WHERE ts >= ? ORDER BY ts DESC", Event, [since])
        return self._fetch_models("SELECT * FROM events ORDER BY ts DESC", Event)

    def add_event(self, event_id: str, ts: str, payload: EventCreate) -> Event:
        self.con.execute(
            "INSERT OR REPLACE INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [event_id, ts, payload.shpt_no, payload.status, payload.location_id, payload.lat, payload.lon, payload.remark],
        )
        return Event(event_id=event_id, ts=ts, **payload.model_dump())
