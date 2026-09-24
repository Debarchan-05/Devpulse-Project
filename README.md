# DevPulse — Full Stack

A GitHub profile turned into a trackable "developer pulse": a growth-tracked
score, achievements, a leaderboard, and AI career coaching.

```
DevPulse-Full-Stack/
├── backend/     FastAPI + SQLAlchemy + MySQL API   → backend/README.md
└── frontend/    React + Tailwind CSS dashboard      → frontend/README.md
```

## Run both together (two terminals)

**Terminal 1 — backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then set DATABASE_URL to your MySQL instance + a JWT_SECRET
uvicorn app.main:app --reload
```
Tables and the badge catalog are created automatically on first boot — no
migration step. Full details, including the MySQL setup commands, are in
`backend/README.md`.

**Terminal 2 — frontend**
```bash
cd frontend
npm install
npm run dev
```

Then open **http://localhost:5173**, register an account, and sync any
public GitHub username (try your own, or a well-known one like `torvalds`)
to see the whole system light up — score, radar chart, growth history,
badges, and leaderboard rank, all computed live by the backend.

The backend's default CORS settings already allow `http://localhost:5173`,
so the two sides talk to each other with zero extra configuration.

## Optional: AI Coach tab

Set `OPENAI_API_KEY` in `backend/.env` to enable the two `/ai/*` endpoints
(career analysis + resume bullets). Everything else works fully without it.

## What to demo

1. Register → log in
2. Sync a GitHub username on the **Overview** tab → watch the Pulse Score,
   radar chart, and badge toasts appear
3. **Repositories** → sorted by per-repo Health Score
4. **Achievements** → the badge catalog, earned ones lit up
5. **Leaderboard** → ranked with a real SQL window-function query
6. **AI Coach** → generate a career report or resume bullets from the
   synced data

See `backend/README.md` for the architecture, database schema, scoring
formula, and full API reference — useful if you need to explain any part
of this project (e.g. in a viva or interview).
