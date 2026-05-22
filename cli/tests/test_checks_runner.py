from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer

from forge_cli.checks import run_checks


def test_run_checks_success(tmp_path: Path):
    checks = [{"name": "test", "run": "pytest -q"}]
    with patch("forge_cli.checks.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        run_checks(tmp_path, checks)

    mock_run.assert_called_once_with(
        "pytest -q",
        shell=True,
        cwd=tmp_path,
    )


def test_run_checks_stops_on_first_failure(tmp_path: Path):
    checks = [
        {"name": "lint", "run": "ruff check ."},
        {"name": "test", "run": "pytest -q"},
    ]
    with patch("forge_cli.checks.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        with pytest.raises(typer.Exit) as exc_info:
            run_checks(tmp_path, checks)

    assert exc_info.value.exit_code == 1
    assert mock_run.call_count == 1
