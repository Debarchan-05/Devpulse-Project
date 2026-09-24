# DevPulse — Frontend

A React + Tailwind CSS dashboard for the DevPulse FastAPI backend. Every
screen calls a real endpoint on the backend — there's no mock data.

## Design concept

DevPulse treats a GitHub profile like a vitals monitor treats a body: a
Pulse Score, a growth line instead of a single number, and a signature
heartbeat-line mark that "beats" in the sidebar. Dark "monitor screen"
background, a mono font (JetBrains Mono) for every number/score to feel
like a live readout, and three meaningful accent colors:

- **Pulse (coral-red)** — the score itself, live actions
- **Signal (gold)** — achievements/badges
- **Rank (violet)** — leaderboard/secondary data

## Stack

React 19 (Vite) · Tailwind CSS v4 · Recharts (radar + growth charts) ·
lucide-react (icons) · plain `fetch` for API calls — no extra HTTP or
state-management library needed for an app this size.

## Running it

1. **Start the DevPulse backend first** (see `../backend/README.md`). It
   needs to be reachable at `http://localhost:8000` — the backend's
   default CORS settings already allow `http://localhost:5173`
   (Vite's default port), so no backend changes are needed.

2. Install and run the frontend:
   ```bash
   npm install
   npm run dev
   ```
3. Open **http://localhost:5173**.

If your backend runs somewhere else, copy `.env.example` to `.env` and
change `VITE_API_BASE_URL`.

## What you can demo end-to-end

1. **Register / log in** — JWT stored in `localStorage`, attached to every
   request via `src/api/client.js`.
2. **Overview tab** — sync any public GitHub username; watch the Pulse
   Score, the 6-pillar radar chart, and the growth line chart populate
   from real data. Sync the same profile again later to see the growth
   line gain a second point.
3. **Repositories** — every synced repo with its own Health Score bar,
   sortable by stars/health/name.
4. **Achievements** — the full Pulse Badge catalog; earned badges light
   up in color, un-earned ones stay dimmed. A toast pops up the moment a
   new badge is earned during a sync.
5. **Leaderboard** — ranked live by the backend's SQL window-function
   query; toggle your own visibility with the opt-in/out control.
6. **AI Coach** — generate a career-analysis report or resume bullets
   (requires `OPENAI_API_KEY` set on the backend); past reports are
   listed below and expand inline.

## Project structure

```
src/
├── api/client.js          every backend call, in one place
├── context/
│   ├── AuthContext.jsx     token + current user
│   └── ToastContext.jsx    success/error toasts
├── components/             Sidebar, PulseMark, SyncForm, shared UI bits
├── pages/
│   ├── AuthScreen.jsx
│   ├── Dashboard.jsx        sidebar + active-tab switcher
│   ├── OverviewTab.jsx
│   ├── RepositoriesTab.jsx
│   ├── AchievementsTab.jsx
│   ├── LeaderboardTab.jsx
│   └── AICoachTab.jsx
└── lib/pulse.js             formatting + pulse-status color helpers
```

Each tab fetches its own data in a `useEffect` on mount — simple,
readable, and enough for a project this size. No router is used since
navigation is just five tabs in one dashboard (`useState` in
`Dashboard.jsx` tracks the active one).

## Building for production

```bash
npm run build
```
Outputs a static site to `dist/` — serve it with any static host, just
make sure `VITE_API_BASE_URL` points at wherever the backend actually runs.
