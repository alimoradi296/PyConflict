"""Tests for ConflictDetector domain service."""

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from pyconflict.domain.entities import Dependency, Environment, Package
from pyconflict.domain.services.conflict_detector import ConflictDetector
from pyconflict.domain.services.version_resolver import VersionResolver


def test_detect_no_conflicts_when_dependencies_satisfied():
    """Test no conflicts when all dependencies are satisfied."""
    # Setup
    detector = ConflictDetector(VersionResolver())

    package = Package(
        name="requests",
        version=Version("2.31.0"),
        dependencies=[
            Dependency(name="urllib3", specifier=SpecifierSet(">=1.21.1,<3")),
            Dependency(name="certifi", specifier=SpecifierSet(">=2017.4.17")),
        ],
    )

    environment = Environment(
        packages={
            "urllib3": Version("2.0.0"),
            "certifi": Version("2023.7.22"),
        },
        python_version=Version("3.11.0"),
        platform="linux",
    )

    # Execute
    conflicts = detector.detect_conflicts(package, environment)

    # Assert
    assert len(conflicts) == 0


def test_detect_conflict_when_version_too_old():
    """Test conflict detection when installed version is too old."""
    # Setup
    detector = ConflictDetector(VersionResolver())

    package = Package(
        name="django",
        version=Version("4.2.0"),
        dependencies=[
            Dependency(name="asgiref", specifier=SpecifierSet(">=3.6.0,<4")),
        ],
    )

    environment = Environment(
        packages={
            "asgiref": Version("3.3.0"),  # Too old
        },
        python_version=Version("3.11.0"),
        platform="linux",
    )

    # Execute
    conflicts = detector.detect_conflicts(package, environment)

    # Assert
    assert len(conflicts) == 1
    assert conflicts[0].dependency_name == "asgiref"
    assert conflicts[0].installed_version == Version("3.3.0")


def test_detect_conflict_when_version_too_new():
    """Test conflict detection when installed version is too new."""
    # Setup
    detector = ConflictDetector(VersionResolver())

    package = Package(
        name="django",
        version=Version("3.2.0"),
        dependencies=[
            Dependency(name="asgiref", specifier=SpecifierSet(">=3.3.2,<4")),
        ],
    )

    environment = Environment(
        packages={
            "asgiref": Version("4.0.0"),  # Too new
        },
        python_version=Version("3.11.0"),
        platform="linux",
    )

    # Execute
    conflicts = detector.detect_conflicts(package, environment)

    # Assert
    assert len(conflicts) == 1
    assert conflicts[0].dependency_name == "asgiref"
    assert conflicts[0].required_constraint == SpecifierSet(">=3.3.2,<4")


def test_no_conflict_when_dependency_not_installed():
    """Test no conflict when dependency is not installed (will be installed)."""
    # Setup
    detector = ConflictDetector(VersionResolver())

    package = Package(
        name="requests",
        version=Version("2.31.0"),
        dependencies=[
            Dependency(name="urllib3", specifier=SpecifierSet(">=1.21.1,<3")),
        ],
    )

    environment = Environment(
        packages={},  # Empty environment
        python_version=Version("3.11.0"),
        platform="linux",
    )

    # Execute
    conflicts = detector.detect_conflicts(package, environment)

    # Assert
    assert len(conflicts) == 0


def test_detect_multiple_conflicts():
    """Test detection of multiple conflicts."""
    # Setup
    detector = ConflictDetector(VersionResolver())

    package = Package(
        name="example",
        version=Version("1.0.0"),
        dependencies=[
            Dependency(name="dep1", specifier=SpecifierSet(">=2.0")),
            Dependency(name="dep2", specifier=SpecifierSet("<1.0")),
            Dependency(name="dep3", specifier=SpecifierSet("==3.0.0")),
        ],
    )

    environment = Environment(
        packages={
            "dep1": Version("1.0.0"),  # Too old
            "dep2": Version("2.0.0"),  # Too new
            "dep3": Version("3.1.0"),  # Wrong version
        },
        python_version=Version("3.11.0"),
        platform="linux",
    )

    # Execute
    conflicts = detector.detect_conflicts(package, environment)

    # Assert
    assert len(conflicts) == 3
    conflict_names = {c.dependency_name for c in conflicts}
    assert conflict_names == {"dep1", "dep2", "dep3"}


def test_no_conflicts_with_empty_constraint():
    """Test no conflict when constraint is empty (any version)."""
    # Setup
    detector = ConflictDetector(VersionResolver())

    package = Package(
        name="example",
        version=Version("1.0.0"),
        dependencies=[
            Dependency(name="flexible-dep", specifier=SpecifierSet("")),
        ],
    )

    environment = Environment(
        packages={
            "flexible-dep": Version("999.0.0"),
        },
        python_version=Version("3.11.0"),
        platform="linux",
    )

    # Execute
    conflicts = detector.detect_conflicts(package, environment)

    # Assert
    assert len(conflicts) == 0


def test_conflict_includes_package_info():
    """Test that conflict includes information about the package."""
    # Setup
    detector = ConflictDetector(VersionResolver())

    package = Package(
        name="mypackage",
        version=Version("2.0.0"),
        dependencies=[
            Dependency(name="somedep", specifier=SpecifierSet(">=5.0")),
        ],
    )

    environment = Environment(
        packages={
            "somedep": Version("4.0.0"),
        },
        python_version=Version("3.11.0"),
        platform="linux",
    )

    # Execute
    conflicts = detector.detect_conflicts(package, environment)

    # Assert
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert "mypackage==2.0.0" in conflict.required_by
    assert conflict.dependency_name == "somedep"
