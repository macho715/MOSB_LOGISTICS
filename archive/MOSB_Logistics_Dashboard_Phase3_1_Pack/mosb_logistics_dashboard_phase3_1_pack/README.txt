MOSB Logistics Dashboard - Phase 3.1 Pack
Stack: Next.js 14 + React 18 + Deck.gl + MapLibre + FastAPI + WebSocket + DuckDB + TTLCache

Backend
  cd backend
  pip install -r requirements.txt
  copy .env.example .env   (optional)
  uvicorn main:app --reload --port 8000

Frontend
  cd frontend
  npm install
  copy .env.local.example .env.local
  npm run dev

Backend tests
  cd backend
  pytest -q -v
