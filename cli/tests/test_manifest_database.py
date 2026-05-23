import pytest
import typer

from forge_cli.manifest import validate_forge_manifest, validate_migrate_flag


def _minimal_manifest(**overrides) -> dict:
    data = {
        "name": "my-app",
        "runtime": "node",
        "framework": "nodejs",
    }
    data.update(overrides)
    return data


def test_database_true_allowed_for_nodejs():
    manifest = _minimal_manifest(database=True)
    result = validate_forge_manifest(manifest)
    assert result["database"] is True


def test_database_object_allowed():
    manifest = _minimal_manifest(
        database={
            "variable": "DATABASE_URL",
            "migration": "npm ci && npx prisma migrate deploy",
        }
    )
    result = validate_forge_manifest(manifest)
    assert result["database"]["migration"]


def test_database_rejects_invalid_type():
    with pytest.raises(typer.Exit):
        validate_forge_manifest(_minimal_manifest(database="yes"))


def test_database_rejects_react():
    with pytest.raises(typer.Exit):
        validate_forge_manifest(
            {
                "name": "my-front",
                "runtime": "node",
                "framework": "react",
                "database": True,
            }
        )


def test_migrate_requires_migration_command():
    with pytest.raises(typer.Exit):
        validate_migrate_flag(_minimal_manifest(database=True), run_migrate=True)


def test_migrate_ok_with_migration_command():
    validate_migrate_flag(
        _minimal_manifest(
            database={"variable": "DATABASE_URL", "migration": "npm ci"}
        ),
        run_migrate=True,
    )
