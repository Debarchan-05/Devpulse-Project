"""
Database bootstrap -- no migration tool required.

This project intentionally skips Alembic (or any migration framework) to
keep the learning curve focused on FastAPI + SQLAlchemy + MySQL. Instead:

  1. `Base.metadata.create_all(engine)` inspects every model in
     app/models/models.py and creates any table that doesn't exist yet in
     your MySQL database. It's idempotent -- safe to call on every
     startup, and it never touches tables that already exist.
  2. `seed_badges()` inserts the fixed catalog of Pulse Badges the first
     time the app runs against a fresh database, and does nothing on
     every run after that (it checks `code` before inserting).

Both run automatically in the FastAPI `lifespan` handler in app/main.py,
so `uvicorn app.main:app` is genuinely all you need after setting up
MySQL -- no separate "migrate" step.

Trade-off worth knowing for later: create_all() only CREATES missing
tables, it never ALTERs an existing one. If you change a model's columns
after the table already exists, you'll need to drop/recreate that table
(fine in development) or graduate to Alembic (a natural "V2" upgrade once
you're comfortable with the basics -- see PROJECT_GUIDE.md).
"""

from sqlalchemy.orm import Session

from app.db.session import Base, SessionLocal, engine
from app.models import Badge

# The full Pulse Badge catalog. Adding a new badge later is a two-step
# change: add a row here, then add a matching rule function in
# app/services/badge_service.py::BADGE_RULES.
BADGE_CATALOG = [
    {
        "code": "FIRST_PULSE",
        "name": "First Pulse",
        "description": "Synced a GitHub profile with DevPulse for the very first time.",
        "icon": "\U0001FAC0",
    },
    {
        "code": "PROLIFIC_BUILDER",
        "name": "Prolific Builder",
        "description": "Has 10 or more public repositories.",
        "icon": "\U0001F3D7\uFE0F",
    },
    {
        "code": "RISING_STAR",
        "name": "Rising Star",
        "description": "Repositories have earned 50+ stars combined.",
        "icon": "\u2B50",
    },
    {
        "code": "POLYGLOT",
        "name": "Full Spectrum",
        "description": "Has written projects in 5 or more programming languages.",
        "icon": "\U0001F308",
    },
    {
        "code": "QUALITY_FIRST",
        "name": "Quality First",
        "description": "Documentation score of 80 or higher.",
        "icon": "\U0001F4DA",
    },
    {
        "code": "TEST_CHAMPION",
        "name": "Test Champion",
        "description": "Testing score of 80 or higher.",
        "icon": "\U0001F9EA",
    },
    {
        "code": "COMMUNITY_FAVORITE",
        "name": "Community Favorite",
        "description": "At least one repository with 20+ stars.",
        "icon": "\U0001F91D",
    },
    {
        "code": "PEAK_PULSE",
        "name": "Peak Pulse",
        "description": "Reached an overall Pulse Score of 90 or higher.",
        "icon": "\U0001F525",
    },
    {
        "code": "WELL_ROUNDED",
        "name": "Well Rounded",
        "description": "Scored 60+ in every core dimension at once.",
        "icon": "\u2696\uFE0F",
    },
]


def seed_badges(db: Session) -> None:
    existing_codes = {code for (code,) in db.query(Badge.code).all()}
    for entry in BADGE_CATALOG:
        if entry["code"] not in existing_codes:
            db.add(Badge(**entry))
    db.commit()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_badges(db)
    finally:
        db.close()


if __name__ == "__main__":
    # Lets you run this by hand too: `python -m app.db.init_db`
    init_db()
    print("Database tables created and badge catalog seeded.")
