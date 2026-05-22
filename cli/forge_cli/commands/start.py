import typer

from forge_cli.client import app_path, builder_post, get_builder_host, handle_request_error


def start(
    name: str = typer.Argument(..., help="App name (from forge.json)."),
):
    """Start a stopped app (existing container or image)."""
    host = get_builder_host()
    typer.echo(f"Starting '{name}'...")

    try:
        response = builder_post(app_path(name, "start"), timeout=120)
        response.raise_for_status()
        data = response.json()
        typer.secho(f"✓ {data.get('message', 'Started')}", fg=typer.colors.GREEN)
        if status := data.get("status"):
            typer.echo(f"  status: {status}")
        if url := data.get("url"):
            typer.echo(f"  url: {url}")
            typer.echo(f"  try: GET {url}/ping")
    except Exception as exc:
        handle_request_error(host, exc)
