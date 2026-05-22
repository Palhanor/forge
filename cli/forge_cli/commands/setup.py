from typing import Optional

import typer

from forge_cli.config import DEFAULT_HOST, load_config, save_config


def setup(
    host: Optional[str] = typer.Option(
        None,
        "--host",
        help=f"Builder URL (default: {DEFAULT_HOST}).",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="API key for authenticating with the builder.",
    ),
):
    """Configure builder host and API key (~/.forge/config.json)."""
    current = load_config()

    resolved_host = host or typer.prompt(
        "Builder host",
        default=current.get("host", DEFAULT_HOST),
    )
    resolved_host = resolved_host.strip().rstrip("/")
    if not resolved_host:
        typer.secho("✗ Host cannot be empty.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if api_key is not None:
        resolved_key = api_key.strip()
    else:
        resolved_key = typer.prompt(
            "API key",
            hide_input=True,
            default=current.get("api_key", ""),
        ).strip()

    if not resolved_key:
        typer.secho("✗ API key cannot be empty.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    save_config(
        {
            **current,
            "host": resolved_host,
            "api_key": resolved_key,
        }
    )

    typer.secho("✓ Configuration saved to ~/.forge/config.json", fg=typer.colors.GREEN)
    typer.echo(f"  host: {resolved_host}")
    typer.echo(f"  api_key: {'*' * min(len(resolved_key), 8)}...")
