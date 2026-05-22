import pytest
import typer

from forge_cli.manifest import _validate_checks_field, validate_forge_manifest


def _minimal_manifest(**overrides) -> dict:
    data = {
        "name": "my-app",
        "runtime": "python",
        "framework": "fastapi",
    }
    data.update(overrides)
    return data


class TestValidateChecksField:
    def test_valid_checks(self):
        checks = [{"name": "test", "run": "pytest -q"}]
        assert _validate_checks_field(checks) == []

    def test_rejects_non_array(self):
        errors = _validate_checks_field({"test": "pytest -q"})
        assert any("'checks' must be an array" in e for e in errors)

    def test_rejects_empty_array(self):
        errors = _validate_checks_field([])
        assert any("non-empty array" in e for e in errors)

    def test_rejects_invalid_item(self):
        errors = _validate_checks_field(["pytest -q"])
        assert any("must be an object" in e for e in errors)

    def test_rejects_missing_run(self):
        errors = _validate_checks_field([{"name": "test"}])
        assert any(".run is required" in e for e in errors)

    def test_rejects_invalid_name_slug(self):
        errors = _validate_checks_field([{"name": "Test", "run": "pytest -q"}])
        assert any(".name must be a slug" in e for e in errors)

    def test_rejects_duplicate_names(self):
        checks = [
            {"name": "test", "run": "pytest -q"},
            {"name": "test", "run": "pytest -q tests/"},
        ]
        errors = _validate_checks_field(checks)
        assert any("duplicated" in e for e in errors)


class TestValidateForgeManifestChecks:
    def test_accepts_manifest_with_checks(self):
        manifest = _minimal_manifest(
            checks=[{"name": "lint", "run": "ruff check ."}],
        )
        result = validate_forge_manifest(manifest)
        assert result["checks"][0]["name"] == "lint"

    def test_rejects_invalid_checks_in_manifest(self):
        manifest = _minimal_manifest(checks=[])
        with pytest.raises(typer.Exit):
            validate_forge_manifest(manifest)
