import { useEffect } from "react";
import type { GeoFenceCollection } from "../types/clientOnly";
import { useClientOnlyStore } from "../store/useClientOnlyStore";

export function useClientOnlyGeofences(url = "/data/geofence.json") {
  const setGeofences = useClientOnlyStore((s) => s.setGeofences);
  const geofences = useClientOnlyStore((s) => s.geofences);

  useEffect(() => {
    if (geofences) return;

    let cancelled = false;

    (async () => {
      try {
        const res = await fetch(url, { cache: "no-store" });
        if (!res.ok) throw new Error(`Failed to load geofences: ${res.status}`);
        const json = (await res.json()) as GeoFenceCollection;
        if (cancelled) return;
        setGeofences(json);
      } catch (err) {
        console.error("Failed to load geofences:", err);
        if (!cancelled) {
          setGeofences({
            type: "FeatureCollection",
            features: [],
          });
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [url, geofences, setGeofences]);
}
