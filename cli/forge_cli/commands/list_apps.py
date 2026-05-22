import typer

from forge_cli.client import APPS_PATH, builder_get, get_builder_host, handle_request_error

LIST_TIMEOUT = 30.0


def _parse_apps(payload) -> list[dict]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("apps", "items", "deployments"):
            if key in payload and isinstance(payload[key], list):
                return payload[key]
    return []


def list_apps():
    """List apps running on the Forge builder."""
    host = get_builder_host()
    typer.echo(f"Fetching apps from {host}{APPS_PATH}...")

    try:
        response = builder_get(APPS_PATH, timeout=LIST_TIMEOUT)
        response.raise_for_status()
        apps = _parse_apps(response.json())
    except Exception as exc:
        handle_request_error(host, exc)

    if not apps:
        typer.echo("No apps running.")
        return

    typer.echo("")
    for app in apps:
        name = app.get("name", "?")
        status = app.get("status", "unknown")
        line = f"  {name}  ({status})"

        if url := app.get("url"):
            line += f"  {url}"
        elif port := app.get("port"):
            line += f"  :{port}"

        typer.echo(line)

    typer.echo("")
    typer.echo(f"{len(apps)} app(s)")
