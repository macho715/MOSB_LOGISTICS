# Server check & restart script

Use `start-servers.ps1` on Windows to check and restart the local dev
servers (Backend/Frontend). By default, it stops any listeners on ports
8000/3000 and starts the servers again.

## Usage

```powershell
# Start both servers (default)
.\start-servers.ps1

# Start backend only
.\start-servers.ps1 -BackendOnly

# Start frontend only
.\start-servers.ps1 -FrontendOnly

# Start without checking ports
.\start-servers.ps1 -SkipCheck
```
