import os, tempfile
from db import DB
from models import EventCreate

def test_db_add_event():
    with tempfile.TemporaryDirectory() as d:
        db_path = os.path.join(d, "logistics.db")
        db = DB(path=db_path, data_dir=d)
        e = db.add_event(
            event_id="EV-TEST",
            ts="2026-01-08T00:00:00+00:00",
            payload=EventCreate(shpt_no="S1", status="PLANNED", location_id="L1", lat=24.0, lon=54.0, remark="x"),
        )
        assert e.event_id == "EV-TEST"
        assert len(db.get_events()) == 1
