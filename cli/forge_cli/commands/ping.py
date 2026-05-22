import typer

from forge_cli.client import PING_PATH, builder_get, get_builder_host, handle_request_error


def ping():
    """Check if the Forge builder service is reachable."""
    host = get_builder_host()
    typer.echo(f"Pinging Forge builder at {host}...")

    try:
        response = builder_get(PING_PATH, timeout=5)
        response.raise_for_status()
        data = response.json()
        typer.secho(f"✓ {data.get('message', 'Pong!')}", fg=typer.colors.GREEN)
    except Exception as exc:
        handle_request_error(host, exc)
