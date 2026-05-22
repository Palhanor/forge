import json
import re
from pathlib import Path

import typer

FORGE_JSON = "forge.json"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

RUNTIME_FRAMEWORKS: dict[str, set[str]] = {
    "python": {"script", "fastapi"},
    "node": {"react", "next", "nodejs"},
}


def load_forge_json(project_root: Path) -> dict:
    path = project_root / FORGE_JSON
    if not path.exists():
        typer.secho(
            f"✗ {FORGE_JSON} not found in {project_root}",
            fg=typer.colors.RED,
        )
        typer.echo("  Create a forge.json manifest before deploying.")
        raise typer.Exit(code=1)

    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        typer.secho(f"✗ Invalid JSON in {FORGE_JSON}: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    if not isinstance(data, dict):
        typer.secho(f"✗ {FORGE_JSON} must be a JSON object", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    return validate_forge_manifest(data)


def validate_forge_manifest(data: dict) -> dict:
    errors: list[str] = []

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("'name' is required (non-empty string)")
    elif not SLUG_PATTERN.match(name.strip()):
        errors.append(
            "'name' must be a slug (lowercase letters, numbers, hyphens)"
        )

    runtime = data.get("runtime")
    if not isinstance(runtime, str) or runtime not in RUNTIME_FRAMEWORKS:
        errors.append("'runtime' must be 'python' or 'node'")
    else:
        framework = data.get("framework")
        allowed = RUNTIME_FRAMEWORKS[runtime]
        if not isinstance(framework, str) or framework not in allowed:
            errors.append(
                f"'framework' must be one of {sorted(allowed)} for runtime '{runtime}'"
            )

    port = data.get("port")
    if port is not None:
        if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
            errors.append("'port' must be an integer between 1 and 65535")

    for field in ("start", "build"):
        value = data.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(f"'{field}' must be a non-empty string when provided")

    subdomain = data.get("subdomain")
    if subdomain is not None:
        if not isinstance(subdomain, str) or not SLUG_PATTERN.match(subdomain.strip()):
            errors.append(
                "'subdomain' must be a slug (lowercase letters, numbers, hyphens)"
            )

    if errors:
        typer.secho(f"✗ Invalid {FORGE_JSON}:", fg=typer.colors.RED)
        for err in errors:
            typer.echo(f"  - {err}")
        raise typer.Exit(code=1)

    return data
