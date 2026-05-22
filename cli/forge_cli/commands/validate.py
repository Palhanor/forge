from pathlib import Path

import typer

from forge_cli.manifest import load_forge_json


def validate():
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
