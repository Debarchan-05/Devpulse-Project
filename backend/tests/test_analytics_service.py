from app.services.analytics_service import (
    WEIGHTS,
    compute_diversity_score,
    compute_scores,
    pulse_status,
)


class FakeRepo:
    """A tiny stand-in for the Repository model so these tests don't need
    a database at all -- compute_scores() and compute_diversity_score()
    are pure functions of a list of repo-like objects."""

    def __init__(self, language=None, stars=0, description=None, topics=None):
        self.language = language
        self.stars = stars
        self.description = description
        self.topics = topics or []


def test_weights_sum_to_one():
    assert round(sum(WEIGHTS.values()), 6) == 1.0


def test_compute_scores_no_repos():
    scores = compute_scores([])
    assert scores["overall_score"] == round(45 * WEIGHTS["coding"] + 40 * WEIGHTS["project"] + 30 * WEIGHTS["testing"] + 35 * WEIGHTS["documentation"] + 40 * WEIGHTS["activity"] + 0 * WEIGHTS["diversity"], 2)
    assert scores["diversity_score"] == 0.0


def test_compute_scores_rewards_more_repos_and_stars():
    few = [FakeRepo(language="Python", stars=1) for _ in range(2)]
    many = [FakeRepo(language="Python", stars=10) for _ in range(10)]
    assert compute_scores(many)["overall_score"] > compute_scores(few)["overall_score"]


def test_diversity_rewards_multiple_languages_over_one():
    single_language = [FakeRepo(language="Python") for _ in range(6)]
    six_languages = [
        FakeRepo(language=lang) for lang in ["Python", "JavaScript", "Go", "Rust", "C++", "TypeScript"]
    ]
    assert compute_diversity_score(six_languages) > compute_diversity_score(single_language)


def test_diversity_score_empty_is_zero():
    assert compute_diversity_score([]) == 0.0


def test_testing_score_detects_test_keyword_in_description_or_topics():
    repos_with_tests = [
        FakeRepo(description="A pytest based testing framework"),
        FakeRepo(topics=["unit-testing", "ci"]),
    ]
    repos_without = [FakeRepo(description="A simple calculator app")]
    assert compute_scores(repos_with_tests)["testing_score"] > compute_scores(repos_without)["testing_score"]


def test_pulse_status_thresholds():
    assert pulse_status(95) == "Peak Pulse"
    assert pulse_status(75) == "Thriving"
    assert pulse_status(55) == "Steady Growth"
    assert pulse_status(35) == "Warming Up"
    assert pulse_status(10) == "Just Getting Started"
