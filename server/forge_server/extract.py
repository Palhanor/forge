import tarfile
from pathlib import Path


def safe_extract_archive(archive_path: Path, dest_dir: Path) -> Path:
    """Extract a .tar.gz into dest_dir/source, rejecting path traversal."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    source_dir = dest_dir / "source"
    if source_dir.exists():
        import shutil

        shutil.rmtree(source_dir)
    source_dir.mkdir(parents=True)

    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            member_path = Path(member.name)
            if member.name.startswith("/") or ".." in member.name.split("/"):
                raise ValueError(f"Unsafe path in archive: {member.name}")
            target = (source_dir / member_path).resolve()
            if not str(target).startswith(str(source_dir.resolve())):
                raise ValueError(f"Unsafe path in archive: {member.name}")

        tar.extractall(source_dir)

    return source_dir
