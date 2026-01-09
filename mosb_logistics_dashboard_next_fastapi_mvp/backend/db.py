import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional

import duckdb

from models import Event, Leg, Location, Shipment


class Database:
    """DB 접근과 초기 데이터를 관리합니다. / Manages DB access and initial data."""

    def __init__(self, db_path: Optional[str] = None, load_csv: bool = True):
        """DB 연결과 초기 로드를 수행합니다. / Initialize DB connection and initial load."""
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

        self.conn = self._connect_with_recovery(db_path)
        self._init_schema()
        if load_csv:
            self._load_csv_data_if_needed()

    def _connect_with_recovery(self, db_path: str) -> duckdb.DuckDBPyConnection:
        recovery_policy = os.getenv("LOGISTICS_DB_RECOVERY", "fail").lower()
        try:
            return duckdb.connect(db_path)
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.error("DuckDB connection failed for %s: %s", db_path, exc)
            if recovery_policy == "fail":
                raise
            if recovery_policy == "memory":
                logger.warning(
                    "LOGISTICS_DB_RECOVERY=memory set; falling back to in-memory DuckDB.",
                )
                return duckdb.connect(":memory:")
            if recovery_policy == "reset":
                return self._reset_database(db_path, logger)
            logger.warning(
                "Unknown LOGISTICS_DB_RECOVERY=%s; re-raising connection error.",
                recovery_policy,
            )
            raise

    def _reset_database(
        self,
        db_path: str,
        logger: logging.Logger,
    ) -> duckdb.DuckDBPyConnection:
        if db_path == ":memory:":
            logger.warning("Reset requested for :memory: DB; reconnecting in-memory.")
            return duckdb.connect(":memory:")
        backup_path = f"{db_path}.bak"
        if os.path.exists(backup_path):
            logger.warning("Existing DuckDB backup found at %s; overwriting.", backup_path)
            os.remove(backup_path)
        if os.path.exists(db_path):
            shutil.move(db_path, backup_path)
            logger.warning("Backed up DuckDB file to %s before reset.", backup_path)
        else:
            logger.warning("No DuckDB file found at %s; creating a new database.", db_path)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        logger.info("Recreating DuckDB database at %s", db_path)
        return duckdb.connect(db_path)

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
        """위치 목록을 반환합니다. / Return the list of locations."""
        return self._fetch_models(
            "SELECT * FROM locations",
            ["location_id", "type", "name", "lat", "lon"],
            Location,
        )

    def get_shipments(self) -> List[Shipment]:
        """운송 목록을 반환합니다. / Return the list of shipments."""
        return self._fetch_models(
            "SELECT * FROM shipments",
            ["shpt_no", "bl_no", "incoterm", "hs_code", "priority", "vendor"],
            Shipment,
        )

    def get_legs(self) -> List[Leg]:
        """운송 구간 목록을 반환합니다. / Return the list of legs."""
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
        """이벤트 목록을 반환합니다. / Return the list of events."""
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
        """이벤트를 추가합니다. / Append an event."""
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
        """DB 연결을 닫습니다. / Close the DB connection."""
        self.conn.close()
