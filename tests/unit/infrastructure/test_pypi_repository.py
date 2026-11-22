"""Unit tests for PyPI metadata handling."""

from packaging.version import Version

from pyconflict.infrastructure.repositories.pypi_repository import PyPIPackageRepository


def test_latest_stable_filters_releases_by_python_version(monkeypatch):
    repository = PyPIPackageRepository()
    release_data = {
        "releases": {
            "1.0": [{"requires_python": ">=3.8", "yanked": False}],
            "2.0": [{"requires_python": ">=3.10", "yanked": False}],
            "3.0rc1": [{"requires_python": ">=3.8", "yanked": False}],
        }
    }
    monkeypatch.setattr(
        repository, "_fetch_from_pypi", lambda name, version: release_data
    )

    result = repository.get_latest_stable("example", Version("3.8"))

    assert result == Version("1.0")


def test_latest_stable_skips_yanked_release_files(monkeypatch):
    repository = PyPIPackageRepository()
    release_data = {
        "releases": {
            "1.0": [{"requires_python": ">=3.8", "yanked": False}],
            "2.0": [{"requires_python": ">=3.8", "yanked": True}],
        }
    }
    monkeypatch.setattr(
        repository, "_fetch_from_pypi", lambda name, version: release_data
    )

    result = repository.get_latest_stable("example", Version("3.8"))

    assert result == Version("1.0")
