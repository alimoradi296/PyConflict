"""Tests for VersionResolver domain service."""

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from pyconflict.domain.services.version_resolver import VersionResolver


def test_is_compatible_with_matching_version():
    """Test version compatibility check with matching version."""
    resolver = VersionResolver()
    version = Version("2.0.0")
    constraint = SpecifierSet(">=1.0.0,<3.0.0")

    assert resolver.is_compatible(version, constraint) is True


def test_is_compatible_with_non_matching_version():
    """Test version compatibility check with non-matching version."""
    resolver = VersionResolver()
    version = Version("0.5.0")
    constraint = SpecifierSet(">=1.0.0")

    assert resolver.is_compatible(version, constraint) is False


def test_is_compatible_with_empty_constraint():
    """Test version compatibility with empty constraint (any version)."""
    resolver = VersionResolver()
    version = Version("1.2.3")
    constraint = SpecifierSet("")

    assert resolver.is_compatible(version, constraint) is True


def test_filter_stable_versions():
    """Test filtering out prerelease versions."""
    resolver = VersionResolver()
    versions = [
        Version("1.0.0"),
        Version("1.1.0a1"),
        Version("1.1.0b1"),
        Version("1.1.0"),
        Version("2.0.0rc1"),
        Version("2.0.0"),
    ]

    stable = resolver.filter_stable_versions(versions)

    assert len(stable) == 3
    assert Version("1.0.0") in stable
    assert Version("1.1.0") in stable
    assert Version("2.0.0") in stable
    assert Version("1.1.0a1") not in stable


def test_get_latest_compatible():
    """Test getting latest compatible version."""
    resolver = VersionResolver()
    versions = [
        Version("1.0.0"),
        Version("1.5.0"),
        Version("2.0.0"),
        Version("2.5.0"),
        Version("3.0.0"),
    ]
    constraint = SpecifierSet(">=1.0.0,<3.0.0")

    latest = resolver.get_latest_compatible(versions, constraint)

    assert latest == Version("2.5.0")


def test_get_latest_compatible_returns_none_when_no_match():
    """Test getting latest compatible when no version matches."""
    resolver = VersionResolver()
    versions = [Version("1.0.0"), Version("1.5.0")]
    constraint = SpecifierSet(">=2.0.0")

    latest = resolver.get_latest_compatible(versions, constraint)

    assert latest is None
