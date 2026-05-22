import typer

from forge_cli.client import app_path, builder_delete, get_builder_host, handle_request_error


def delete(
    name: str = typer.Argument(..., help="App name to remove permanently."),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt.",
    ),
):
    """Delete an app: container, image, registry entry, and deployment files."""
    if not yes:
        confirmed = typer.confirm(
            f"Permanently delete '{name}' (container, image, and files)?"
        )
        if not confirmed:
            typer.echo("Cancelled.")
            raise typer.Exit(code=0)

    host = get_builder_host()
    typer.echo(f"Deleting '{name}'...")

    try:
        response = builder_delete(app_path(name), timeout=60)
        response.raise_for_status()
        data = response.json()
        typer.secho(f"✓ {data.get('message', 'Deleted')}", fg=typer.colors.GREEN)
    except Exception as exc:
        handle_request_error(host, exc)
