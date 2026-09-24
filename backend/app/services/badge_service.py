"""
Pulse Badges -- a small, deterministic achievement engine.

Every rule below is a plain Python predicate over data you already have
(the latest score snapshot + synced repositories). Nothing here is
random or AI-generated, which keeps it fair, explainable, and instant.
Badges are catalog rows seeded automatically at app startup (see
app/db/init_db.py); this module only decides who has *earned* them and
records that in the user_badges table.
"""

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Badge, DeveloperMetric, Repository, UserBadge


@dataclass
class BadgeContext:
    is_first_sync: bool
    metric: DeveloperMetric
    repos: list[Repository]


def _rule_first_pulse(ctx: BadgeContext) -> bool:
    return ctx.is_first_sync


def _rule_prolific_builder(ctx: BadgeContext) -> bool:
    return len(ctx.repos) >= 10


def _rule_rising_star(ctx: BadgeContext) -> bool:
    return sum(r.stars for r in ctx.repos) >= 50


def _rule_polyglot(ctx: BadgeContext) -> bool:
    return len({r.language for r in ctx.repos if r.language}) >= 5


def _rule_quality_first(ctx: BadgeContext) -> bool:
    return ctx.metric.documentation_score >= 80


def _rule_test_champion(ctx: BadgeContext) -> bool:
    return ctx.metric.testing_score >= 80


def _rule_community_favorite(ctx: BadgeContext) -> bool:
    return any(r.stars >= 20 for r in ctx.repos)


def _rule_peak_pulse(ctx: BadgeContext) -> bool:
    return ctx.metric.overall_score >= 90


def _rule_well_rounded(ctx: BadgeContext) -> bool:
    scores = [
        ctx.metric.coding_score,
        ctx.metric.project_score,
        ctx.metric.testing_score,
        ctx.metric.documentation_score,
        ctx.metric.activity_score,
    ]
    return all(score >= 60 for score in scores)


# Maps a badge's `code` (as seeded in the DB) to the predicate that awards it.
BADGE_RULES: dict[str, Callable[[BadgeContext], bool]] = {
    "FIRST_PULSE": _rule_first_pulse,
    "PROLIFIC_BUILDER": _rule_prolific_builder,
    "RISING_STAR": _rule_rising_star,
    "POLYGLOT": _rule_polyglot,
    "QUALITY_FIRST": _rule_quality_first,
    "TEST_CHAMPION": _rule_test_champion,
    "COMMUNITY_FAVORITE": _rule_community_favorite,
    "PEAK_PULSE": _rule_peak_pulse,
    "WELL_ROUNDED": _rule_well_rounded,
}


def evaluate_and_award_badges(
    db: Session, user_id: int, metric: DeveloperMetric, repos: list[Repository], is_first_sync: bool
) -> list[Badge]:
    """Runs every rule, awards any newly-earned badges, and returns just
    the ones earned in THIS call (so the sync endpoint can show
    "you just unlocked ...")."""
    ctx = BadgeContext(is_first_sync=is_first_sync, metric=metric, repos=repos)

    already_earned_codes = set(
        db.scalars(
            select(Badge.code).join(UserBadge, UserBadge.badge_id == Badge.id).where(UserBadge.user_id == user_id)
        ).all()
    )

    all_badges = {b.code: b for b in db.scalars(select(Badge)).all()}

    newly_earned: list[Badge] = []
    for code, rule in BADGE_RULES.items():
        if code in already_earned_codes:
            continue
        badge = all_badges.get(code)
        if not badge:
            continue  # badge not seeded in this DB yet -- skip gracefully
        if rule(ctx):
            db.add(UserBadge(user_id=user_id, badge_id=badge.id))
            newly_earned.append(badge)

    if newly_earned:
        db.commit()

    return newly_earned


def get_badge_board(db: Session, user_id: int) -> list[dict]:
    """Full catalog, annotated with whether/when the current user earned each one."""
    earned = {
        ub.badge_id: ub.earned_at
        for ub in db.scalars(select(UserBadge).where(UserBadge.user_id == user_id)).all()
    }
    badges = db.scalars(select(Badge).order_by(Badge.id)).all()
    return [
        {
            "code": b.code,
            "name": b.name,
            "description": b.description,
            "icon": b.icon,
            "earned": b.id in earned,
            "earned_at": earned.get(b.id),
        }
        for b in badges
    ]
