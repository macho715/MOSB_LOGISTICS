import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { buildGeofenceIndex, findZone, type GeoFenceIndex } from "../lib/client-only/geofence";
import type {
    AnnotatedEvent,
    ClientShipment,
    GeoFenceCollection,
    LiveEvent,
    ShipmentLeg,
} from "../types/clientOnly";
import type { Leg, Location, LocationMetric, LocationStatus } from "../types/logistics";

type UiState = {
    showGeofenceMask: boolean;
    showHeatmap: boolean;
    showEta: boolean;
    hoursWindow: number;
    heatEventType: "all" | "enter" | "exit" | "move" | "unknown";
};

type LocationStatusById = Record<string, LocationStatus>;
type LocationMetricsById = Record<string, LocationMetric>;

type ClientOnlyState = {
    geofences: GeoFenceCollection | null;
    geofenceIndex: GeoFenceIndex | null;
    locations: Location[];
    legs: Leg[];
    shipmentsByNo: Record<string, ClientShipment>;
    eventsById: Record<string, AnnotatedEvent>;
    eventIds: string[];
    lastZoneByKey: Record<string, string | null>;
    locationStatusById: LocationStatusById;
    locationMetricsById: LocationMetricsById;
    ui: UiState;

    setGeofences: (c: GeoFenceCollection) => void;
    setLocations: (locs: Location[]) => void;
    setLegs: (legs: Leg[]) => void;
    upsertShipments: (rows: ClientShipment[]) => void;
    ingestEvents: (rows: LiveEvent[]) => void;
    pruneOldEvents: (nowMs: number) => void;
    setUi: (patch: Partial<UiState>) => void;
    deriveShipmentsFromEvents: () => void;
    setLocationStatus: (items: LocationStatus[]) => void;
    upsertLocationStatus: (item: LocationStatus) => void;
    setLocationMetrics: (items: LocationMetric[]) => void;
    getEventsCountByLocation: (locationId: string, sinceMs: number) => number;
};

const MAX_EVENTS = 1000;

function tsToMs(ts: string | number): number {
    if (typeof ts === "number" && Number.isFinite(ts)) return ts;
    const ms = Date.parse(String(ts));
    return Number.isFinite(ms) ? ms : Date.now();
}

function clampInt(n: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, Math.trunc(n)));
}

function deriveKey(e: LiveEvent): string {
    return e.tracker_id ?? e.shpt_no ?? e.id;
}

export const useClientOnlyStore = create<ClientOnlyState>()(
    devtools((set, get) => ({
        geofences: null,
        geofenceIndex: null,
        locations: [],
        legs: [],
        shipmentsByNo: {},
        eventsById: {},
        eventIds: [],
        lastZoneByKey: {},
        locationStatusById: {},
        locationMetricsById: {},
        ui: {
            showGeofenceMask: true,
            showHeatmap: true,
            showEta: true,
            hoursWindow: 24,
            heatEventType: "all",
        },

        setGeofences: (c) => {
            set(
                {
                    geofences: c,
                    geofenceIndex: buildGeofenceIndex(c),
                },
                false,
                "setGeofences",
            );
            get().deriveShipmentsFromEvents();
        },

        setLocations: (locs) => {
            set({ locations: locs }, false, "setLocations");
            get().deriveShipmentsFromEvents();
        },

        setLegs: (legs) => {
            set({ legs }, false, "setLegs");
            get().deriveShipmentsFromEvents();
        },

        upsertShipments: (rows) => {
            const prev = get().shipmentsByNo;
            const next = { ...prev };
            for (const s of rows) {
                if (!s?.shpt_no) continue;
                next[s.shpt_no] = { ...prev[s.shpt_no], ...s };
            }
            set({ shipmentsByNo: next }, false, "upsertShipments");
        },

        ingestEvents: (rows) => {
            const { geofenceIndex, eventsById, eventIds, lastZoneByKey } = get();

            const nextEventsById = { ...eventsById };
            const nextEventIds = [...eventIds];
            const nextLastZoneByKey = { ...lastZoneByKey };

            for (const e of rows) {
                if (!e?.id || !e?.position) continue;
                if (nextEventsById[e.id]) continue;

                const ts_ms = tsToMs(e.ts);
                const zone = findZone(e.position, geofenceIndex);
                const key = deriveKey(e);

                const prevZone = nextLastZoneByKey[key] ?? null;
                const newZone = zone?.zone_id ?? null;

                // Event type classification logic:
                // - "enter": was outside (null) → now inside (non-null)
                // - "exit": was inside (non-null) → now outside (null)
                // - "move": zone-to-zone transition OR same zone movement
                // - "unknown": was outside (null) → still outside (null) - no geofence history
                const event_type =
                    prevZone === null && newZone !== null ? "enter" :
                        prevZone !== null && newZone === null ? "exit" :
                            prevZone !== null && newZone !== null ? "move" : // zone-to-zone OR same zone
                                "unknown"; // prevZone === null && newZone === null

                nextLastZoneByKey[key] = newZone;

                const annotated: AnnotatedEvent = {
                    ...e,
                    ts_ms,
                    zone_id: zone?.zone_id ?? null,
                    zone_kind: zone?.zone_kind ?? null,
                    event_type,
                    weight: clampInt(1, 1, 255),
                };

                nextEventsById[e.id] = annotated;
                nextEventIds.push(e.id);

                if (nextEventIds.length > MAX_EVENTS) {
                    const oldestId = nextEventIds.shift();
                    if (oldestId) delete nextEventsById[oldestId];
                }
            }

            set(
                {
                    eventsById: nextEventsById,
                    eventIds: nextEventIds,
                    lastZoneByKey: nextLastZoneByKey,
                },
                false,
                "ingestEvents",
            );
            get().deriveShipmentsFromEvents();
        },

        pruneOldEvents: (nowMs) => {
            const { ui, eventIds, eventsById } = get();
            const windowMs = ui.hoursWindow * 60 * 60 * 1000;
            const sinceMs = nowMs - windowMs;

            const nextIds: string[] = [];
            const nextById: Record<string, AnnotatedEvent> = {};

            for (const id of eventIds) {
                const e = eventsById[id];
                if (!e) continue;
                if (e.ts_ms < sinceMs) continue;
                nextIds.push(id);
                nextById[id] = e;
            }

            set({ eventIds: nextIds, eventsById: nextById }, false, "pruneOldEvents");
            get().deriveShipmentsFromEvents();
        },

        setUi: (patch) => set({ ui: { ...get().ui, ...patch } }, false, "setUi"),

        setLocationStatus: (items) => {
            const byId: LocationStatusById = {};
            for (const item of items) {
                if (item?.location_id) {
                    byId[item.location_id] = item;
                }
            }
            set({ locationStatusById: byId }, false, "setLocationStatus");
        },

        upsertLocationStatus: (item) => {
            if (!item?.location_id) return;
            const prev = get().locationStatusById;
            // Monotonic merge: only update if last_updated is newer (or missing)
            const prevItem = prev[item.location_id];
            if (prevItem) {
                try {
                    const prevMs = Date.parse(prevItem.last_updated);
                    const newMs = Date.parse(item.last_updated);
                    if (!Number.isFinite(newMs) || (Number.isFinite(prevMs) && newMs < prevMs)) {
                        return; // Skip older update
                    }
                    // Reject future timestamps (5s tolerance)
                    const nowMs = Date.now();
                    if (newMs > nowMs + 5000) {
                        return; // Skip future timestamp
                    }
                } catch {
                    // Invalid timestamp, skip
                    return;
                }
            }
            set(
                { locationStatusById: { ...prev, [item.location_id]: item } },
                false,
                "upsertLocationStatus",
            );
        },

        setLocationMetrics: (items) => {
            const byId: LocationMetricsById = {};
            for (const item of items) {
                if (item?.location_id) {
                    byId[item.location_id] = item;
                }
            }
            set({ locationMetricsById: byId }, false, "setLocationMetrics");
        },

        getEventsCountByLocation: (locationId, sinceMs) => {
            const { eventsById, eventIds } = get();
            let count = 0;
            for (const id of eventIds) {
                const event = eventsById[id];
                if (!event) continue;
                if (event.ts_ms < sinceMs) continue;
                if (event.meta?.location_id === locationId) {
                    count += 1;
                }
            }
            return count;
        },

        deriveShipmentsFromEvents: () => {
            const { eventsById, eventIds, legs, locations } = get();

            const latestByShipment = new Map<string, AnnotatedEvent>();
            for (let i = eventIds.length - 1; i >= 0; i -= 1) {
                const e = eventsById[eventIds[i]];
                if (!e?.shpt_no) continue;
                if (!latestByShipment.has(e.shpt_no)) {
                    latestByShipment.set(e.shpt_no, e);
                }
            }

            const locationMap = new Map(locations.map((loc) => [loc.location_id, loc]));

            const shipments: Record<string, ClientShipment> = {};
            for (const [shptNo, event] of latestByShipment.entries()) {
                const shipmentLegs: ShipmentLeg[] = legs
                    .filter((l) => l.shpt_no === shptNo)
                    .map((leg) => {
                        const fromLoc = locationMap.get(leg.from_location_id);
                        const toLoc = locationMap.get(leg.to_location_id);
                        const speedKph = leg.mode === "SEA" ? 25 : leg.mode === "AIR" ? 800 : 60;
                        return {
                            leg_id: leg.leg_id,
                            from: {
                                name: fromLoc?.name,
                                position: fromLoc ? ([fromLoc.lon, fromLoc.lat] as [number, number]) : [0, 0],
                            },
                            to: {
                                name: toLoc?.name,
                                position: toLoc ? ([toLoc.lon, toLoc.lat] as [number, number]) : [0, 0],
                            },
                            speed_kph: speedKph,
                            eta_planned: leg.planned_eta,
                        };
                    });

                shipments[shptNo] = {
                    shpt_no: shptNo,
                    status: (event.meta?.status as ClientShipment["status"]) || "IN_TRANSIT",
                    current_position: event.position,
                    speed_kph: shipmentLegs[0]?.speed_kph ?? 40,
                    legs: shipmentLegs,
                    updated_at: new Date(event.ts_ms).toISOString(),
                };
            }

            set({ shipmentsByNo: shipments }, false, "deriveShipmentsFromEvents");
        },
    })),
);
