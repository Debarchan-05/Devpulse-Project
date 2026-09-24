# DevPulse API

**A FastAPI + MySQL backend that turns any GitHub profile into a living
"developer pulse" — a growth-tracked score, an achievement board, a public
leaderboard, and AI-assisted career feedback.**

Built as a B.Tech final-year project to demonstrate real backend engineering:
relational schema design, authentication, a deterministic scoring engine,
SQL window-function analytics, and a thin AI integration layer — all in
plain FastAPI + SQLAlchemy, no black-box frameworks.

---

## Why this project is different

Most "GitHub analyzer" student projects fetch a profile, show some stars,
and stop there. DevPulse treats a developer profile like a **health
tracker treats a body** — one reading isn't the story, the trend is:

| Feature | What makes it non-trivial |
|---|---|
| **Pulse Score history** | Every sync writes a new snapshot row instead of overwriting one. `GET /analytics/overview` is a pure read — score calculation only ever happens as a side effect of `POST /github/sync`, following proper REST semantics. |
| **Polyglot Index** | A 6th scoring dimension computed with **Shannon entropy** from information theory — rewards developers whose skills are evenly spread across languages, not just developers who happen to know many. |
| **Repo Health Score** | Each repository gets its own 0–100 score from license presence, description quality, topic tagging, maintenance state, and traction — computed for free from data GitHub already returns, no extra API calls. |
| **Pulse Badges** | A rule-based achievement engine (9 badges) evaluated in pure Python — deterministic, instant, and fully unit-tested. |
| **Public Leaderboard** | Ranked with real SQL **window functions** (`ROW_NUMBER()` + `RANK()`), not Python sorting — the kind of query interviewers actually ask about. |
| **AI Resume Bullets** | A second, narrower AI feature (separate from the general career report) that turns your strongest repos into ATS-ready resume bullets in a chosen tone. |
| **Sync cooldown** | A simple database-only rate limiter (no Redis) that protects your GitHub API quota. |

---

## Tech stack

- **FastAPI** — routing, dependency injection, request/response validation
- **SQLAlchemy 2.0** (typed `Mapped[]` models) — ORM + raw window-function queries
- **MySQL 8** — primary datastore, via `PyMySQL` (pure Python driver, no compiler/toolchain needed)
- **PyJWT** + **pwdlib (argon2)** — stateless auth with properly hashed passwords
- **httpx** — async calls to the GitHub REST API
- **OpenAI SDK** — optional AI career analysis + resume bullet generation
- **pytest** — 17 tests covering the scoring engine, badge rules, and full API flows

No Docker, no Alembic, no Redis, no Celery — intentionally. Everything
here is plain enough to explain line-by-line in a viva, and the
[Extending this project](#extending-this-project) section below tells you
exactly where each of those would plug in later.

---

## Project structure

```
app/
├── main.py                 FastAPI app, CORS, startup hook
├── core/
│   ├── config.py            typed settings loaded from .env
│   └── security.py          JWT issuing/verification, password hashing
├── db/
│   ├── session.py            SQLAlchemy engine/session
│   └── init_db.py            creates tables + seeds badge catalog (no Alembic)
├── models/models.py          7 SQLAlchemy models (see schema below)
├── schemas/                  Pydantic request/response models, one file per feature
├── services/                 all business logic — kept OUT of the endpoints
│   ├── github_service.py      talks to GitHub, computes repo health, sync cooldown
│   ├── analytics_service.py   the scoring engine + leaderboard SQL
│   ├── badge_service.py       achievement rule engine
│   └── ai_service.py          OpenAI prompts for career report + resume bullets
└── api/v1/endpoints/          thin route handlers: validate → call a service → return
    ├── auth.py, github.py, analytics.py, achievements.py, ai.py
tests/                        pytest suite (unit + full API integration, SQLite-backed)
```

The **endpoints never contain business logic** — they parse the request,
call a function in `services/`, and shape the response. That separation is
deliberate and is the single most important pattern to be able to explain
in your viva: it's what makes each service function unit-testable without
spinning up the whole app (see `tests/test_analytics_service.py` and
`tests/test_badge_rules.py`, which test the scoring/badge logic with zero
HTTP requests or database calls at all).

---

## Database schema

```
users               1───1  github_profiles
  │                          │
  │ 1                        │ 1
  │                          │
  N                          N
repositories ◄──── (per user) ──────► developer_metrics (score history)
  │
  N
  │
badges ◄──N:N──► user_badges

users 1───N ai_reports
```

- **`developer_metrics`** is a *history* table, not a single row per user —
  each sync appends a snapshot, which is what powers `/analytics/history`.
- **`repositories.topics`** uses MySQL's native **JSON column type** to
  store a list of GitHub topic tags, avoiding an unnecessary join table.
- **`badges`** is small reference/catalog data seeded once at startup;
  **`user_badges`** records who earned what, and when.

---

## Getting started

### 1. Install MySQL and create a database

```sql
CREATE DATABASE devpulse CHARACTER SET utf8mb4;
CREATE USER 'devpulse'@'localhost' IDENTIFIED BY 'devpulse';
GRANT ALL PRIVILEGES ON devpulse.* TO 'devpulse'@'localhost';
FLUSH PRIVILEGES;
```

(Any MySQL 8.x install works — locally installed, XAMPP/WAMP, or a free
cloud instance like PlanetScale/Railway/Aiven. Just point `DATABASE_URL`
at it in step 3.)

### 2. Install Python dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:
- `DATABASE_URL` — your MySQL connection string
- `JWT_SECRET` — any long random string
- `GITHUB_TOKEN` — optional, but recommended (GitHub allows only 60
  unauthenticated API requests/hour vs. 5,000 with a
  [personal access token](https://github.com/settings/tokens), no scopes needed for public data)
- `OPENAI_API_KEY` — only needed for the two `/ai/*` endpoints

### 4. Run it

```bash
uvicorn app.main:app --reload
```

That's it — **no separate migration step**. On startup, `app/db/init_db.py`
calls `Base.metadata.create_all()` (creates any missing tables) and seeds
the badge catalog if it's empty. Both are safe to run every time the app
starts.

Open **http://localhost:8000/docs** for interactive Swagger UI — the
fastest way to try every endpoint without writing a single line of
frontend code.

---

## API reference

All routes are prefixed with `/api/v1`. Authenticated routes expect
`Authorization: Bearer <token>`.

| Method & path | Description |
|---|---|
| `POST /auth/register` | Create an account |
| `POST /auth/login` | OAuth2 password flow → JWT access token |
| `GET /auth/me` | Current user |
| `PATCH /auth/leaderboard-preference` | Opt in/out of the public leaderboard |
| `POST /github/sync` | Fetch + store GitHub profile & repos, compute a new Pulse snapshot, award any new badges |
| `GET /github/profile` | Stored GitHub profile |
| `GET /github/repositories?sort_by=stars\|health\|name` | Synced repos with per-repo health scores |
| `GET /analytics/overview` | Latest Pulse Score, pulse status label, score change since last sync |
| `GET /analytics/history?limit=20` | Score snapshots over time, oldest → newest |
| `GET /analytics/leaderboard?limit=20` | Public ranking via SQL window functions |
| `GET /achievements` | Full badge catalog, flagged with earned/unearned |
| `POST /ai/career-analysis` | AI strengths/weaknesses/roadmap report for a target role |
| `POST /ai/resume-bullets` | AI-generated resume bullet points in a chosen tone |
| `GET /ai/reports` | History of generated AI reports |
| `GET /health` | Liveness check |

---

## The scoring engine, in plain terms

Six pillars are combined into one **overall Pulse Score (0–100)**:

| Pillar | Weight | Signal |
|---|---|---|
| Coding | 25% | breadth of original repository work |
| Project | 20% | repo count + average community traction |
| Testing | 15% | descriptions/topics mentioning tests |
| Documentation | 15% | how many repos have a real description |
| Activity | 15% | repo count + total stars, as a momentum proxy |
| Diversity | 10% | **Polyglot Index** — Shannon entropy of your language mix |

The score maps to a friendly status label:

`Peak Pulse (85+)` → `Thriving (70+)` → `Steady Growth (50+)` →
`Warming Up (30+)` → `Just Getting Started`

Everything here is a **pure, deterministic function of data already in
MySQL** (`app/services/analytics_service.py::compute_scores`) — no AI
model decides your score, which keeps it reproducible and fair. AI is only
used *afterwards*, to interpret the score into human career advice.

### Pulse Badges

| Badge | Rule |
|---|---|
| First Pulse | First successful sync |
| Prolific Builder | 10+ repositories |
| Rising Star | 50+ total stars |
| Full Spectrum | 5+ distinct languages |
| Quality First | Documentation score ≥ 80 |
| Test Champion | Testing score ≥ 80 |
| Community Favorite | Any single repo with 20+ stars |
| Peak Pulse | Overall score ≥ 90 |
| Well Rounded | All five base pillars ≥ 60 at once |

---

## Running the tests

```bash
pytest -v
```

17 tests, no MySQL server required — the suite points `DATABASE_URL` at a
throwaway SQLite file (SQLite 3.25+ supports the same window functions
used in the real leaderboard query, so the logic is genuinely exercised,
not mocked away). Includes:
- pure unit tests of the scoring formulas and every badge rule
- a full integration test that registers a user, mocks a GitHub sync,
  and checks the resulting score, badges, repo health ranking, and
  leaderboard placement

---

## Extending this project

Good "V2" ideas to mention if asked what you'd do next, and roughly where
each would go:

- **Alembic** for versioned schema migrations, once `create_all()`'s
  "can't alter existing tables" limitation starts to hurt — replaces
  `app/db/init_db.py`.
- **Redis** to replace the DB-column sync cooldown with a proper
  rate limiter, and to cache `/analytics/leaderboard`.
- **Celery / background jobs** for a scheduled "resync everyone nightly"
  task instead of manual sync.
- **WebSockets** to push a live notification the instant a badge is earned.
- **Docker** to package the API + MySQL for one-command deployment once
  you're comfortable with the manual setup above.

---

## Deploying it

There's no Docker layer here, so deployment is just "run a Python app
with a MySQL connection string" — works as-is on Railway, Render,
PythonAnywhere, an EC2/VPS box, or any host that gives you a Python
runtime + a MySQL add-on:

1. Provision a MySQL 8 database (most platforms offer one as an add-on).
2. Set the environment variables from `.env.example` in the platform's
   dashboard (`DATABASE_URL` pointing at the provisioned MySQL instance).
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Tables and the badge catalog are created automatically on first boot.
