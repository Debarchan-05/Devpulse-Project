from app.services.badge_service import BADGE_RULES, BadgeContext


class FakeMetric:
    def __init__(self, **scores):
        self.coding_score = scores.get("coding_score", 0)
        self.project_score = scores.get("project_score", 0)
        self.testing_score = scores.get("testing_score", 0)
        self.documentation_score = scores.get("documentation_score", 0)
        self.activity_score = scores.get("activity_score", 0)
        self.overall_score = scores.get("overall_score", 0)


class FakeRepo:
    def __init__(self, language=None, stars=0):
        self.language = language
        self.stars = stars


def test_first_pulse_only_on_first_sync():
    ctx_first = BadgeContext(is_first_sync=True, metric=FakeMetric(), repos=[])
    ctx_repeat = BadgeContext(is_first_sync=False, metric=FakeMetric(), repos=[])
    assert BADGE_RULES["FIRST_PULSE"](ctx_first) is True
    assert BADGE_RULES["FIRST_PULSE"](ctx_repeat) is False


def test_prolific_builder_needs_ten_repos():
    ctx = BadgeContext(is_first_sync=False, metric=FakeMetric(), repos=[FakeRepo() for _ in range(10)])
    assert BADGE_RULES["PROLIFIC_BUILDER"](ctx) is True
    ctx_short = BadgeContext(is_first_sync=False, metric=FakeMetric(), repos=[FakeRepo() for _ in range(9)])
    assert BADGE_RULES["PROLIFIC_BUILDER"](ctx_short) is False


def test_polyglot_needs_five_distinct_languages():
    repos = [FakeRepo(language=lang) for lang in ["Python", "Go", "Rust", "C++", "TypeScript"]]
    ctx = BadgeContext(is_first_sync=False, metric=FakeMetric(), repos=repos)
    assert BADGE_RULES["POLYGLOT"](ctx) is True


def test_well_rounded_requires_all_five_dimensions():
    balanced = FakeMetric(coding_score=65, project_score=65, testing_score=65, documentation_score=65, activity_score=65)
    lopsided = FakeMetric(coding_score=95, project_score=95, testing_score=95, documentation_score=95, activity_score=10)
    assert BADGE_RULES["WELL_ROUNDED"](BadgeContext(False, balanced, [])) is True
    assert BADGE_RULES["WELL_ROUNDED"](BadgeContext(False, lopsided, [])) is False


def test_peak_pulse_needs_overall_ninety():
    assert BADGE_RULES["PEAK_PULSE"](BadgeContext(False, FakeMetric(overall_score=90), [])) is True
    assert BADGE_RULES["PEAK_PULSE"](BadgeContext(False, FakeMetric(overall_score=89.9), [])) is False


def test_community_favorite_needs_one_repo_with_twenty_stars():
    ctx = BadgeContext(False, FakeMetric(), [FakeRepo(stars=5), FakeRepo(stars=25)])
    assert BADGE_RULES["COMMUNITY_FAVORITE"](ctx) is True
