from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Repository, User
from app.schemas.github import GitHubProfileOut, GitHubSyncRequest, GitHubSyncResult, RepositoryOut
from app.services import analytics_service, badge_service
from app.services.github_service import sync_github_profile

router = APIRouter(prefix="/github", tags=["GitHub"])


@router.post("/sync", response_model=GitHubSyncResult)
async def sync_profile(
    payload: GitHubSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile, is_first_sync = await sync_github_profile(db, current_user.id, payload.username.strip())

    repos = db.scalars(select(Repository).where(Repository.user_id == current_user.id)).all()
    scores = analytics_service.compute_scores(list(repos))
    snapshot = analytics_service.save_snapshot(db, current_user.id, scores)
    new_badges = badge_service.evaluate_and_award_badges(
        db, current_user.id, snapshot, list(repos), is_first_sync
    )

    return GitHubSyncResult(
        profile=profile,
        scores={
            "coding": snapshot.coding_score,
            "project": snapshot.project_score,
            "testing": snapshot.testing_score,
            "documentation": snapshot.documentation_score,
            "activity": snapshot.activity_score,
            "diversity": snapshot.diversity_score,
            "overall": snapshot.overall_score,
        },
        new_badges=new_badges,
    )


@router.get("/profile", response_model=GitHubProfileOut)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.github_profile:
        raise HTTPException(status_code=404, detail="GitHub profile not synced yet")
    return current_user.github_profile


@router.get("/repositories", response_model=list[RepositoryOut])
def get_repositories(
    sort_by: str = "stars",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order_column = {
        "stars": Repository.stars.desc(),
        "health": Repository.repo_health_score.desc(),
        "name": Repository.name.asc(),
    }.get(sort_by, Repository.stars.desc())

    return db.scalars(
        select(Repository).where(Repository.user_id == current_user.id).order_by(order_column)
    ).all()
