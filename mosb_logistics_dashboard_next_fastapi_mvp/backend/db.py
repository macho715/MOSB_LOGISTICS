import os
from pathlib import Path
from typing import List, Optional

import duckdb

from models import Event, Leg, Location, Shipment


class Database:
    def __init__(self, db_path: Optional[str] = None, load_csv: bool = True):
        if db_path is None:
            env_path = os.getenv("LOGISTICS_DB_PATH")
            if env_path:
                db_path = env_path
            else:
                data_dir = os.getenv(
                    "DATA_DIR",
                    os.path.join(os.path.dirname(__file__), "data"),
                )
                db_path = os.path.join(data_dir, "logistics.db")

        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = duckdb.connect(db_path)
        self._init_schema()
        if load_csv:
            self._load_csv_data_if_needed()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                location_id VARCHAR PRIMARY KEY,
                type VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                lat DOUBLE NOT NULL,
                lon DOUBLE NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shipments (
                shpt_no VARCHAR PRIMARY KEY,
                bl_no VARCHAR,
                incoterm VARCHAR,
                hs_code VARCHAR,
                priority VARCHAR NOT NULL,
                vendor VARCHAR NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS legs (
                leg_id VARCHAR PRIMARY KEY,
                shpt_no VARCHAR NOT NULL,
                from_location_id VARCHAR NOT NULL,
                to_location_id VARCHAR NOT NULL,
                mode VARCHAR NOT NULL,
                planned_etd VARCHAR NOT NULL,
                planned_eta VARCHAR NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id VARCHAR PRIMARY KEY,
                ts VARCHAR NOT NULL,
                shpt_no VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                location_id VARCHAR NOT NULL,
                lat DOUBLE NOT NULL,
                lon DOUBLE NOT NULL,
                remark VARCHAR
            )
            """
        )

    def _load_csv_table(self, table: str, csv_path: str, select_sql: str) -> None:
        if not os.path.exists(csv_path):
            return
        count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count:
            return
        self.conn.execute(f"INSERT INTO {table} {select_sql}", [csv_path])

    def _load_csv_data_if_needed(self) -> None:
        data_dir = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
        read_csv_base = (
            "read_csv(?, delim=',', header=true, all_varchar=true, "
            "strict_mode=false, ignore_errors=true, null_padding=true)"
        )
        self._load_csv_table(
            "locations",
            os.path.join(data_dir, "locations.csv"),
            f"""
            SELECT location_id, type, name, CAST(lat AS DOUBLE), CAST(lon AS DOUBLE)
            FROM {read_csv_base}
            """,
        )
        self._load_csv_table(
            "shipments",
            os.path.join(data_dir, "shipments.csv"),
            f"SELECT * FROM {read_csv_base}",
        )
        self._load_csv_table(
            "legs",
            os.path.join(data_dir, "legs.csv"),
            f"SELECT * FROM {read_csv_base}",
        )
        self._load_csv_table(
            "events",
            os.path.join(data_dir, "events.csv"),
            f"""
            SELECT event_id, ts, shpt_no, status, location_id,
                   CAST(lat AS DOUBLE), CAST(lon AS DOUBLE), remark
            FROM {read_csv_base}
            """,
        )

    def _fetch_models(self, query: str, columns: list[str], model, params=None):
        rows = self.conn.execute(query, params or []).fetchall()
        return [model(**dict(zip(columns, row))) for row in rows]

    def get_locations(self) -> List[Location]:
        return self._fetch_models(
            "SELECT * FROM locations",
            ["location_id", "type", "name", "lat", "lon"],
            Location,
        )

    def get_shipments(self) -> List[Shipment]:
        return self._fetch_models(
            "SELECT * FROM shipments",
            ["shpt_no", "bl_no", "incoterm", "hs_code", "priority", "vendor"],
            Shipment,
        )

    def get_legs(self) -> List[Leg]:
        return self._fetch_models(
            "SELECT * FROM legs",
            [
                "leg_id",
                "shpt_no",
                "from_location_id",
                "to_location_id",
                "mode",
                "planned_etd",
                "planned_eta",
            ],
            Leg,
        )

    def get_events(self, since: Optional[str] = None) -> List[Event]:
        columns = [
            "event_id",
            "ts",
            "shpt_no",
            "status",
            "location_id",
            "lat",
            "lon",
            "remark",
        ]
        if since:
            return self._fetch_models(
                "SELECT * FROM events WHERE ts >= ? ORDER BY ts DESC",
                columns,
                Event,
                [since],
            )
        return self._fetch_models(
            "SELECT * FROM events ORDER BY ts DESC",
            columns,
            Event,
        )

    def append_event(self, event: Event) -> None:
        self.conn.execute(
            """
            INSERT INTO events (event_id, ts, shpt_no, status, location_id, lat, lon, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                event.event_id,
                event.ts,
                event.shpt_no,
                event.status,
                event.location_id,
                event.lat,
                event.lon,
                event.remark,
            ],
        )

    def close(self) -> None:
        self.conn.close()
