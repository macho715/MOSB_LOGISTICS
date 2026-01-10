import { HeatmapLayer } from "@deck.gl/aggregation-layers";
import type { Layer } from "@deck.gl/core";
import { MaskExtension } from "@deck.gl/extensions";
import { ArcLayer, GeoJsonLayer, ScatterplotLayer, SolidPolygonLayer, TextLayer } from "@deck.gl/layers";
import DeckGL from "@deck.gl/react";
import { CanvasContext } from "@luma.gl/core";
import maplibregl from "maplibre-gl";
import { useEffect, useMemo, useRef, useState } from "react";

import { computeEtaWedges } from "../../lib/client-only/eta";
import { buildHeatPoints } from "../../lib/client-only/heatmap";
import { useClientOnlyStore } from "../../store/useClientOnlyStore";
import type { AnnotatedEvent } from "../../types/clientOnly";
import type { LocationStatus } from "../../types/logistics";

const DEFAULT_VIEW = {
    longitude: 54.45857,
    latitude: 24.328853,
    zoom: 9.6,
    pitch: 0,
    bearing: 0,
};

const MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

const LUMA_PATCH_KEY = "__mosbLumaMaxTextureGuard__";
if (typeof window !== "undefined" && !(window as any)[LUMA_PATCH_KEY]) {
    (window as any)[LUMA_PATCH_KEY] = true;
    if (
        CanvasContext.prototype &&
        typeof CanvasContext.prototype.getMaxDrawingBufferSize === "function"
    ) {
        const originalGetMax = CanvasContext.prototype.getMaxDrawingBufferSize;
        CanvasContext.prototype.getMaxDrawingBufferSize = function getMaxDrawingBufferSize() {
            const max = (this as any)?.device?.limits?.maxTextureDimension2D;
            if (max && Number.isFinite(max)) {
                return [max, max];
            }
            try {
                return originalGetMax.call(this);
            } catch {
                // Safe fallback when device limits are unavailable.
                return [4096, 4096];
            }
        };
    }
}

function nowMs(): number {
    return Date.now();
}

type ArcDatum = {
    leg_id: string;
    mode: string;
    source: [number, number];
    target: [number, number];
};

export default function ClientOnlyMap() {
    const geofences = useClientOnlyStore((s) => s.geofences);
    const ui = useClientOnlyStore((s) => s.ui);
    const locations = useClientOnlyStore((s) => s.locations);
    const legs = useClientOnlyStore((s) => s.legs);

    const events = useClientOnlyStore((s) =>
        s.eventIds
            .map((id) => s.eventsById[id])
            .filter((event): event is AnnotatedEvent => Boolean(event)),
    );
    const shipments = useClientOnlyStore((s) => Object.values(s.shipmentsByNo));
    const locationStatusById = useClientOnlyStore((s) => s.locationStatusById);
    const getEventsCountByLocation = useClientOnlyStore((s) => s.getEventsCountByLocation);

    const [isMapReady, setIsMapReady] = useState(false);
    const [viewState, setViewState] = useState(DEFAULT_VIEW);
    const [currentTimeMs, setCurrentTimeMs] = useState(nowMs());
    const mapContainerRef = useRef<HTMLDivElement | null>(null);
    const mapRef = useRef<maplibregl.Map | null>(null);

    const maskExt = useMemo(() => new MaskExtension(), []);

    // Update current time periodically for ETA calculations (every 10 seconds)
    useEffect(() => {
        const intervalId = setInterval(() => {
            setCurrentTimeMs(nowMs());
        }, 10000); // 10 seconds

        return () => clearInterval(intervalId);
    }, []);

    const sinceMs = useMemo(
        () => currentTimeMs - ui.hoursWindow * 60 * 60 * 1000,
        [currentTimeMs, ui.hoursWindow],
    );

    // Location별 이벤트 카운트 메모이제이션
    const eventsCountByLocation = useMemo(() => {
        const counts: Record<string, number> = {};
        locations.forEach((loc) => {
            counts[loc.location_id] = getEventsCountByLocation(loc.location_id, sinceMs);
        });
        return counts;
    }, [locations, sinceMs, getEventsCountByLocation, events]);

    const heatPoints = useMemo(
        () => buildHeatPoints(events, { sinceMs, eventType: ui.heatEventType, zoneId: "all" }),
        [events, sinceMs, ui.heatEventType],
    );

    const etaWedges = useMemo(
        () => computeEtaWedges(shipments, events, currentTimeMs),
        [shipments, events, currentTimeMs],
    );

    const arcs = useMemo<ArcDatum[]>(() => {
        if (!legs.length || !locations.length) return [];
        const locMap = new Map(locations.map((loc) => [loc.location_id, loc]));
        const result: ArcDatum[] = [];
        for (const leg of legs) {
            const from = locMap.get(leg.from_location_id);
            const to = locMap.get(leg.to_location_id);
            if (from && to) {
                result.push({
                    leg_id: leg.leg_id,
                    mode: leg.mode,
                    source: [from.lon, from.lat] as [number, number],
                    target: [to.lon, to.lat] as [number, number],
                });
            }
        }
        return result;
    }, [legs, locations]);

    useEffect(() => {
        const container = mapContainerRef.current;
        if (!container || mapRef.current) return;

        let active = true;
        const map = new maplibregl.Map({
            container,
            style: MAP_STYLE,
            center: [DEFAULT_VIEW.longitude, DEFAULT_VIEW.latitude],
            zoom: DEFAULT_VIEW.zoom,
            pitch: DEFAULT_VIEW.pitch,
            bearing: DEFAULT_VIEW.bearing,
        });

        mapRef.current = map;

        map.on("load", () => {
            if (active) {
                setIsMapReady(true);
                // Initialize viewState from MapLibre
                const center = map.getCenter();
                setViewState({
                    longitude: center.lng,
                    latitude: center.lat,
                    zoom: map.getZoom(),
                    pitch: map.getPitch(),
                    bearing: map.getBearing(),
                });
            }
        });

        // Sync DeckGL viewState with MapLibre on move
        // Note: 'move' event fires on all view changes (pan, zoom, pitch, bearing)
        // Use requestAnimationFrame to throttle updates and improve performance
        let rafId: number | null = null;
        const handleMove = () => {
            if (!active || !map) return;
            if (rafId !== null) return; // Skip if already scheduled

            rafId = requestAnimationFrame(() => {
                rafId = null;
                if (!active || !map) return;
                const center = map.getCenter();
                setViewState({
                    longitude: center.lng,
                    latitude: center.lat,
                    zoom: map.getZoom(),
                    pitch: map.getPitch(),
                    bearing: map.getBearing(),
                });
            });
        };

        map.on("move", handleMove);

        map.on("error", (e) => {
            console.error("MapLibre error:", e);
            if (active) setIsMapReady(false);
        });

        return () => {
            active = false;
            if (rafId !== null) {
                cancelAnimationFrame(rafId);
                rafId = null;
            }
            if (mapRef.current) {
                mapRef.current.off("move", handleMove);
                mapRef.current.remove();
                mapRef.current = null;
            }
            setIsMapReady(false);
        };
    }, []);

    const layers = useMemo(() => {
        const out: Layer[] = [];

        if (geofences) {
            if (ui.showGeofenceMask) {
                out.push(
                    new GeoJsonLayer({
                        id: "geofence-mask",
                        data: geofences as any,
                        operation: "mask",
                        extensions: [maskExt],
                    }),
                );
            }

            out.push(
                new GeoJsonLayer({
                    id: "geofence-outline",
                    data: geofences as any,
                    stroked: true,
                    filled: false,
                    lineWidthMinPixels: 2,
                    getLineColor: (f: any) => {
                        const kind = f.properties?.kind;
                        const colors: Record<string, [number, number, number, number]> = {
                            MOSB: [255, 80, 80, 200],
                            WH: [140, 90, 255, 200],
                            PORT: [0, 160, 255, 200],
                            BERTH: [0, 200, 255, 200],
                            SITE: [255, 120, 80, 200],
                        };
                        return colors[kind] || [200, 200, 200, 180];
                    },
                }),
            );
        }

        if (ui.showHeatmap && heatPoints.length > 0) {
            out.push(
                new HeatmapLayer({
                    id: "heatmap",
                    data: heatPoints,
                    getPosition: (d: any) => d.position,
                    getWeight: (d: any) => d.weight,
                    aggregation: "SUM",
                    radiusPixels: 30,
                    intensity: 1.0,
                    threshold: 0.05,
                    debounceTimeout: 500,
                    colorRange: [
                        [0, 0, 255, 0],
                        [0, 255, 255, 128],
                        [0, 255, 0, 192],
                        [255, 255, 0, 224],
                        [255, 0, 0, 255],
                    ],
                }),
            );
        }

        if (ui.showEta && etaWedges.length > 0) {
            out.push(
                new SolidPolygonLayer({
                    id: "eta-wedges",
                    data: etaWedges,
                    getPolygon: (d: any) => d.polygon,
                    extruded: true,
                    getElevation: (d: any) => d.elevation_m,
                    getFillColor: [255, 140, 0, 120],
                    getLineColor: [255, 140, 0, 200],
                    lineWidthMinPixels: 1,
                    pickable: false,
                }),
            );
        }

        if (arcs.length) {
            out.push(
                new ArcLayer({
                    id: "legs",
                    data: arcs,
                    getSourcePosition: (d: any) => d.source,
                    getTargetPosition: (d: any) => d.target,
                    getSourceColor: (d: any) =>
                        d.mode === "SEA" ? [0, 160, 255, 180] :
                            d.mode === "AIR" ? [255, 200, 80, 180] :
                                [120, 200, 120, 180],
                    getTargetColor: (d: any) =>
                        d.mode === "SEA" ? [0, 160, 255, 180] :
                            d.mode === "AIR" ? [255, 200, 80, 180] :
                                [120, 200, 120, 180],
                    getWidth: 2,
                    pickable: false,
                }),
            );
        }

        out.push(
            new ScatterplotLayer({
                id: "events",
                data: events,
                getPosition: (d: any) => d.position,
                getRadius: 30,
                radiusUnits: "meters",
                getFillColor: (d: any) => {
                    switch (d.event_type) {
                        case "enter":
                            return [0, 200, 0, 200];
                        case "exit":
                            return [220, 0, 0, 200];
                        default:
                            return [0, 120, 255, 160];
                    }
                },
                pickable: false,
                extensions: ui.showGeofenceMask && geofences ? [maskExt] : [],
                maskId: ui.showGeofenceMask && geofences ? "geofence-mask" : undefined,
            }),
        );

        if (locations.length) {
            out.push(
                new ScatterplotLayer({
                    id: "locations",
                    data: locations,
                    getPosition: (d: any) => [d.lon, d.lat],
                    getFillColor: (d: any) => {
                        const status = locationStatusById[d.location_id];
                        if (status) {
                            switch (status.status_code) {
                                case "CRITICAL":
                                    return [255, 0, 0, 220]; // 빨강
                                case "WARNING":
                                    return [255, 165, 0, 220]; // 주황
                                default:
                                    return [0, 128, 0, 220]; // 초록 (OK)
                            }
                        }
                        // Status 없을 때는 기존 type 기반 색상 사용
                        const m: Record<string, [number, number, number, number]> = {
                            MOSB: [255, 80, 80, 230],
                            WH: [140, 90, 255, 220],
                            PORT: [0, 160, 255, 220],
                            BERTH: [0, 200, 255, 220],
                            SITE: [255, 120, 80, 220],
                        };
                        return m[d.type] || [160, 160, 160, 200];
                    },
                    getRadius: (d: any) => {
                        const status = locationStatusById[d.location_id];
                        if (status) {
                            return 50 + status.occupancy_rate * 200; // 50-250 픽셀
                        }
                        return d.type === "MOSB" ? 260 : 200; // 기존 기본값
                    },
                    pickable: false,
                }),
            );

            out.push(
                new TextLayer({
                    id: "location-labels",
                    data: locations,
                    getPosition: (d: any) => [d.lon, d.lat],
                    getText: (d: any) => {
                        const status = locationStatusById[d.location_id];
                        const eventCount = eventsCountByLocation[d.location_id] || 0;

                        if (status) {
                            const pct = Math.round(status.occupancy_rate * 100);
                            return `${d.name}\n${pct}% (${status.status_code})\n${eventCount}건`;
                        }
                        return `${d.name}\n${eventCount}건`;
                    },
                    getSize: 12,
                    sizeUnits: "pixels",
                    getColor: (d: any) => {
                        const status = locationStatusById[d.location_id];
                        if (status?.status_code === "CRITICAL") {
                            return [255, 200, 200, 255]; // 빨간색 텍스트
                        }
                        return [220, 230, 240, 220]; // 기본 색상
                    },
                    getPixelOffset: [0, 14],
                    getTextAnchor: "middle",
                    getAlignmentBaseline: "top",
                    pickable: false,
                }),
            );
        }

        return out;
    }, [
        geofences,
        events,
        heatPoints,
        etaWedges,
        arcs,
        locations,
        locationStatusById,
        eventsCountByLocation,
        ui.showGeofenceMask,
        ui.showHeatmap,
        ui.showEta,
        maskExt,
    ]);

    // No-op handler for DeckGL controlled mode (controller={false} means MapLibre handles interactions)
    // This prevents potential warnings or edge cases when using viewState as a controlled prop
    const handleViewStateChange = () => {
        // View state changes are handled by MapLibre's 'move' event, not by DeckGL interactions
        // Since controller={false}, DeckGL won't generate viewState changes from user gestures
    };

    return (
        <div style={{ position: "relative", width: "100%", height: "calc(100vh - 120px)" }}>
            <div ref={mapContainerRef} style={{ position: "absolute", inset: 0 }} />
            {isMapReady && (
                <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
                    <DeckGL
                        viewState={viewState}
                        onViewStateChange={handleViewStateChange}
                        controller={false}
                        layers={layers}
                    />
                </div>
            )}
            <div
                style={{
                    position: "absolute",
                    inset: 0,
                    pointerEvents: "none",
                    background:
                        "radial-gradient(120% 120% at 20% 20%, rgba(255,255,255,0.06), rgba(0,0,0,0.15) 60%, rgba(0,0,0,0.4) 100%)",
                }}
            />
        </div>
    );
}
