from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    enabled: bool
    variable: str = "DATABASE_URL"
    migration: str | None = None


def parse_database_config(manifest: dict) -> DatabaseConfig | None:
    raw = manifest.get("database")
    if raw is None or raw is False:
        return None
    if raw is True:
        return DatabaseConfig(enabled=True)
    if not isinstance(raw, dict):
        raise ValueError("'database' must be true or an object with 'variable' and optional 'migration'")

    variable = raw.get("variable", "DATABASE_URL")
    if not isinstance(variable, str) or not variable.strip():
        raise ValueError("'database.variable' must be a non-empty string")

    migration = raw.get("migration")
    if migration is not None:
        if not isinstance(migration, str) or not migration.strip():
            raise ValueError("'database.migration' must be a non-empty string when provided")

    return DatabaseConfig(
        enabled=True,
        variable=variable.strip(),
        migration=migration.strip() if isinstance(migration, str) else None,
    )


def database_enabled(manifest: dict) -> bool:
    config = parse_database_config(manifest)
    return config is not None and config.enabled
