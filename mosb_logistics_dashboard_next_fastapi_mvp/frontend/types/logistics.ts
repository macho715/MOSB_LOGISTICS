export type LocationType = "MOSB" | "SITE" | "WH" | "PORT" | "BERTH";
export type ShipmentStatus = "PLANNED" | "IN_TRANSIT" | "ARRIVED" | "DELAYED" | "HOLD";
export type TransportMode = "ROAD" | "SEA" | "AIR";

export interface Location {
  location_id: string;
  type: LocationType;
  name: string;
  lat: number;
  lon: number;
}

export interface Shipment {
  shpt_no: string;
  bl_no: string;
  incoterm: string;
  hs_code: string;
  priority: "HIGH" | "MED" | "LOW";
  vendor: string;
}

export interface Leg {
  leg_id: string;
  shpt_no: string;
  from_location_id: string;
  to_location_id: string;
  mode: TransportMode;
  planned_etd: string;
  planned_eta: string;
}

export interface Event {
  event_id: string;
  ts: string;
  shpt_no: string;
  status: ShipmentStatus;
  location_id: string;
  lat: number;
  lon: number;
  remark: string;
}
