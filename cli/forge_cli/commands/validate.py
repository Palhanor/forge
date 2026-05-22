from pathlib import Path

import typer

from forge_cli.checks import run_checks
from forge_cli.manifest import load_forge_json


def validate(
    skip_checks: bool = typer.Option(
        False,
        "--skip-checks",
        help="Skip checks declared in forge.json.",
    ),
):
    """Validate forge.json in the current directory."""
    project_root = Path.cwd()
    manifest = load_forge_json(project_root)
    typer.secho(
        f"✓ {project_root / 'forge.json'} is valid",
        fg=typer.colors.GREEN,
    )
    typer.echo(f"  name: {manifest.get('name')}")
    typer.echo(f"  runtime: {manifest.get('runtime')}")
    typer.echo(f"  framework: {manifest.get('framework')}")
    if manifest.get("envFile"):
        typer.echo(f"  envFile: {manifest.get('envFile')}")
    if checks := manifest.get("checks"):
        typer.echo(f"  checks: {', '.join(c['name'] for c in checks)}")
        if skip_checks:
            typer.echo("  (checks skipped via --skip-checks)")
        else:
            run_checks(project_root, checks)
