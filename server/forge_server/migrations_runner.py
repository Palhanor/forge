import os
import subprocess
from pathlib import Path

from forge_server.config import DATA_DIR, FORGE_DATA_VOLUME, FORGE_DOCKER_NETWORK

MIGRATION_TIMEOUT = 300
NODE_MIGRATION_IMAGE = "node:20-alpine"


def run_migration(
    *,
    source_dir: Path,
    command: str,
    env: dict[str, str],
    framework: str,
) -> None:
    source_dir = source_dir.resolve()

    if framework == "nodejs":
        _run_nodejs_migration(source_dir, command, env)
    elif framework == "fastapi":
        _run_shell_migration(source_dir, command, env)
    else:
        raise RuntimeError(
            f"Migrations are not supported for framework '{framework}' yet."
        )


def _run_shell_migration(source_dir: Path, command: str, env: dict[str, str]) -> None:
    run_env = os.environ.copy()
    run_env.update(env)
    result = subprocess.run(
        ["sh", "-c", command],
        cwd=source_dir,
        env=run_env,
        capture_output=True,
        text=True,
        timeout=MIGRATION_TIMEOUT,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(stderr or f"Migration failed: {command}")


def _run_nodejs_migration(source_dir: Path, command: str, env: dict[str, str]) -> None:
    try:
        source_dir.relative_to(DATA_DIR)
    except ValueError as exc:
        raise RuntimeError(
            f"Migration source path must be under DATA_DIR ({DATA_DIR})"
        ) from exc

    cmd = [
        "docker",
        "run",
        "--rm",
        "--network",
        FORGE_DOCKER_NETWORK,
        "-v",
        f"{FORGE_DATA_VOLUME}:{DATA_DIR}",
        "-w",
        str(source_dir),
    ]
    for key, value in env.items():
        cmd.extend(["-e", f"{key}={value}"])
    cmd.extend([NODE_MIGRATION_IMAGE, "sh", "-c", command])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=MIGRATION_TIMEOUT,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(stderr or f"Migration failed: {command}")
