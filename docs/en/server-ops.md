# Server check & restart script (Improved Version)

Use `start-servers.ps1` on Windows to check and restart the local dev
servers (Backend/Frontend). By default, it stops any listeners on ports
8000/3000 and starts the servers again.

**Improvements (2026-01-10)**:
- ✅ Auto-fix `next-env.d.ts` (removes invalid import, supports Windows/Unix line endings)
- ✅ Cache cleanup option (`-CleanCache`)
- ✅ Frontend server runs in new PowerShell window (logs visible)
- ✅ Auto-remove global `NODE_ENV=production`
- ✅ Auto-install `cross-env` if missing (checks both `package.json` and `node_modules`)
- ✅ Improved server status checking (port listening verification, waits up to 60 seconds)
- ✅ Backend Job scope isolation fix (proper environment variable passing)
- ✅ Enhanced port cleanup (also stops PowerShell Jobs, waits up to 5 seconds)
- ✅ Backend Job ID tracking and reporting (auto-generates shutdown commands)

## Usage

```powershell
# Start both servers (default)
.\start-servers.ps1

# Start backend only
.\start-servers.ps1 -BackendOnly

# Start frontend only (with cache cleanup)
.\start-servers.ps1 -FrontendOnly -CleanCache

# Start with cache cleanup
.\start-servers.ps1 -CleanCache

# Start without checking ports
.\start-servers.ps1 -SkipCheck
```

## Key Features

### 1. Auto File Fix
- Automatically removes invalid import from `next-env.d.ts`
- Supports Windows/Unix line endings, includes empty line cleanup
- Prevents JSX runtime errors

### 2. Cache Management
- `-CleanCache` option to automatically clean `.next` cache
- Useful for resolving build issues

### 3. Frontend Server Execution Improvement
- Runs in new PowerShell window for visible logs
- Auto-installs `cross-env` if missing (checks both `package.json` and `node_modules`)
- Auto-removes global `NODE_ENV=production`
- Auto-configures and validates environment variables

### 4. Backend Server Execution Improvement
- Fixed PowerShell Job scope isolation issue
- Proper `.env` file parsing and environment variable passing
- Backend Job ID tracking and reporting

### 5. Server Shutdown and Cleanup
- Automatically detects and stops processes using ports
- Also stops PowerShell Jobs (prevents orphaned processes)
- Waits for port release (up to 5 seconds with retry)
- Auto-generates and displays shutdown commands

### 6. Server Status Checking
- Verifies port listening status (waits up to 60 seconds)
- Notifies when server is ready
- Checks and reports Backend Job status
