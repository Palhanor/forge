import json
from pathlib import Path

import typer

DEFAULT_HOST = "http://localhost:8000"
CONFIG_PATH = Path.home() / ".forge" / "config.json"


def load_config() -> dict:
    """Load config from ~/.forge/config.json. Returns empty dict if not found."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(data: dict):
    """Save config to ~/.forge/config.json."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_host() -> str:
    config = load_config()
    return config.get("host", DEFAULT_HOST).rstrip("/")


def get_api_key() -> str | None:
    config = load_config()
    api_key = config.get("api_key")
    if isinstance(api_key, str) and api_key.strip():
        return api_key.strip()
    return None


def require_config() -> tuple[str, str]:
    """Return (host, api_key) or exit with instructions to run forge setup."""
    host = get_host()
    api_key = get_api_key()
    if not api_key:
        typer.secho("✗ API key not configured.", fg=typer.colors.RED)
        typer.echo("  Run: forge setup")
        raise typer.Exit(code=1)
    return host, api_key
