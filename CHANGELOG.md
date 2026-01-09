# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
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
- Updated `docs/Implementation_Progress.md` with server management script and bug fix details
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
