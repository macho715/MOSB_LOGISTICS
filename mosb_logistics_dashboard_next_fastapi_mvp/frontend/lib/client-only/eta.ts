import type { EtaWedge, LngLat, ClientShipment, AnnotatedEvent } from "../../types/clientOnly";

const EARTH_RADIUS_M = 6371000;

function toRad(d: number): number {
  return (d * Math.PI) / 180;
}

function toDeg(r: number): number {
  return (r * 180) / Math.PI;
}

export function bearingDeg(from: LngLat, to: LngLat): number {
  const [lng1, lat1] = from;
  const [lng2, lat2] = to;

  const phi1 = toRad(lat1);
  const phi2 = toRad(lat2);
  const deltaLambda = toRad(lng2 - lng1);

  const y = Math.sin(deltaLambda) * Math.cos(phi2);
  const x = Math.cos(phi1) * Math.sin(phi2) -
    Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLambda);

  const theta = Math.atan2(y, x);
  return (toDeg(theta) + 360) % 360;
}

export function destination(from: LngLat, bearingDegrees: number, distanceM: number): LngLat {
  const [lng, lat] = from;
  const phi1 = toRad(lat);
  const lambda1 = toRad(lng);
  const theta = toRad(bearingDegrees);
  const delta = distanceM / EARTH_RADIUS_M;

  const sinPhi2 = Math.sin(phi1) * Math.cos(delta) +
    Math.cos(phi1) * Math.sin(delta) * Math.cos(theta);
  const phi2 = Math.asin(sinPhi2);

  const y = Math.sin(theta) * Math.sin(delta) * Math.cos(phi1);
  const x = Math.cos(delta) - Math.sin(phi1) * Math.sin(phi2);
  const lambda2 = lambda1 + Math.atan2(y, x);

  return [(toDeg(lambda2) + 540) % 360 - 180, toDeg(phi2)];
}

export function buildWedgePolygon(
  pos: LngLat,
  bearing: number,
  radiusM: number,
  spreadDeg = 20,
  steps = 9,
): LngLat[] {
  const start = bearing - spreadDeg;
  const end = bearing + spreadDeg;

  const pts: LngLat[] = [];
  pts.push(pos);

  for (let i = 0; i < steps; i += 1) {
    const t = i / (steps - 1);
    const b = start + (end - start) * t;
    pts.push(destination(pos, b, radiusM));
  }

  pts.push(pos);
  return pts;
}

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

export function computeEtaWedges(
  shipments: ClientShipment[],
  _events: AnnotatedEvent[],
  _nowMs: number,
): EtaWedge[] {
  const out: EtaWedge[] = [];

  for (const s of shipments) {
    const pos = s.current_position;
    if (!pos) continue;

    const target = s.legs?.[0]?.to?.position;
    if (!target) continue;

    const brg = bearingDeg(pos, target);

    const speedKph = s.speed_kph ?? 40;
    const speedMps = (speedKph * 1000) / 3600;

    const status = s.status || "IN_TRANSIT";
    const baseUncMin =
      status === "DELAYED" ? 30 :
      status === "IN_TRANSIT" ? 15 :
      10;

    const uncertaintySec = baseUncMin * 60;
    const radiusM = clamp(speedMps * uncertaintySec, 200, 15000);
    const elevationM = clamp(baseUncMin * 30, 200, 2500);

    out.push({
      id: `eta-${s.shpt_no}`,
      shpt_no: s.shpt_no,
      position: pos,
      bearing_deg: brg,
      uncertainty_m: radiusM,
      polygon: buildWedgePolygon(pos, brg, radiusM, 20, 9),
      elevation_m: elevationM,
    });
  }

  return out;
}
