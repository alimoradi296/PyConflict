"""Tests for dependency version suggestions."""

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from pyconflict.domain.entities import Conflict, ConflictSeverity, Package
from pyconflict.domain.services.suggestion_generator import SuggestionGenerator
from pyconflict.domain.services.version_resolver import VersionResolver


def _suggestion_for(installed_version: str) -> str:
    conflict = Conflict(
        dependency_name="asgiref",
        required_by="django==3.2.0",
        required_constraint=SpecifierSet(">=3.3.2,<4"),
        installed_version=Version(installed_version),
        conflicting_package=None,
        severity=ConflictSeverity.ERROR,
    )
    package = Package(name="django", version=Version("3.2.0"))
    generator = SuggestionGenerator(VersionResolver())
    return generator._generate_conflict_suggestion(conflict, package)


def test_suggests_upgrade_when_installed_dependency_is_below_lower_bound():
    suggestion = _suggestion_for("3.2.0")

    assert "Upgrade 'asgiref' from 3.2.0" in suggestion
    assert "django's requirement" in suggestion


def test_suggests_compatible_dependency_when_installed_version_is_above_upper_bound():
    suggestion = _suggestion_for("4.0.0")

    assert "Use a version of 'asgiref' compatible with django" in suggestion
    assert "older version of django" not in suggestion
