from unittest.mock import AsyncMock, patch

from tests.conftest import register_and_login

FAKE_PROFILE = {
    "login": "octocat",
    "avatar_url": "https://example.com/avatar.png",
    "html_url": "https://github.com/octocat",
    "bio": "Just a test account",
    "public_repos": 3,
    "followers": 10,
    "following": 5,
}

FAKE_REPOS = [
    {
        "id": 1,
        "name": "awesome-api",
        "language": "Python",
        "stargazers_count": 30,
        "forks_count": 4,
        "description": "A FastAPI project with pytest tests",
        "html_url": "https://github.com/octocat/awesome-api",
        "topics": ["fastapi", "testing"],
        "license": {"key": "mit"},
        "archived": False,
        "open_issues_count": 2,
        "updated_at": "2026-01-01T00:00:00Z",
        "fork": False,
    },
    {
        "id": 2,
        "name": "cli-tool",
        "language": "Go",
        "stargazers_count": 12,
        "forks_count": 1,
        "description": "A small CLI utility",
        "html_url": "https://github.com/octocat/cli-tool",
        "topics": [],
        "license": None,
        "archived": False,
        "open_issues_count": 0,
        "updated_at": "2026-01-02T00:00:00Z",
        "fork": False,
    },
]


async def fake_fetch_github(username: str, endpoint: str):
    if endpoint.endswith("/repos?per_page=100&sort=updated"):
        return FAKE_REPOS
    return FAKE_PROFILE


def test_full_sync_and_analytics_flow(client):
    token = register_and_login(client, "flow-user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.services.github_service.fetch_github", new=AsyncMock(side_effect=fake_fetch_github)):
        sync_response = client.post(
            "/api/v1/github/sync", json={"username": "octocat"}, headers=headers
        )
    assert sync_response.status_code == 200
    sync_body = sync_response.json()
    assert sync_body["profile"]["github_username"] == "octocat"
    assert sync_body["scores"]["overall"] > 0
    # First sync should always unlock the onboarding badge.
    assert any(b["code"] == "FIRST_PULSE" for b in sync_body["new_badges"])

    overview = client.get("/api/v1/analytics/overview", headers=headers)
    assert overview.status_code == 200
    overview_body = overview.json()
    assert overview_body["total_repositories"] == 2
    assert overview_body["total_stars"] == 42
    assert overview_body["pulse_status"] in {
        "Peak Pulse",
        "Thriving",
        "Steady Growth",
        "Warming Up",
        "Just Getting Started",
    }
    assert overview_body["score_change"] is None  # only one snapshot so far

    history = client.get("/api/v1/analytics/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1

    repos = client.get("/api/v1/github/repositories?sort_by=health", headers=headers)
    assert repos.status_code == 200
    repo_names = [r["name"] for r in repos.json()]
    assert "awesome-api" in repo_names
    # awesome-api has a license + description + topics, so it should
    # score healthier than cli-tool, which has none of those.
    scores_by_name = {r["name"]: r["repo_health_score"] for r in repos.json()}
    assert scores_by_name["awesome-api"] > scores_by_name["cli-tool"]

    achievements = client.get("/api/v1/achievements", headers=headers)
    assert achievements.status_code == 200
    earned_codes = {b["code"] for b in achievements.json() if b["earned"]}
    assert "FIRST_PULSE" in earned_codes

    leaderboard = client.get("/api/v1/analytics/leaderboard", headers=headers)
    assert leaderboard.status_code == 200
    assert leaderboard.json()["your_rank"] == 1


def test_second_sync_creates_new_snapshot_and_score_change(client):
    token = register_and_login(client, "flow-user-2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.services.github_service.fetch_github", new=AsyncMock(side_effect=fake_fetch_github)):
        client.post("/api/v1/github/sync", json={"username": "octocat"}, headers=headers)
        client.post("/api/v1/github/sync", json={"username": "octocat"}, headers=headers)

    overview = client.get("/api/v1/analytics/overview", headers=headers).json()
    # Same input data synced twice -> same score -> delta of 0, but the
    # field itself must now be populated (not None).
    assert overview["score_change"] == 0.0

    history = client.get("/api/v1/analytics/history", headers=headers).json()
    assert len(history) == 2


def test_leaderboard_opt_out_hides_user(client):
    token = register_and_login(client, "private-user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.services.github_service.fetch_github", new=AsyncMock(side_effect=fake_fetch_github)):
        client.post("/api/v1/github/sync", json={"username": "octocat"}, headers=headers)

    client.patch("/api/v1/auth/leaderboard-preference", json={"leaderboard_opt_in": False}, headers=headers)

    leaderboard = client.get("/api/v1/analytics/leaderboard", headers=headers).json()
    assert all(not entry["is_you"] for entry in leaderboard["entries"])
