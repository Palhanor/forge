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
        return None  # caller reports type error

    variable = raw.get("variable", "DATABASE_URL")
    migration = raw.get("migration")
    return DatabaseConfig(
        enabled=True,
        variable=variable.strip() if isinstance(variable, str) else "",
        migration=migration.strip() if isinstance(migration, str) and migration.strip() else None,
    )
