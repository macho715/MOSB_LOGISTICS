MOSB Logistics Dashboard (Sleek MVP)
Platform: Next.js (UI) + Deck.gl/MapLibre (Map) + FastAPI (Backend) + WebSocket (Events)

Why this (vs Streamlit)
- More polished UI (React/Next.js), full control over components, responsive layout, real-time websocket, enterprise-ready auth/RBAC later.

Run (local)
1) Backend
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000

2) Frontend
   cd frontend
   npm install
   cp .env.example .env.local
   npm run dev

Data
- backend/data/*.csv are demo sources (replace with DB / Sheets / Airtable / integrations).
- events.csv is append-only; WS demo endpoint /api/events/demo pushes synthetic events.

Important
- MIR/SHU/AGI/DAS in this demo are "reference points". Replace with your exact gate/jetty pins.
