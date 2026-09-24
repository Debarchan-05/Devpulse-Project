from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Repository, User
from app.schemas.analytics import AnalyticsOverview, LeaderboardEntry, LeaderboardOut, MetricSnapshotOut
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Read-only by design: this endpoint only reads the most recent Pulse
    snapshot, it never computes or writes a new one. Score calculation
    happens exactly once, as a side effect of POST /github/sync -- keeping
    GET requests side-effect-free is a core REST/HTTP convention worth
    knowing for your viva.
    """
    repos = db.scalars(select(Repository).where(Repository.user_id == current_user.id)).all()
    if not repos:
        raise HTTPException(status_code=400, detail="Sync a GitHub profile first")

    snapshot = analytics_service.get_latest_snapshot(db, current_user.id)
    if not snapshot:
        raise HTTPException(status_code=400, detail="Sync a GitHub profile first")

    scores = {
        "coding": snapshot.coding_score,
        "project": snapshot.project_score,
        "testing": snapshot.testing_score,
        "documentation": snapshot.documentation_score,
        "activity": snapshot.activity_score,
        "diversity": snapshot.diversity_score,
        "overall": snapshot.overall_score,
    }
    return AnalyticsOverview(
        developer_score=snapshot.overall_score,
        pulse_status=analytics_service.pulse_status(snapshot.overall_score),
        metrics=scores,
        total_repositories=len(repos),
        total_stars=sum(r.stars for r in repos),
        top_languages=analytics_service.get_language_counts(list(repos)),
        score_change=analytics_service.get_score_change(db, current_user.id),
    )


@router.get("/history", response_model=list[MetricSnapshotOut])
def history(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Oldest-to-newest Pulse Score snapshots -- feed this straight into a
    line chart on any frontend you build later."""
    snapshots = analytics_service.get_history(db, current_user.id, limit)
    return [
        MetricSnapshotOut(
            created_at=s.created_at,
            coding=s.coding_score,
            project=s.project_score,
            testing=s.testing_score,
            documentation=s.documentation_score,
            activity=s.activity_score,
            diversity=s.diversity_score,
            overall=s.overall_score,
        )
        for s in snapshots
    ]


@router.get("/leaderboard", response_model=LeaderboardOut)
def leaderboard(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Public ranking by latest Pulse Score, computed with SQL window
    functions (RANK() / ROW_NUMBER()) rather than in Python. Only users
    with leaderboard_opt_in=True are listed; toggle yours with
    PATCH /auth/leaderboard-preference.
    """
    entries, your_rank = analytics_service.get_leaderboard(db, limit, current_user.id)
    return LeaderboardOut(entries=[LeaderboardEntry(**e) for e in entries], your_rank=your_rank)
