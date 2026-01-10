from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

LocationType = Literal["MOSB", "SITE", "WH", "PORT", "BERTH"]
ShipmentStatus = Literal["PLANNED", "IN_TRANSIT", "ARRIVED", "DELAYED", "HOLD"]
TransportMode = Literal["ROAD", "SEA", "AIR"]

class Location(BaseModel):
    location_id: str
    type: LocationType
    name: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

class Shipment(BaseModel):
    shpt_no: str
    bl_no: str = ""
    incoterm: str = ""
    hs_code: str = ""
    priority: Literal["HIGH","MED","LOW"] = "LOW"
    vendor: str = ""

class Leg(BaseModel):
    leg_id: str
    shpt_no: str
    from_location_id: str
    to_location_id: str
    mode: TransportMode
    planned_etd: str = ""
    planned_eta: str = ""

class EventCreate(BaseModel):
    shpt_no: str
    status: ShipmentStatus
    location_id: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    remark: str = ""

class Event(EventCreate):
    event_id: str
    ts: str
