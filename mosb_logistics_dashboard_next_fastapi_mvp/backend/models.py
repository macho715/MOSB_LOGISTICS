from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field, field_validator
from typing import Literal


class Location(BaseModel):
    location_id: str
    type: Literal["MOSB", "SITE", "WH", "PORT", "BERTH"]
    name: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class Shipment(BaseModel):
    shpt_no: str
    bl_no: str
    incoterm: str
    hs_code: str
    priority: Literal["HIGH", "MED", "LOW"]
    vendor: str


class Leg(BaseModel):
    leg_id: str
    shpt_no: str
    from_location_id: str
    to_location_id: str
    mode: Literal["ROAD", "SEA", "AIR"]
    planned_etd: str
    planned_eta: str


class EventCreate(BaseModel):
    shpt_no: str
    status: Literal["PLANNED", "IN_TRANSIT", "ARRIVED", "DELAYED", "HOLD"]
    location_id: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    remark: str = ""


class Event(EventCreate):
    event_id: str
    ts: str


class LocationStatusUpdate(BaseModel):
    """
    Input model for updating location status.
    status_code is optional and will be auto-derived from occupancy_rate if omitted.
    """

    location_id: str
    occupancy_rate: float = Field(..., ge=0.0, le=1.0)
    status_code: Literal["OK", "WARNING", "CRITICAL"] | None = None
    last_updated: str

    @field_validator("last_updated")
    @classmethod
    def validate_last_updated(cls, value: str) -> str:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("last_updated must be valid ISO8601 timestamp") from exc
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        if dt > now + timedelta(seconds=5):
            raise ValueError("last_updated cannot be in the future")
        return value


class LocationStatus(BaseModel):
    """
    Output model representing the real-time status of a location.
    status_code is always present (required) and matches the frontend TypeScript interface.
    This model is used for API responses and WebSocket broadcasts.
    """

    location_id: str
    occupancy_rate: float = Field(..., ge=0.0, le=1.0)
    status_code: Literal["OK", "WARNING", "CRITICAL"]
    last_updated: str

    @field_validator("last_updated")
    @classmethod
    def validate_last_updated(cls, value: str) -> str:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("last_updated must be valid ISO8601 timestamp") from exc
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        if dt > now + timedelta(seconds=5):
            raise ValueError("last_updated cannot be in the future")
        return value


def derive_status_code(occupancy_rate: float) -> Literal["OK", "WARNING", "CRITICAL"]:
    if occupancy_rate >= 0.9:
        return "CRITICAL"
    if occupancy_rate >= 0.7:
        return "WARNING"
    return "OK"
