import json
from pathlib import Path

import typer

from forge_cli.archive import create_project_archive
from forge_cli.checks import run_checks
from forge_cli.client import (
    DEPLOY_PATH,
    builder_post,
    get_builder_host,
    handle_request_error,
)
from forge_cli.manifest import load_forge_json

DEPLOY_TIMEOUT = 600.0


def deploy(
    name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="Override app name from forge.json.",
    ),
    skip_checks: bool = typer.Option(
        False,
        "--skip-checks",
        help="Skip pre-deploy checks declared in forge.json.",
    ),
):
    """Package the current project as .tar.gz and upload it to the Forge builder."""
    project_root = Path.cwd()
    manifest = load_forge_json(project_root)
    app_name = name or manifest["name"]
    host = get_builder_host()

    if checks := manifest.get("checks"):
        if skip_checks:
            typer.echo("Skipping pre-deploy checks (--skip-checks).")
        else:
            run_checks(project_root, checks)

    typer.echo(f"Packaging {project_root}...")
    archive_path = None

    try:
        archive_path = create_project_archive(project_root)
        size_kb = archive_path.stat().st_size / 1024
        typer.echo(f"Archive: {archive_path.name} ({size_kb:.1f} KB)")
        typer.echo(f"Deploying '{app_name}' to {host}{DEPLOY_PATH}...")

        with archive_path.open("rb") as archive_file:
            response = builder_post(
                DEPLOY_PATH,
                files={
                    "archive": (f"{app_name}.tar.gz", archive_file, "application/gzip"),
                },
                data={
                    "name": app_name,
                    "source_path": str(project_root),
                    "manifest": json.dumps(manifest),
                },
                timeout=DEPLOY_TIMEOUT,
            )
            response.raise_for_status()

        data = response.json()
        message = data.get("message", "Deploy accepted")
        typer.secho(f"✓ {message}", fg=typer.colors.GREEN)

        if deploy_id := data.get("id"):
            typer.echo(f"  id: {deploy_id}")
        if status := data.get("status"):
            typer.echo(f"  status: {status}")
        if url := data.get("url"):
            typer.echo(f"  url: {url}")
            if manifest.get("framework") in ("fastapi", "nodejs"):
                typer.echo(f"  try: GET {url}/ping")
            elif manifest.get("framework") == "react":
                typer.echo(f"  try: open {url} in your browser")

    except Exception as exc:
        handle_request_error(host, exc)
    finally:
        if archive_path is not None and archive_path.exists():
            archive_path.unlink()
