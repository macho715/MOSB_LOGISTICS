from typing import Literal

from pydantic import BaseModel, Field


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
    """KR: 위치 상태 업데이트 요청입니다. EN: Location status update request."""

    location_id: str
    ts: str
    status: Literal["OK", "WARN", "CRITICAL"]
    status_code: str | None = None
    remark: str = ""


class LocationStatus(BaseModel):
    """KR: 위치 상태 응답 모델입니다. EN: Location status response model."""

    location_id: str
    ts: str
    status: Literal["OK", "WARN", "CRITICAL"]
    status_code: Literal["GREEN", "AMBER", "RED"]
    remark: str = ""
