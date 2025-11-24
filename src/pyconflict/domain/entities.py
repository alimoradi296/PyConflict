"""Domain entities - Immutable business objects."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from packaging.specifiers import SpecifierSet
from packaging.version import Version


class ConflictSeverity(Enum):
    """Severity level of a conflict."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Dependency:
    """A dependency with version constraint.

    Represents a single dependency requirement, including version constraints,
    platform markers, and extras.
    """

    name: str
    specifier: SpecifierSet
    markers: Optional[str] = None  # PEP 508 markers (e.g., "python_version >= '3.8'")
    extras: Set[str] = field(default_factory=set)

    def __str__(self) -> str:
        """String representation matching PEP 508 format."""
        parts = [self.name]

        if self.extras:
            parts.append(f"[{','.join(sorted(self.extras))}]")

        if self.specifier:
            parts.append(str(self.specifier))

        if self.markers:
            parts.append(f"; {self.markers}")

        return "".join(parts)


@dataclass(frozen=True)
class Package:
    """Immutable package entity.

    Represents a Python package with its metadata and dependencies.
    """

    name: str
    version: Version
    requires_python: Optional[str] = None
    dependencies: List[Dependency] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name}=={self.version}"


@dataclass(frozen=True)
class Conflict:
    """Represents a dependency conflict.

    A conflict occurs when a package requires a version of a dependency
    that is incompatible with what's installed or required by another package.
    """

    dependency_name: str
    required_by: str  # Package that requires this dependency
    required_constraint: SpecifierSet
    installed_version: Optional[Version]
    conflicting_package: Optional[str]  # Package that conflicts with this requirement
    severity: ConflictSeverity

    def __str__(self) -> str:
        """Human-readable description of the conflict."""
        lines = [
            f"Conflict in '{self.dependency_name}':",
            f"  Required by: {self.required_by} ({self.required_constraint})",
        ]

        if self.installed_version:
            lines.append(f"  Installed: {self.installed_version}")

        if self.conflicting_package:
            lines.append(f"  Conflicts with: {self.conflicting_package}")

        return "\n".join(lines)


@dataclass(frozen=True)
class Environment:
    """Current Python environment state.

    Represents the current state of installed packages and Python version.
    """

    packages: Dict[str, Version]  # package_name -> version
    python_version: Version
    platform: str  # sys.platform value

    def has_package(self, name: str) -> bool:
        """Check if a package is installed."""
        return name.lower() in self.packages

    def get_version(self, name: str) -> Optional[Version]:
        """Get installed version of a package."""
        return self.packages.get(name.lower())
