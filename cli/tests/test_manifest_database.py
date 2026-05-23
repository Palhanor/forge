import pytest
import typer

from forge_cli.manifest import validate_forge_manifest


def _minimal_manifest(**overrides) -> dict:
    data = {
        "name": "my-app",
        "runtime": "python",
        "framework": "fastapi",
    }
    data.update(overrides)
    return data


def test_database_true_allowed_for_fastapi():
    manifest = _minimal_manifest(database=True)
    result = validate_forge_manifest(manifest)
    assert result["database"] is True


def test_database_rejects_non_boolean():
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


def test_database_false_allowed():
    manifest = _minimal_manifest(database=False)
    result = validate_forge_manifest(manifest)
    assert result["database"] is False
