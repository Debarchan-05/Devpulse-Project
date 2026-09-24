from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))

    # Whether this user's latest Pulse Score can appear on the public
    # /analytics/leaderboard endpoint. Defaults to True since DevPulse is
    # meant to work like a public developer-portfolio score, but anyone
    # can opt out via PATCH /auth/leaderboard-preference.
    leaderboard_opt_in: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    github_profile: Mapped["GitHubProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    repositories: Mapped[list["Repository"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    # One user has MANY metric snapshots over time -- every successful
    # GitHub sync writes a new row here. That history is what powers the
    # growth chart in /analytics/history and the score_change field in
    # /analytics/overview.
    metric_snapshots: Mapped[list["DeveloperMetric"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", order_by="DeveloperMetric.created_at"
    )
    ai_reports: Mapped[list["AIReport"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    badges: Mapped[list["UserBadge"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class GitHubProfile(Base):
    __tablename__ = "github_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    github_username: Mapped[str] = mapped_column(String(100), index=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_repos: Mapped[int] = mapped_column(Integer, default=0)
    followers: Mapped[int] = mapped_column(Integer, default=0)
    following: Mapped[int] = mapped_column(Integer, default=0)

    # Used to enforce SYNC_COOLDOWN_SECONDS -- a simple, DB-only rate
    # limiter so one user spamming /github/sync can't burn through your
    # GitHub API quota for everyone else.
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="github_profile")


class Repository(Base):
    __tablename__ = "repositories"
    __table_args__ = (UniqueConstraint("user_id", "github_repo_id", name="uq_user_github_repo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    github_repo_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text)

    # GitHub topics/tags for the repo, e.g. ["fastapi", "mysql", "college-project"].
    # Stored using MySQL's native JSON column type -- no extra join table
    # needed just to keep a small list of strings.
    topics: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    has_license: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    open_issues: Mapped[int] = mapped_column(Integer, default=0)

    # 0-100 score for THIS repository alone (license, docs, topics,
    # maintenance state, community traction). See
    # app/services/github_service.py::compute_repo_health for the rubric.
    repo_health_score: Mapped[float] = mapped_column(Float, default=0)

    updated_at_github: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="repositories")


class DeveloperMetric(Base):
    """
    A single "Pulse reading" for a user, captured at sync time.

    Unlike the original V1 design (one row per user), this is a history
    table: a new row is inserted every time a user re-syncs their GitHub
    profile. That's what lets us show growth over time instead of just a
    single snapshot -- much closer to how a real fitness/health tracker
    works, which fits the "Pulse" theme of this project.
    """

    __tablename__ = "developer_metrics"
    __table_args__ = (Index("ix_developer_metrics_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    coding_score: Mapped[float] = mapped_column(Float, default=0)
    project_score: Mapped[float] = mapped_column(Float, default=0)
    testing_score: Mapped[float] = mapped_column(Float, default=0)
    documentation_score: Mapped[float] = mapped_column(Float, default=0)
    activity_score: Mapped[float] = mapped_column(Float, default=0)
    # Language-diversity ("polyglot") score, derived from Shannon entropy
    # of the user's language distribution. See analytics_service.py.
    diversity_score: Mapped[float] = mapped_column(Float, default=0)
    overall_score: Mapped[float] = mapped_column(Float, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="metric_snapshots")


class Badge(Base):
    """
    Catalog of all badges DevPulse can award ("Pulse Badges"). This table
    is reference/lookup data -- it rarely changes and is seeded once at
    app startup (see app/db/init_db.py), similar to a "roles" or
    "categories" table you'll see in most real-world schemas.
    """

    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    icon: Mapped[str] = mapped_column(String(10), default="\U0001F3C5")

    earned_by: Mapped[list["UserBadge"]] = relationship(back_populates="badge")


class UserBadge(Base):
    """Join table recording which user earned which badge, and when."""

    __tablename__ = "user_badges"
    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id", ondelete="CASCADE"), index=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="badges")
    badge: Mapped[Badge] = relationship(back_populates="earned_by")


class AIReport(Base):
    __tablename__ = "ai_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # "CAREER_ANALYSIS" or "RESUME_BULLETS"
    report_type: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="ai_reports")
