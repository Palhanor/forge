import json
import re
import secrets
import subprocess
from urllib.parse import quote_plus

import psycopg
from psycopg import sql

from forge_server.config import (
    DEPLOYMENTS_DIR,
    FORGE_DOCKER_NETWORK,
    FORGE_POSTGRES_DB,
    FORGE_POSTGRES_HOST,
    FORGE_POSTGRES_PASSWORD,
    FORGE_POSTGRES_PORT,
    FORGE_POSTGRES_USER,
    POSTGRES_CONTAINER_NAME,
)
from forge_server.database_config import DatabaseConfig, parse_database_config
from forge_server.storage import get_deploy_metadata, update_deploy_status

_IDENTIFIER_RE = re.compile(r"[^a-z0-9_]")


def database_name_for_app(app_name: str) -> str:
    """Map app slug to a safe Postgres identifier (forge_ping_api)."""
    slug = app_name.strip().lower().replace("-", "_")
    slug = _IDENTIFIER_RE.sub("", slug)
    if not slug or slug[0].isdigit():
        slug = f"app_{slug}" if slug else "app"
    name = f"forge_{slug}"
    return name[:63]


def _admin_conninfo() -> str:
    return (
        f"host={FORGE_POSTGRES_HOST} port={FORGE_POSTGRES_PORT} "
        f"dbname={FORGE_POSTGRES_DB} user={FORGE_POSTGRES_USER} "
        f"password={FORGE_POSTGRES_PASSWORD}"
    )


def build_database_url(credentials: dict) -> str:
    user = quote_plus(credentials["user"])
    password = quote_plus(credentials["password"])
    host = credentials.get("host", FORGE_POSTGRES_HOST)
    port = credentials.get("port", FORGE_POSTGRES_PORT)
    dbname = credentials["database"]
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def check_postgres_available() -> None:
    if not FORGE_POSTGRES_PASSWORD.strip():
        raise RuntimeError(
            "FORGE_POSTGRES_PASSWORD is not set on the builder. "
            "Configure server/.env and run make builder-up (full stack)."
        )

    network_result = subprocess.run(
        ["docker", "network", "inspect", FORGE_DOCKER_NETWORK],
        capture_output=True,
    )
    if network_result.returncode != 0:
        raise RuntimeError(
            f"Docker network '{FORGE_DOCKER_NETWORK}' not found. "
            "Run make builder-up (full stack) before deploying with database."
        )

    container_result = subprocess.run(
        [
            "docker",
            "inspect",
            "-f",
            "{{.State.Status}}",
            POSTGRES_CONTAINER_NAME,
        ],
        capture_output=True,
        text=True,
    )
    if container_result.returncode != 0:
        raise RuntimeError(
            f"Postgres container '{POSTGRES_CONTAINER_NAME}' is not running. "
            "Run make builder-up (full stack) before deploying with database."
        )
    if container_result.stdout.strip() != "running":
        raise RuntimeError(
            f"Postgres container '{POSTGRES_CONTAINER_NAME}' is not running "
            f"(status: {container_result.stdout.strip()})."
        )

    try:
        with psycopg.connect(_admin_conninfo(), connect_timeout=5) as conn:
            conn.execute("SELECT 1")
    except Exception as exc:
        raise RuntimeError(
            f"Cannot connect to Postgres at {FORGE_POSTGRES_HOST}:{FORGE_POSTGRES_PORT}: {exc}"
        ) from exc


def _save_database_metadata(
    deploy_id: str,
    app_name: str,
    database_meta: dict,
    *,
    config: DatabaseConfig,
) -> None:
    metadata_path = DEPLOYMENTS_DIR / deploy_id / "metadata.json"
    metadata = get_deploy_metadata(deploy_id)
    database_meta["config"] = {
        "variable": config.variable,
        "migration": config.migration,
    }
    metadata["database"] = database_meta
    metadata_path.write_text(json.dumps(metadata, indent=2))
    update_deploy_status(deploy_id, app_name, database_enabled=True)


def build_extra_env_for_credentials(
    credentials: dict,
    config: DatabaseConfig,
) -> dict[str, str]:
    return {config.variable: build_database_url(credentials)}


def _role_exists(conn: psycopg.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM pg_roles WHERE rolname = %s", (name,)
    ).fetchone()
    return row is not None


def _database_exists(conn: psycopg.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s", (name,)
    ).fetchone()
    return row is not None


def ensure_app_database(
    app_name: str,
    deploy_id: str,
    config: DatabaseConfig,
) -> dict[str, str]:
    """Provision or reuse per-app database; returns extra_env for docker run."""
    check_postgres_available()

    metadata = get_deploy_metadata(deploy_id)
    existing = metadata.get("database") or {}
    credentials = existing.get("credentials")
    if credentials:
        return build_extra_env_for_credentials(credentials, config)

    db_name = database_name_for_app(app_name)
    db_user = db_name
    db_password = secrets.token_urlsafe(24)

    with psycopg.connect(_admin_conninfo(), autocommit=True) as conn:
        if not _role_exists(conn, db_user):
            conn.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD {}").format(
                    sql.Identifier(db_user),
                    sql.Literal(db_password),
                )
            )
        else:
            conn.execute(
                sql.SQL("ALTER USER {} WITH PASSWORD {}").format(
                    sql.Identifier(db_user),
                    sql.Literal(db_password),
                )
            )

        if not _database_exists(conn, db_name):
            conn.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(db_name),
                    sql.Identifier(db_user),
                )
            )
        conn.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(db_name),
                sql.Identifier(db_user),
            )
        )

    credentials = {
        "user": db_user,
        "password": db_password,
        "database": db_name,
        "host": FORGE_POSTGRES_HOST,
        "port": FORGE_POSTGRES_PORT,
    }
    database_meta = {"credentials": credentials}
    _save_database_metadata(deploy_id, app_name, database_meta, config=config)

    return build_extra_env_for_credentials(credentials, config)


def drop_app_database(metadata: dict) -> None:
    database_meta = metadata.get("database") or {}
    credentials = database_meta.get("credentials")
    if not credentials:
        return

    if not FORGE_POSTGRES_PASSWORD.strip():
        return

    db_name = credentials["database"]
    db_user = credentials["user"]

    try:
        with psycopg.connect(_admin_conninfo(), autocommit=True) as conn:
            conn.execute(
                sql.SQL(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = {} AND pid <> pg_backend_pid()"
                ).format(sql.Literal(db_name))
            )
            conn.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name))
            )
            conn.execute(
                sql.SQL("DROP USER IF EXISTS {}").format(sql.Identifier(db_user))
            )
    except Exception:
        pass


def validate_manifest_database(manifest: dict) -> DatabaseConfig | None:
    config = parse_database_config(manifest)
    if config is None:
        return None
    framework = manifest.get("framework")
    if framework in ("react", "next"):
        raise ValueError(
            f"Framework '{framework}' does not support Forge database. "
            "Use fastapi or nodejs with a server-side runtime."
        )
    if framework not in ("fastapi", "nodejs", "script"):
        raise ValueError(
            "Forge database requires a server framework (fastapi, nodejs, or script)."
        )
    return config
