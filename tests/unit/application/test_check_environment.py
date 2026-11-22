"""Tests for checking requirements of installed distributions."""

from typing import List

from packaging.version import Version

from pyconflict.application.use_cases.check_environment import CheckEnvironmentUseCase
from pyconflict.domain.entities import InstalledDistribution


class FakeEnvironmentRepository:
    def __init__(self, distributions: List[InstalledDistribution]) -> None:
        self.distributions = distributions

    def get_installed_distributions(self) -> List[InstalledDistribution]:
        return self.distributions


def test_check_environment_reports_incompatible_and_missing_requirements():
    repository = FakeEnvironmentRepository(
        [
            InstalledDistribution(
                "consumer",
                Version("1.0"),
                [
                    "dependency>=2",
                    "missing>=1",
                    "windows-only>=1; sys_platform == 'win32'",
                ],
            ),
            InstalledDistribution("dependency", Version("1.0")),
        ]
    )

    response = CheckEnvironmentUseCase(repository).execute()

    assert response.exit_code == 1
    assert [conflict.dependency_name for conflict in response.conflicts] == [
        "dependency",
        "missing",
    ]
    assert response.conflicts[0].installed_version == Version("1.0")
    assert response.conflicts[1].installed_version is None


def test_check_environment_reports_unparseable_metadata():
    repository = FakeEnvironmentRepository(
        [InstalledDistribution("consumer", Version("1.0"), ["not a requirement !!!"])]
    )

    response = CheckEnvironmentUseCase(repository).execute()

    assert response.exit_code == 5
    assert response.conflicts == []
    assert response.analysis_errors[0]["package"] == "consumer"
