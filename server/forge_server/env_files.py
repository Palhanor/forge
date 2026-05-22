import re
from pathlib import Path

ENV_FILE_TRAVERSAL = re.compile(r"(^|[\\/])\.\.([\\/]|$)")


def _validate_env_file_path(env_file: str) -> None:
    if not env_file.strip():
        raise ValueError("'envFile' must be a non-empty string when provided")
    if env_file.startswith(("/", "\\")) or (
        len(env_file) > 1 and env_file[1] == ":"
    ):
        raise ValueError("'envFile' must be a relative path")
    if "\\" in env_file:
        raise ValueError("'envFile' must use forward slashes (relative path)")
    if ENV_FILE_TRAVERSAL.search(env_file):
        raise ValueError("'envFile' must not contain '..' path segments")


def resolve_env_file(source_dir: Path, manifest: dict) -> Path | None:
    """Resolve manifest envFile to an absolute path under source_dir, or None."""
    env_file = manifest.get("envFile")
    if env_file is None:
        return None
    if not isinstance(env_file, str):
        raise ValueError("'envFile' must be a string when provided")

    _validate_env_file_path(env_file)

    source_dir = source_dir.resolve()
    resolved = (source_dir / env_file).resolve()
    if not str(resolved).startswith(str(source_dir)):
        raise ValueError(f"Unsafe envFile path: {env_file}")

    if not resolved.is_file():
        raise ValueError(f"envFile not found in project: {env_file}")

    return resolved
