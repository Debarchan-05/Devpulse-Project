from datetime import datetime

from pydantic import BaseModel

from app.schemas.achievements import BadgeOut
from app.schemas.analytics import ScoreBreakdown


class GitHubProfileOut(BaseModel):
    github_username: str
    avatar_url: str | None = None
    profile_url: str | None = None
    bio: str | None = None
    public_repos: int
    followers: int
    following: int
    last_synced_at: datetime | None = None

    model_config = {"from_attributes": True}


class RepositoryOut(BaseModel):
    id: int
    github_repo_id: int
    name: str
    language: str | None
    stars: int
    forks: int
    description: str | None
    url: str
    topics: list[str] | None = None
    has_license: bool
    is_archived: bool
    open_issues: int
    repo_health_score: float
    updated_at_github: datetime | None

    model_config = {"from_attributes": True}


class GitHubSyncRequest(BaseModel):
    username: str


class GitHubSyncResult(BaseModel):
    """
    Returned by POST /github/sync. Deliberately richer than "just the
    profile" -- syncing is the one action-heavy endpoint in this API, so
    it hands back everything that changed as a result: the refreshed
    profile, the freshly computed Pulse Score, and any badges earned in
    this sync (empty list if none).
    """

    profile: GitHubProfileOut
    scores: ScoreBreakdown
    new_badges: list[BadgeOut]
