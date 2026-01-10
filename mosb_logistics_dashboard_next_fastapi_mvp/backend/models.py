from pydantic import BaseModel, Field
from typing import Literal


class LogiBaseModel(BaseModel):
    """KR: 물류 도메인 기본 모델입니다. EN: Base model for logistics domain."""


class Location(LogiBaseModel):
    """KR: 위치 정보를 정의합니다. EN: Defines location details."""
    location_id: str
    type: Literal["MOSB", "SITE", "WH", "PORT", "BERTH"]
    name: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class Shipment(LogiBaseModel):
    """KR: 운송 정보를 정의합니다. EN: Defines shipment details."""
    shpt_no: str
    bl_no: str
    incoterm: str
    hs_code: str
    priority: Literal["HIGH", "MED", "LOW"]
    vendor: str


class Leg(LogiBaseModel):
    """KR: 운송 구간 정보를 정의합니다. EN: Defines shipment leg details."""
    leg_id: str
    shpt_no: str
    from_location_id: str
    to_location_id: str
    mode: Literal["ROAD", "SEA", "AIR"]
    planned_etd: str
    planned_eta: str


class EventCreate(LogiBaseModel):
    """KR: 이벤트 생성 요청 모델입니다. EN: Event creation request model."""
    shpt_no: str
    status: Literal["PLANNED", "IN_TRANSIT", "ARRIVED", "DELAYED", "HOLD"]
    location_id: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    remark: str = ""


class Event(EventCreate):
    """KR: 이벤트 응답 모델입니다. EN: Event response model."""
    event_id: str
    ts: str


class LocationStatusIn(LogiBaseModel):
    """KR: 위치 상태 입력 모델입니다. EN: Location status input model."""
    location_id: str
    ts: str
    occupancy_ratio: float = Field(..., ge=0, le=1)


class LocationStatusOut(LocationStatusIn):
    """KR: 위치 상태 응답 모델입니다. EN: Location status response model."""
    status_code: Literal["OK", "BUSY", "FULL"]


LocationStatus = LocationStatusOut
