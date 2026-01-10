import type { ShipmentStatus } from "./logistics";

export type LngLat = [number, number];

export type ZoneKind = "MOSB" | "SITE" | "WH" | "PORT" | "BERTH";

export type EventType = "enter" | "exit" | "move" | "unknown";

export interface GeoFenceProperties {
  id: string;
  kind: ZoneKind;
  name?: string;
}

export type GeoFenceGeometry =
  | { type: "Polygon"; coordinates: LngLat[][] }
  | { type: "MultiPolygon"; coordinates: LngLat[][][] };

export interface GeoFenceFeature {
  type: "Feature";
  properties: GeoFenceProperties;
  geometry: GeoFenceGeometry;
}

export interface GeoFenceCollection {
  type: "FeatureCollection";
  features: GeoFenceFeature[];
}

export interface LiveEvent {
  id: string;
  ts: string | number;
  position: LngLat;
  shpt_no?: string;
  tracker_id?: string;
  meta?: Record<string, unknown>;
}

export interface AnnotatedEvent extends LiveEvent {
  ts_ms: number;
  zone_id: string | null;
  zone_kind: ZoneKind | null;
  event_type: EventType;
  weight: number;
}

export interface ClientShipment {
  shpt_no: string;
  status?: ShipmentStatus;
  current_position?: LngLat;
  speed_kph?: number;
  legs?: ShipmentLeg[];
  updated_at?: string;
}

export interface ShipmentLeg {
  leg_id: string;
  from: { name?: string; position: LngLat };
  to: { name?: string; position: LngLat };
  speed_kph?: number;
  eta_planned?: string;
}

export interface HeatPoint {
  position: LngLat;
  weight: number;
}

export interface EtaWedge {
  id: string;
  shpt_no: string;
  position: LngLat;
  bearing_deg: number;
  uncertainty_m: number;
  polygon: LngLat[];
  elevation_m: number;
}
