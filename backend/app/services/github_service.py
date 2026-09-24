from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import GitHubProfile, Repository


async def fetch_github(username: str, endpoint: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(f"{settings.github_api_url}{endpoint}", headers=headers)

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="GitHub user or repository was not found")
    if response.status_code == 403:
        raise HTTPException(status_code=429, detail="GitHub API rate limit reached")
    if response.is_error:
        raise HTTPException(status_code=502, detail="GitHub API request failed")
    return response.json()


def compute_repo_health(item: dict) -> float:
    """
    0-100 health score for a single repository, based only on fields
    already returned by GitHub's repo-list endpoint (no extra API calls
    needed). The rubric rewards discoverability and maintenance signals
    that matter to a recruiter skimming a GitHub profile:

        +20  has a description
        +20  has an OSS license attached
        +15  tagged with topics (up to 5 topics counted, 3 pts each)
        +15  bonus for community traction (stars, capped)
        -25  penalty if the repo is archived (no longer maintained)
    """
    score = 30.0
    if item.get("description"):
        score += 20
    if item.get("license"):
        score += 20
    topics = item.get("topics") or []
    if topics:
        score += min(len(topics) * 3, 15)
    score += min(item.get("stargazers_count", 0) * 0.5, 15)
    if item.get("archived"):
        score -= 25
    return round(max(0.0, min(score, 100.0)), 2)


def check_sync_cooldown(profile: GitHubProfile | None) -> None:
    if not profile or not profile.last_synced_at:
        return
    elapsed = (datetime.utcnow() - profile.last_synced_at).total_seconds()
    remaining = settings.sync_cooldown_seconds - elapsed
    if remaining > 0:
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {int(remaining)} more second(s) before syncing again.",
        )


async def sync_github_profile(db: Session, user_id: int, username: str) -> tuple[GitHubProfile, bool]:
    """Returns (profile, is_first_sync) -- the boolean is used by the
    badge engine to award the onboarding "First Pulse" badge exactly once."""
    profile = db.query(GitHubProfile).filter(GitHubProfile.user_id == user_id).first()
    check_sync_cooldown(profile)
    is_first_sync = profile is None

    profile_data = await fetch_github(username, f"/users/{username}")
    repos_data = await fetch_github(username, f"/users/{username}/repos?per_page=100&sort=updated")

    if not profile:
        profile = GitHubProfile(user_id=user_id)
        db.add(profile)

    profile.github_username = profile_data["login"]
    profile.avatar_url = profile_data.get("avatar_url")
    profile.profile_url = profile_data.get("html_url")
    profile.bio = profile_data.get("bio")
    profile.public_repos = profile_data.get("public_repos", 0)
    profile.followers = profile_data.get("followers", 0)
    profile.following = profile_data.get("following", 0)
    profile.last_synced_at = datetime.utcnow()

    existing = {r.github_repo_id: r for r in db.query(Repository).filter(Repository.user_id == user_id).all()}
    for item in repos_data:
        if item.get("fork"):
            continue
        repo_id = item["id"]
        repo = existing.get(repo_id)
        if not repo:
            repo = Repository(user_id=user_id, github_repo_id=repo_id)
            db.add(repo)
        repo.name = item["name"]
        repo.language = item.get("language")
        repo.stars = item.get("stargazers_count", 0)
        repo.forks = item.get("forks_count", 0)
        repo.description = item.get("description")
        repo.url = item["html_url"]
        repo.topics = item.get("topics") or []
        repo.has_license = bool(item.get("license"))
        repo.is_archived = bool(item.get("archived"))
        repo.open_issues = item.get("open_issues_count", 0)
        repo.repo_health_score = compute_repo_health(item)
        repo.updated_at_github = (
            datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
            if item.get("updated_at")
            else None
        )

    db.commit()
    db.refresh(profile)
    return profile, is_first_sync
