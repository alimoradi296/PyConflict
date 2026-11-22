"""Application workflow for comparing an environment with a team baseline."""

from typing import Dict, List, Optional

from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

from pyconflict.domain.repositories import ICacheRepository, IEnvironmentRepository


class TeamCheckResult:
    """Comparison between installed packages and a saved team baseline."""

    def __init__(self, workspace_id: str, drift: List[Dict[str, Optional[str]]]) -> None:
        self.workspace_id = workspace_id
        self.drift = drift
        self.matches_standard = not drift
        self.packages_count = 0


class TeamCheckUseCase:
    """Read or save an explicitly selected team package baseline.

    The check only reads the baseline. It does not upload a developer's
    environment unless ``save_current_as_standard`` is explicitly called.
    """

    STANDARD_KEY = "team:standard_environment"

    def __init__(
        self,
        environment_repository: IEnvironmentRepository,
        cache_repository: ICacheRepository,
        workspace_id: str,
    ) -> None:
        if not workspace_id.strip():
            raise ValueError("workspace_id must not be empty")
        self.environment_repository = environment_repository
        self.cache_repository = cache_repository
        self.workspace_id = workspace_id

    def execute(self) -> TeamCheckResult:
        """Compare installed packages with the saved team standard."""
        baseline = self.cache_repository.get(self.STANDARD_KEY)
        if baseline is None:
            raise RuntimeError("No team baseline exists. Run team-check --set-standard first.")

        installed_versions = {
            str(canonicalize_name(name)): str(version)
            for name, version in self.environment_repository.get_installed_packages().items()
        }
        normalized_baseline = self._normalize_baseline(baseline)
        drift: List[Dict[str, Optional[str]]] = []

        for package, expected in normalized_baseline.items():
            actual = installed_versions.get(package)
            if actual is None:
                drift.append(
                    {
                        "package": package,
                        "installed_version": None,
                        "standard_version": expected,
                        "status": "missing",
                    }
                )
            elif actual != expected:
                drift.append(
                    {
                        "package": package,
                        "installed_version": actual,
                        "standard_version": expected,
                        "status": "different",
                    }
                )

        for package, actual in installed_versions.items():
            if package not in normalized_baseline:
                drift.append(
                    {
                        "package": package,
                        "installed_version": actual,
                        "standard_version": None,
                        "status": "extra",
                    }
                )

        result = TeamCheckResult(self.workspace_id, drift)
        result.packages_count = len(installed_versions)
        return result

    def save_current_as_standard(self, ttl: int = 30 * 24 * 60 * 60) -> Dict[str, str]:
        """Save the current environment as the team baseline on explicit request."""
        if ttl <= 0:
            raise ValueError("ttl must be greater than zero")
        standard = {
            str(canonicalize_name(name)): str(version)
            for name, version in self.environment_repository.get_installed_packages().items()
        }
        self.cache_repository.set(self.STANDARD_KEY, standard, ttl)
        return standard

    @staticmethod
    def _normalize_baseline(value: object) -> Dict[str, str]:
        if not isinstance(value, dict):
            raise ValueError("The saved team baseline must be a package-to-version object")
        normalized: Dict[str, str] = {}
        for name, version in value.items():
            if not isinstance(name, str) or not isinstance(version, str):
                raise ValueError("Team baseline package names and versions must be strings")
            try:
                normalized[str(canonicalize_name(name))] = str(Version(version))
            except InvalidVersion as error:
                raise ValueError(f"Invalid version for {name}: {version}") from error
        return normalized
