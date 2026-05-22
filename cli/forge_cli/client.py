import httpx
import typer

from forge_cli.config import require_config

DEPLOY_PATH = "/deploy"
APPS_PATH = "/apps"
PING_PATH = "/ping"


def app_path(name: str, action: str | None = None) -> str:
    base = f"{APPS_PATH}/{name}"
    return f"{base}/{action}" if action else base


def get_auth_headers() -> dict:
    _, api_key = require_config()
    return {"Authorization": f"Bearer {api_key}"}


def builder_get(path: str, timeout: float = 30.0) -> httpx.Response:
    host, _ = require_config()
    return httpx.get(
        f"{host}{path}",
        headers=get_auth_headers(),
        timeout=timeout,
    )


def builder_post(
    path: str,
    *,
    files: dict | None = None,
    data: dict | None = None,
    timeout: float = 120.0,
) -> httpx.Response:
    host, _ = require_config()
    return httpx.post(
        f"{host}{path}",
        headers=get_auth_headers(),
        files=files,
        data=data,
        timeout=timeout,
    )


def builder_delete(path: str, timeout: float = 30.0) -> httpx.Response:
    host, _ = require_config()
    return httpx.delete(
        f"{host}{path}",
        headers=get_auth_headers(),
        timeout=timeout,
    )


def handle_request_error(host: str, exc: Exception) -> None:
    if isinstance(exc, httpx.ConnectError):
        typer.secho(f"✗ Could not connect to {host}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code == 401:
            typer.secho("✗ Unauthorized (401)", fg=typer.colors.RED)
            typer.echo(
                "  Check your API key: forge setup"
            )
            typer.echo(
                "  Ensure the builder has the same FORGE_API_KEY environment variable."
            )
        elif exc.response.status_code == 503:
            typer.secho("✗ Builder not configured (503)", fg=typer.colors.RED)
            typer.echo(
                "  Set FORGE_API_KEY on the server before starting forge-server."
            )
        else:
            typer.secho(
                f"✗ Server returned {exc.response.status_code}",
                fg=typer.colors.RED,
            )
        if exc.response.text:
            typer.echo(exc.response.text)
        raise typer.Exit(code=1) from exc
    typer.secho(f"✗ Unexpected error: {exc}", fg=typer.colors.RED)
    raise typer.Exit(code=1) from exc


def get_builder_host() -> str:
    host, _ = require_config()
    return host
