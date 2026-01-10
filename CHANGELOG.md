# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Improved `start-servers.ps1` script** (2026-01-10)
  - Auto-fix `next-env.d.ts`: Automatically removes invalid `import "./.next/dev/types/routes.d.ts"` with improved regex handling (Windows/Unix line endings)
  - Cache cleanup option: `-CleanCache` parameter to clean `.next` cache
  - Frontend server runs in new PowerShell window: Visible logs and proper `cross-env` execution
  - Global `NODE_ENV=production` auto-detection and removal
  - Auto-install `cross-env` if missing: Checks both `package.json` and `node_modules` for proper detection
  - Improved server status checking: Uses `Get-NetTCPConnection` for better port detection
  - Enhanced `Check-Port` function: More reliable port detection using `Get-NetTCPConnection`
  - Backend Job scope isolation fix: Proper environment variable passing to PowerShell Jobs with explicit `.env` file parsing
  - Enhanced `Stop-ServerOnPort`: Now also stops related PowerShell Jobs, improved wait logic with timeout (max 5 seconds)
  - Backend Job ID tracking: Script-scoped variable for easy job management and shutdown commands
  - Better error handling: Improved regex patterns, empty line cleanup in `next-env.d.ts`, and graceful fallbacks
- **Phase 4.1: Client-Only Dashboard** (2026-01-10)
  - New route `/dashboard-client-only` with client-side geofence filtering, heatmap aggregation, and ETA calculation
  - Zustand-based state management (`useClientOnlyStore.ts`)
  - Geofence utilities with BBox pre-filtering for performance (`lib/client-only/geofence.ts`)
  - Heatmap aggregation with status-based weighting (`lib/client-only/heatmap.ts`)
  - ETA wedge calculation using great-circle distance (`lib/client-only/eta.ts`)
  - Batched WebSocket processing (500ms) for reduced React re-renders (`useBatchedClientOnlyWs.ts`)
  - Map component with MapLibre base and DeckGL overlay (`ClientOnlyMap.tsx`)
    - GeoJsonLayer for geofence visualization
    - ScatterplotLayer for event points (enter/exit color coding)
    - ArcLayer for legs visualization
    - TextLayer for location labels
    - HeatmapLayer for event density
    - SolidPolygonLayer for ETA wedges (3D)
  - Dashboard UI with KPI panel and layer toggles (`ClientOnlyDashboard.tsx`)
  - Geofence data placeholder (`public/data/geofence.json`)
  - Documentation:
    - `docs/Client-Only_Dashboard_Guide.md`: User and developer guide
    - `frontend/docs/client-only-geofence-guide.md`: Geofence data replacement guide
- Dependencies added:
  - `@deck.gl/aggregation-layers`: HeatmapLayer support
  - `@deck.gl/extensions`: MaskExtension for geofence masking
  - `@deck.gl/layers`: GeoJsonLayer support (includes GeoJsonLayer, no separate package needed)
  - `@turf/boolean-point-in-polygon`: Point-in-polygon testing
  - `@turf/helpers`: Turf.js helper functions
  - `zustand`: State management
  - `@types/geojson`: TypeScript types for GeoJSON
- `start-servers.ps1`: Windows PowerShell script for automated server management
  - Automatic port conflict detection and resolution
  - Environment variable auto-configuration
  - Support for Backend/Frontend selective startup
  - Options: `-BackendOnly`, `-FrontendOnly`, `-SkipCheck`
- `CHANGELOG.md`: Project change history tracking
- `docs/en/release-notes.md`: English release notes
- `docs/kr/release-notes.md`: Korean release notes
- `docs/en/server-ops.md`: Server operations guide (English)
- `docs/kr/server-ops.md`: Server operations guide (Korean)
- MapLibre CSS import in `_app.tsx` for proper map rendering

### Fixed
- **Fixed `next-env.d.ts` invalid import** (2026-01-10)
  - Removed `import "./.next/dev/types/routes.d.ts"` from `next-env.d.ts`
  - Prevents JSX runtime errors (`jsxDEV is not a function`)
  - Auto-fixed by improved `start-servers.ps1` script
- **Fixed `start-servers.ps1` frontend execution issues** (2026-01-10)
  - Changed from `Start-Job` to `Start-Process` with new PowerShell window
  - Ensures `cross-env` works correctly
  - Makes server logs visible for debugging
- **Fixed `start-servers.ps1` backend Job scope issues** (2026-01-10)
  - Fixed `Import-DotEnv` function not available in Job scope by inlining `.env` file parsing
  - Environment variables now properly passed to backend Job via explicit arguments
  - Backend Job ID properly tracked and reported for easier management
- **Improved `start-servers.ps1` reliability** (2026-01-10)
  - Better `cross-env` detection: Checks both `package.json` devDependencies and `node_modules` directory
  - Improved `Fix-NextEnvDts`: Handles edge cases with whitespace, multiple line endings, and consecutive empty lines
  - Enhanced port cleanup: Waits up to 5 seconds for port release, better process termination
  - PowerShell Jobs cleanup: `Stop-ServerOnPort` now also stops related Jobs, preventing orphaned processes
- TypeScript compilation errors in Client-Only Dashboard (2026-01-10)
  - Fixed `GeoJsonLayer` import path: `@deck.gl/geo-layers` → `@deck.gl/layers`
  - Fixed `GeoFenceIndex` import: moved from `types/clientOnly.ts` to `lib/client-only/geofence.ts`
  - Fixed `arcs` type guard: improved null filtering with explicit type predicate
- Removed unused dependency `@deck.gl/geo-layers` (2026-01-10)
  - `GeoJsonLayer` is imported from `@deck.gl/layers`, making `@deck.gl/geo-layers` unnecessary
  - Reduces bundle size by removing unused dependency
- Dashboard crash when user cache is empty on initial render
  - Changed `user.role` to `user?.role` (optional chaining) in `frontend/pages/index.tsx`
  - Prevents `TypeError: Cannot read property 'role' of null`
- Map container initialization error ("Container 'map' not found")
  - Changed from string ID to `useRef` for DOM element reference
  - Added proper dependency array with `user` in MapLibre useEffect
- WebGL context initialization error (`maxTextureDimension2D`)
  - Added `isMapReady` state to gate DeckGL rendering
  - MapLibre `load` event now triggers `isMapReady` instead of immediate setting
  - DeckGL only renders after MapLibre is fully loaded
- Map not displaying issue
  - Fixed MapLibre useEffect to depend on `user` state
  - Added MapLibre CSS import for proper canvas/controls rendering
- Add DuckDB connection recovery policy with reset/memory options

### Changed
- Updated `docs/Implementation_Progress.md` with Phase 4.1 Client-Only Dashboard implementation details
- Updated `AGENTS.md` to reflect Next.js 16.1.1 (was 14)
- Upgraded Next.js from `14.2.0` to `^16.1.1`
- Upgraded ESLint from `^8.0.0` to `^9.39.2`
- Upgraded `eslint-config-next` from `^14.2.0` to `^16.1.1`
- Improved MapLibre initialization logic with proper lifecycle management

### Removed
- `mosb_logistics_dashboard_next_fastapi_mvp/backend/Untitled-1.ini`: Debug file containing git diff (accidentally committed)

### Technical Details
- Git commit: `05a3fff` (previous)
- Files changed: Multiple (map initialization fixes, Next.js upgrade, debug file removal)
- All changes verified and tested
