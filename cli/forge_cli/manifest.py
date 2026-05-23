import json
import re
from pathlib import Path

import typer

FORGE_JSON = "forge.json"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ENV_FILE_TRAVERSAL = re.compile(r"(^|[\\/])\.\.([\\/]|$)")

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

    return validate_forge_manifest(data, project_root=project_root)


def _validate_checks_field(checks: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(checks, list):
        errors.append("'checks' must be an array when provided")
        return errors
    if not checks:
        errors.append("'checks' must be a non-empty array when provided")
        return errors

    seen_names: set[str] = set()
    for index, item in enumerate(checks):
        prefix = f"'checks[{index}]'"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object with 'name' and 'run'")
            continue

        check_name = item.get("name")
        if not isinstance(check_name, str) or not check_name.strip():
            errors.append(f"{prefix}.name is required (non-empty string)")
        elif not SLUG_PATTERN.match(check_name.strip()):
            errors.append(
                f"{prefix}.name must be a slug (lowercase letters, numbers, hyphens)"
            )
        else:
            normalized = check_name.strip()
            if normalized in seen_names:
                errors.append(f"{prefix}.name '{normalized}' is duplicated")
            else:
                seen_names.add(normalized)

        run_cmd = item.get("run")
        if not isinstance(run_cmd, str) or not run_cmd.strip():
            errors.append(f"{prefix}.run is required (non-empty string)")

    return errors


def _validate_database_field(data: dict) -> list[str]:
    errors: list[str] = []
    database = data.get("database")
    if database is None:
        return errors

    framework = data.get("framework")

    if database is True:
        if isinstance(framework, str) and framework in ("react", "next"):
            errors.append(
                f"'database' is not supported for framework '{framework}'. "
                "Use fastapi or nodejs."
            )
        return errors

    if not isinstance(database, dict):
        errors.append("'database' must be true or an object with 'variable' and optional 'migration'")
        return errors

    variable = database.get("variable", "DATABASE_URL")
    if not isinstance(variable, str) or not variable.strip():
        errors.append("'database.variable' must be a non-empty string")

    migration = database.get("migration")
    if migration is not None and (not isinstance(migration, str) or not migration.strip()):
        errors.append("'database.migration' must be a non-empty string when provided")

    if isinstance(framework, str) and framework in ("react", "next"):
        errors.append(
            f"'database' is not supported for framework '{framework}'. "
            "Use fastapi or nodejs."
        )

    return errors


def validate_migrate_flag(manifest: dict, run_migrate: bool) -> None:
    if not run_migrate:
        return
    database = manifest.get("database")
    migration = None
    if database is True:
        pass
    elif isinstance(database, dict):
        migration = database.get("migration")
    if not migration or not str(migration).strip():
        typer.secho(
            "✗ --migrate requires 'database.migration' in forge.json",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)


def _validate_env_file_field(env_file: str) -> list[str]:
    errors: list[str] = []
    if not env_file.strip():
        errors.append("'envFile' must be a non-empty string when provided")
        return errors
    if env_file.startswith(("/", "\\")) or (
        len(env_file) > 1 and env_file[1] == ":"
    ):
        errors.append("'envFile' must be a relative path")
    elif "\\" in env_file:
        errors.append("'envFile' must use forward slashes (relative path)")
    elif ENV_FILE_TRAVERSAL.search(env_file):
        errors.append("'envFile' must not contain '..' path segments")
    return errors


def validate_forge_manifest(data: dict, *, project_root: Path | None = None) -> dict:
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

    env_file = data.get("envFile")
    if env_file is not None:
        if not isinstance(env_file, str):
            errors.append("'envFile' must be a string when provided")
        else:
            env_file_errors = _validate_env_file_field(env_file)
            errors.extend(env_file_errors)
            if not env_file_errors and project_root is not None:
                env_path = (project_root / env_file).resolve()
                if not env_path.is_file():
                    errors.append(
                        f"'envFile' not found: {project_root / env_file} "
                        "(create it locally before deploy, e.g. from .env.example)"
                    )

    checks = data.get("checks")
    if checks is not None:
        errors.extend(_validate_checks_field(checks))

    errors.extend(_validate_database_field(data))

    if errors:
        typer.secho(f"✗ Invalid {FORGE_JSON}:", fg=typer.colors.RED)
        for err in errors:
            typer.echo(f"  - {err}")
        raise typer.Exit(code=1)

    return data
