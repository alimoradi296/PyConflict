"""Regression tests for CLI commands with previously misleading behavior."""

import json

from packaging.specifiers import SpecifierSet
from packaging.version import Version
from typer.testing import CliRunner

from pyconflict.application.use_cases.check_environment import CheckEnvironmentResponse
from pyconflict.domain.entities import Conflict, ConflictSeverity
from pyconflict.presentation.cli import commands

runner = CliRunner()


def test_check_env_formats_use_case_response(monkeypatch):
    conflict = Conflict(
        dependency_name="dependency",
        required_by="consumer==1.0",
        required_constraint=SpecifierSet(">=2"),
        installed_version=Version("1.0"),
        conflicting_package=None,
        severity=ConflictSeverity.ERROR,
    )

    class FakeCheckEnvironmentUseCase:
        def execute(self):
            return CheckEnvironmentResponse(
                conflicts=[conflict], analysis_errors=[], packages_count=2
            )

    monkeypatch.setattr(
        commands,
        "get_check_environment_use_case",
        lambda: FakeCheckEnvironmentUseCase(),
    )

    result = runner.invoke(commands.app, ["check-env", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["healthy"] is False
    assert payload["conflicts"][0]["dependency"] == "dependency"
    assert payload["conflicts"][0]["installed"] == "1.0"


def test_batch_check_rejects_ranges_and_extras(monkeypatch):
    def unexpected_use_case():
        raise AssertionError("invalid package specifications must not reach PyPI")

    monkeypatch.setattr(commands, "get_check_add_package_use_case", unexpected_use_case)

    result = runner.invoke(
        commands.app,
        ["batch-check", "--package", "demo>=1", "--package", "demo[extra]", "--json"],
    )

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["exit_code"] == 2
    assert all("error" in entry for entry in payload["results"])
