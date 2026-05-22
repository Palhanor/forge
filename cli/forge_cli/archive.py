import os
import tarfile
import tempfile
from pathlib import Path

# Directory and file name patterns excluded from deploy archives.
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".eggs",
    "dist",
    "build",
    ".forge",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}

DEFAULT_EXCLUDE_FILE_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".egg-info",
)


def _exclude_dir(name: str) -> bool:
    return name in DEFAULT_EXCLUDE_DIRS


def _exclude_file(name: str) -> bool:
    return name.endswith(DEFAULT_EXCLUDE_FILE_SUFFIXES) or name == ".DS_Store"


def create_project_archive(project_root: Path) -> Path:
    """Create a .tar.gz of project_root in a temp file. Caller must delete the file."""
    project_root = project_root.resolve()
    archive_fd, archive_path = tempfile.mkstemp(suffix=".tar.gz", prefix="forge-deploy-")
    os.close(archive_fd)

    with tarfile.open(archive_path, "w:gz") as tar:
        for dirpath, dirnames, filenames in os.walk(project_root):
            dirnames[:] = [d for d in dirnames if not _exclude_dir(d)]

            for filename in filenames:
                if _exclude_file(filename):
                    continue

                full_path = Path(dirpath) / filename
                arcname = full_path.relative_to(project_root).as_posix()
                tar.add(full_path, arcname=arcname)

    return Path(archive_path)
