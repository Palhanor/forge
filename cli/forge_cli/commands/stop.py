import typer

from forge_cli.client import app_path, builder_post, get_builder_host, handle_request_error


def stop(
    name: str = typer.Argument(..., help="App name (from forge.json)."),
):
    """Stop a running app (container stopped, deployment data kept)."""
    host = get_builder_host()
    typer.echo(f"Stopping '{name}'...")

    try:
        response = builder_post(app_path(name, "stop"), timeout=30)
        response.raise_for_status()
        data = response.json()
        typer.secho(f"✓ {data.get('message', 'Stopped')}", fg=typer.colors.GREEN)
        if status := data.get("status"):
            typer.echo(f"  status: {status}")
    except Exception as exc:
        handle_request_error(host, exc)
