"""
The Pulse Scoring Engine.

Design principle (kept from the original project, and important for your
viva): the numeric score is always computed deterministically in plain
Python from data already sitting in MySQL. Nothing here calls an AI model.
That keeps the score reproducible, explainable, and cheap to run on every
sync -- the AI layer (app/services/ai_service.py) only *interprets* the
score afterwards, it never invents it.

Six pillars feed the overall Pulse Score:
    coding          - breadth of original repository work
    project         - repo count + average traction (stars)
    testing         - signals of testing discipline
    documentation   - how well repos are described
    activity        - repo count + total stars, as a proxy for momentum
    diversity       - "polyglot index": how evenly skills are spread across
                      languages, using Shannon entropy from information
                      theory (this is the differentiating idea vs. a plain
                      GitHub-stats clone)
"""

import math
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.models import DeveloperMetric, Repository, User

# Weights must sum to 1.0. Kept in one place so the rubric is easy to point
# to and defend in a viva.
WEIGHTS = {
    "coding": 0.25,
    "project": 0.20,
    "testing": 0.15,
    "documentation": 0.15,
    "activity": 0.15,
    "diversity": 0.10,
}

PULSE_STATUS_THRESHOLDS = [
    (85, "Peak Pulse"),
    (70, "Thriving"),
    (50, "Steady Growth"),
    (30, "Warming Up"),
    (0, "Just Getting Started"),
]


def compute_diversity_score(repos: list[Repository]) -> float:
    """
    "Polyglot Index" -- rewards developers whose skills are spread across
    several languages rather than concentrated in one.

    Uses Shannon entropy (H = -sum(p_i * log2(p_i))) to measure how evenly
    a user's repositories are distributed across languages, normalized
    against the maximum possible entropy for that many languages. A small
    bonus is added for the raw number of distinct languages, so a
    developer with 2 perfectly balanced languages doesn't outscore one
    who has genuinely worked across 6+.
    """
    languages = [r.language for r in repos if r.language]
    if not languages:
        return 0.0

    counts = Counter(languages)
    total = sum(counts.values())
    distinct = len(counts)

    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
    max_entropy = math.log2(distinct) if distinct > 1 else 1.0
    evenness = entropy / max_entropy if max_entropy > 0 else 0.0

    language_bonus = min(distinct * 5, 40)
    diversity = evenness * 60 + language_bonus
    return round(min(diversity, 100.0), 2)


def compute_scores(repos: list[Repository]) -> dict[str, float]:
    """Pure function: repos in, score breakdown out. No DB access, so it's
    trivial to unit test (see tests/test_analytics_service.py)."""
    total_repos = len(repos)
    total_stars = sum(repo.stars for repo in repos)
    avg_stars = min(total_stars / max(total_repos, 1), 20)

    coding = min(45 + total_repos * 4, 100)
    project = min(40 + total_repos * 5 + avg_stars, 100)
    activity = min(40 + total_repos * 5 + total_stars * 0.5, 100)
    testing = min(
        30
        + sum(
            1
            for r in repos
            if (r.description and "test" in r.description.lower())
            or (r.topics and any("test" in t.lower() for t in r.topics))
        )
        * 10,
        100,
    )
    documentation = min(35 + sum(1 for r in repos if r.description) * 5, 100)
    diversity = compute_diversity_score(repos)

    overall = round(
        coding * WEIGHTS["coding"]
        + project * WEIGHTS["project"]
        + testing * WEIGHTS["testing"]
        + documentation * WEIGHTS["documentation"]
        + activity * WEIGHTS["activity"]
        + diversity * WEIGHTS["diversity"],
        2,
    )

    return {
        "coding_score": round(coding, 2),
        "project_score": round(project, 2),
        "testing_score": round(testing, 2),
        "documentation_score": round(documentation, 2),
        "activity_score": round(activity, 2),
        "diversity_score": round(diversity, 2),
        "overall_score": overall,
    }


def pulse_status(overall_score: float) -> str:
    for threshold, label in PULSE_STATUS_THRESHOLDS:
        if overall_score >= threshold:
            return label
    return PULSE_STATUS_THRESHOLDS[-1][1]


def save_snapshot(db: Session, user_id: int, scores: dict[str, float]) -> DeveloperMetric:
    """Insert a brand-new Pulse reading. Deliberately never updates an
    existing row -- every sync is a new point on the growth chart."""
    snapshot = DeveloperMetric(user_id=user_id, **scores)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_latest_snapshot(db: Session, user_id: int) -> DeveloperMetric | None:
    return db.scalar(
        select(DeveloperMetric)
        .where(DeveloperMetric.user_id == user_id)
        .order_by(DeveloperMetric.created_at.desc())
        .limit(1)
    )


def get_score_change(db: Session, user_id: int) -> float | None:
    """Difference between the two most recent overall_score snapshots."""
    rows = db.scalars(
        select(DeveloperMetric)
        .where(DeveloperMetric.user_id == user_id)
        .order_by(DeveloperMetric.created_at.desc())
        .limit(2)
    ).all()
    if len(rows) < 2:
        return None
    return round(rows[0].overall_score - rows[1].overall_score, 2)


def get_history(db: Session, user_id: int, limit: int = 20) -> list[DeveloperMetric]:
    rows = db.scalars(
        select(DeveloperMetric)
        .where(DeveloperMetric.user_id == user_id)
        .order_by(DeveloperMetric.created_at.desc())
        .limit(limit)
    ).all()
    return list(reversed(rows))  # oldest -> newest, ready for a line chart


def get_language_counts(repos: list[Repository]) -> dict[str, int]:
    counter = Counter(repo.language for repo in repos if repo.language)
    return dict(counter.most_common())


def get_leaderboard(db: Session, limit: int, current_user_id: int) -> tuple[list[dict], int | None]:
    """
    Public leaderboard ranked by each user's MOST RECENT Pulse Score.

    This is written with SQL window functions rather than pulling
    everything into Python:
      1. ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC)
         picks out just the latest snapshot per user.
      2. RANK() OVER (ORDER BY overall_score DESC) then ranks those
         latest snapshots against each other, with ties sharing a rank.

    Both MySQL 8+ and modern SQLite (used in the test suite) support
    these, so the same query works in both environments.
    """
    latest_rn = (
        func.row_number()
        .over(partition_by=DeveloperMetric.user_id, order_by=DeveloperMetric.created_at.desc())
        .label("rn")
    )
    latest_subq = select(DeveloperMetric.user_id, DeveloperMetric.overall_score, latest_rn).subquery()

    rank_col = func.rank().over(order_by=latest_subq.c.overall_score.desc()).label("rank")

    ranked = (
        select(
            User.id.label("user_id"),
            User.name.label("name"),
            latest_subq.c.overall_score.label("overall_score"),
            rank_col,
        )
        .join(latest_subq, latest_subq.c.user_id == User.id)
        .where(latest_subq.c.rn == 1)
        .subquery()
    )

    total_ranked = db.scalar(select(func.count()).select_from(ranked)) or 0

    public_rows = db.execute(
        select(ranked)
        .join(User, User.id == ranked.c.user_id)
        .where(User.leaderboard_opt_in.is_(True))
        .order_by(ranked.c.rank.asc())
        .limit(limit)
    ).all()

    entries = [
        {
            "rank": row.rank,
            "percentile": round((1 - (row.rank - 1) / max(total_ranked, 1)) * 100, 1),
            "name": row.name,
            "overall_score": row.overall_score,
            "is_you": row.user_id == current_user_id,
        }
        for row in public_rows
    ]

    your_row = db.execute(select(ranked).where(ranked.c.user_id == current_user_id)).first()
    your_rank = your_row.rank if your_row else None

    return entries, your_rank
