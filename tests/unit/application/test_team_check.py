"""Tests for the opt-in team baseline workflow."""

import pytest
from packaging.version import Version

from pyconflict.application.use_cases.team_check import TeamCheckUseCase


class FakeEnvironment:
    def __init__(self, packages):
        self.packages = packages

    def get_installed_packages(self):
        return self.packages


class FakeCache:
    def __init__(self, baseline=None):
        self.values = {} if baseline is None else {TeamCheckUseCase.STANDARD_KEY: baseline}
        self.writes = []

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value, ttl):
        self.writes.append((key, value, ttl))
        self.values[key] = value

    def clear(self):
        self.values.clear()


def test_team_check_reports_missing_different_and_extra_packages():
    use_case = TeamCheckUseCase(
        FakeEnvironment({"Requests": Version("2.32.0"), "rich": Version("13.0")}),
        FakeCache({"requests": "2.31.0", "urllib3": "2.0"}),
        "workspace-a",
    )

    result = use_case.execute()

    assert result.workspace_id == "workspace-a"
    assert result.matches_standard is False
    assert result.packages_count == 2
    assert {item["status"] for item in result.drift} == {"different", "missing", "extra"}


def test_team_check_does_not_upload_environment_during_comparison():
    cache = FakeCache({"requests": "2.31.0"})
    use_case = TeamCheckUseCase(
        FakeEnvironment({"requests": Version("2.31.0")}), cache, "workspace-a"
    )

    assert use_case.execute().matches_standard is True
    assert cache.writes == []


def test_saving_baseline_is_explicit_and_uses_cache_ttl():
    cache = FakeCache()
    use_case = TeamCheckUseCase(
        FakeEnvironment({"Requests": Version("2.31.0")}), cache, "workspace-a"
    )

    result = use_case.save_current_as_standard(ttl=60)

    assert result == {"requests": "2.31.0"}
    assert cache.writes == [(TeamCheckUseCase.STANDARD_KEY, result, 60)]


def test_team_check_requires_existing_baseline():
    use_case = TeamCheckUseCase(FakeEnvironment({}), FakeCache(), "workspace-a")

    with pytest.raises(RuntimeError, match="No team baseline"):
        use_case.execute()


def test_team_check_rejects_invalid_baseline_version():
    use_case = TeamCheckUseCase(
        FakeEnvironment({}), FakeCache({"requests": "not-a-version"}), "workspace-a"
    )

    with pytest.raises(ValueError, match="Invalid version"):
        use_case.execute()
