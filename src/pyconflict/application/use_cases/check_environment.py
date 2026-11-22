"""Use case for validating the current Python environment."""

from dataclasses import dataclass
from typing import Dict, List

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from pyconflict.domain.entities import (
    Conflict,
    ConflictSeverity,
    InstalledDistribution,
)
from pyconflict.domain.repositories import IEnvironmentRepository


@dataclass
class CheckEnvironmentResponse:
    """Result of checking installed distribution requirements."""

    conflicts: List[Conflict]
    analysis_errors: List[Dict[str, str]]
    packages_count: int

    @property
    def exit_code(self) -> int:
        """Return the CLI status for this result."""
        if self.analysis_errors:
            return 5
        return 1 if self.conflicts else 0


class CheckEnvironmentUseCase:
    """Check installed distributions for missing or incompatible requirements."""

    def __init__(self, environment_repository: IEnvironmentRepository) -> None:
        self._environment_repository = environment_repository

    def execute(self) -> CheckEnvironmentResponse:
        distributions = self._environment_repository.get_installed_distributions()
        installed = {str(canonicalize_name(item.name)): item.version for item in distributions}
        conflicts: List[Conflict] = []
        analysis_errors: List[Dict[str, str]] = []

        for distribution in distributions:
            self._check_distribution(
                distribution,
                installed,
                conflicts,
                analysis_errors,
            )

        return CheckEnvironmentResponse(
            conflicts=conflicts,
            analysis_errors=analysis_errors,
            packages_count=len(distributions),
        )

    @staticmethod
    def _check_distribution(
        distribution: InstalledDistribution,
        installed: Dict[str, Version],
        conflicts: List[Conflict],
        analysis_errors: List[Dict[str, str]],
    ) -> None:
        for raw_requirement in distribution.requirements:
            try:
                requirement = Requirement(raw_requirement)
                if requirement.marker and not requirement.marker.evaluate():
                    continue
            except (InvalidRequirement, ValueError, TypeError) as error:
                analysis_errors.append(
                    {
                        "package": distribution.name,
                        "requirement": raw_requirement,
                        "error": str(error),
                    }
                )
                continue

            installed_version = installed.get(canonicalize_name(requirement.name))
            if installed_version is not None and requirement.specifier.contains(
                installed_version, prereleases=True
            ):
                continue

            conflicts.append(
                Conflict(
                    dependency_name=requirement.name,
                    required_by=f"{distribution.name}=={distribution.version}",
                    required_constraint=requirement.specifier,
                    installed_version=installed_version,
                    conflicting_package=None,
                    severity=ConflictSeverity.ERROR,
                )
            )
