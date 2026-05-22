import subprocess
from pathlib import Path

import typer


def run_checks(project_root: Path, checks: list[dict]) -> None:
    total = len(checks)
    for index, check in enumerate(checks, start=1):
        name = check["name"].strip()
        run_cmd = check["run"].strip()
        typer.echo(f"Running check '{name}' ({index}/{total})...")
        result = subprocess.run(
            run_cmd,
            shell=True,
            cwd=project_root,
        )
        if result.returncode != 0:
            typer.secho(
                f"✗ Check '{name}' failed (exit code {result.returncode})",
                fg=typer.colors.RED,
            )
            typer.echo("  Fix the issues above and run forge deploy again.")
            raise typer.Exit(code=1)

    typer.secho(f"✓ All checks passed ({total}/{total})", fg=typer.colors.GREEN)
