import pytest

from forge_server.database_config import DatabaseConfig, parse_database_config


def test_parse_database_true():
    config = parse_database_config({"database": True})
    assert config == DatabaseConfig(enabled=True, variable="DATABASE_URL", migration=None)


def test_parse_database_object():
    config = parse_database_config(
        {
            "database": {
                "variable": "DB_URL",
                "migration": "npm ci && npx prisma migrate deploy",
            }
        }
    )
    assert config is not None
    assert config.variable == "DB_URL"
    assert config.migration == "npm ci && npx prisma migrate deploy"


def test_parse_database_disabled():
    assert parse_database_config({}) is None


def test_parse_database_invalid_type():
    with pytest.raises(ValueError, match="database"):
        parse_database_config({"database": "yes"})
