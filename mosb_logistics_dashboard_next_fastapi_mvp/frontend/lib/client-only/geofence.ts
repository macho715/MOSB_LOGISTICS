import booleanPointInPolygon from "@turf/boolean-point-in-polygon";
import { point as turfPoint } from "@turf/helpers";
import type {
  GeoFenceCollection,
  GeoFenceFeature,
  LngLat,
  ZoneKind,
} from "../../types/clientOnly";

export type BBox = [minLng: number, minLat: number, maxLng: number, maxLat: number];

export interface GeoFenceIndexed {
  feature: GeoFenceFeature;
  bbox: BBox;
}

export interface GeoFenceIndex {
  items: GeoFenceIndexed[];
}

function isFiniteNumber(n: unknown): n is number {
  return typeof n === "number" && Number.isFinite(n);
}

function computeBBoxPolygon(coords: LngLat[][]): BBox {
  let minLng = Infinity;
  let minLat = Infinity;
  let maxLng = -Infinity;
  let maxLat = -Infinity;
  for (const ring of coords) {
    for (const [lng, lat] of ring) {
      if (!isFiniteNumber(lng) || !isFiniteNumber(lat)) continue;
      minLng = Math.min(minLng, lng);
      minLat = Math.min(minLat, lat);
      maxLng = Math.max(maxLng, lng);
      maxLat = Math.max(maxLat, lat);
    }
  }
  return [minLng, minLat, maxLng, maxLat];
}

function computeBBox(feature: GeoFenceFeature): BBox {
  const g = feature.geometry;
  if (g.type === "Polygon") return computeBBoxPolygon(g.coordinates);
  let minLng = Infinity;
  let minLat = Infinity;
  let maxLng = -Infinity;
  let maxLat = -Infinity;
  for (const poly of g.coordinates) {
    const [a, b, c, d] = computeBBoxPolygon(poly);
    minLng = Math.min(minLng, a);
    minLat = Math.min(minLat, b);
    maxLng = Math.max(maxLng, c);
    maxLat = Math.max(maxLat, d);
  }
  return [minLng, minLat, maxLng, maxLat];
}

export function buildGeofenceIndex(collection: GeoFenceCollection): GeoFenceIndex {
  return {
    items: collection.features.map((feature) => ({
      feature,
      bbox: computeBBox(feature),
    })),
  };
}

function inBBox([lng, lat]: LngLat, [minLng, minLat, maxLng, maxLat]: BBox): boolean {
  return lng >= minLng && lng <= maxLng && lat >= minLat && lat <= maxLat;
}

export function findZone(
  position: LngLat,
  index: GeoFenceIndex | null,
): { zone_id: string; zone_kind: ZoneKind } | null {
  if (!index) return null;

  const pt = turfPoint(position);

  for (const it of index.items) {
    if (!inBBox(position, it.bbox)) continue;
    if (booleanPointInPolygon(pt, it.feature as any)) {
      return {
        zone_id: it.feature.properties.id,
        zone_kind: it.feature.properties.kind,
      };
    }
  }
  return null;
}
