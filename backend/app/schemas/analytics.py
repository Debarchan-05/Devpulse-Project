from datetime import datetime

from pydantic import BaseModel


class ScoreBreakdown(BaseModel):
    coding: float
    project: float
    testing: float
    documentation: float
    activity: float
    diversity: float
    overall: float


class AnalyticsOverview(BaseModel):
    developer_score: float
    pulse_status: str
    metrics: ScoreBreakdown
    total_repositories: int
    total_stars: int
    top_languages: dict[str, int]
    # Change in overall_score compared to the previous snapshot, if one
    # exists. None the very first time a user syncs.
    score_change: float | None = None


class MetricSnapshotOut(BaseModel):
    created_at: datetime
    coding: float
    project: float
    testing: float
    documentation: float
    activity: float
    diversity: float
    overall: float


class LeaderboardEntry(BaseModel):
    rank: int
    percentile: float
    name: str
    overall_score: float
    is_you: bool = False


class LeaderboardOut(BaseModel):
    entries: list[LeaderboardEntry]
    your_rank: int | None = None
