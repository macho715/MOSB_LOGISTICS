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

### Fixed
- Dashboard crash when user cache is empty on initial render
  - Changed `user.role` to `user?.role` (optional chaining) in `frontend/pages/index.tsx`
  - Prevents `TypeError: Cannot read property 'role' of null`
- Add DuckDB connection recovery policy with reset/memory options

### Changed
- Updated `docs/Implementation_Progress.md` with server management script and bug fix details

### Technical Details
- Git commit: `05a3fff`
- Files changed: 7 files (339 insertions, 1 deletion)
- All changes verified and tested
