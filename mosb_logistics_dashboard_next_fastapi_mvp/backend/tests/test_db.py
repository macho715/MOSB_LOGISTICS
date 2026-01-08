import os
import tempfile

from db import Database
from models import Event, Location


def test_db_connection():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test.db")
        db = Database(db_path, load_csv=False)
        locations = db.get_locations()
        assert isinstance(locations, list)
        db.close()


def test_db_get_locations():
    db = Database(":memory:", load_csv=False)
    db.conn.execute(
        """
        INSERT INTO locations (location_id, type, name, lat, lon)
        VALUES ('TEST_001', 'MOSB', 'Test Location', 24.328853, 54.458570)
        """
    )
    locations = db.get_locations()
    assert len(locations) > 0
    assert isinstance(locations[0], Location)
    db.close()


def test_db_get_events_with_since():
    db = Database(":memory:", load_csv=False)
    db.conn.execute(
        """
        INSERT INTO events (event_id, ts, shpt_no, status, location_id, lat, lon, remark)
        VALUES
        ('EV-001', '2026-01-01T00:00:00', 'SHPT-001', 'PLANNED', 'LOC-001', 24.0, 54.0, 'test'),
        ('EV-002', '2026-01-02T00:00:00', 'SHPT-001', 'IN_TRANSIT', 'LOC-002', 24.1, 54.1, 'test')
        """
    )
    events = db.get_events(since="2026-01-01T12:00:00")
    assert len(events) == 1
    assert events[0].event_id == "EV-002"
    db.close()


def test_db_append_event():
    db = Database(":memory:", load_csv=False)
    event = Event(
        event_id="EV-TEST",
        ts="2026-01-01T00:00:00",
        shpt_no="SHPT-TEST",
        status="PLANNED",
        location_id="LOC-TEST",
        lat=24.0,
        lon=54.0,
        remark="test",
    )
    db.append_event(event)
    events = db.get_events()
    assert len(events) == 1
    assert events[0].event_id == "EV-TEST"
    db.close()
