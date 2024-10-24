"""Tests for configuration utilities."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from lionfuncs.utils.config_utils import Config, ConfigSchema, ConfigUtils


class TestConfig:
    """Test suite for Config class."""

    def test_basic_operations(self):
        """Test basic config operations."""
        config = Config({"key": "value"})

        # Test get
        assert config.get("key") == "value"
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", "default") == "default"

        # Test set
        config.set("new_key", "new_value")
        assert config.get("new_key") == "new_value"

        # Test update
        config.update({"key1": 1, "key2": 2})
        assert config.get("key1") == 1
        assert config.get("key2") == 2

    def test_schema_defaults(self):
        """Test schema default values."""
        schema = {
            "required": ConfigSchema(type=int, required=True),
            "optional": ConfigSchema(
                type=str, required=False, default="default"
            ),
            "nullable": ConfigSchema(type=str, required=False),
        }

        config = Config({"required": 1}, schema)
        assert config.get("required") == 1
        assert config.get("optional") == "default"
        assert config.get("nullable") is None

    def test_secret_handling(self):
        """Test secret value handling."""
        schema = {
            "password": ConfigSchema(type=str, secret=True),
            "api_key": ConfigSchema(type=str, secret=True),
            "debug": ConfigSchema(type=bool),
        }

        config = Config(
            {"password": "secret123", "api_key": "key123", "debug": True},
            schema,
        )

        # Without secrets
        data = config.get("password") == "secret123"
        data = config.to_dict(include_secrets=False)
        assert data["password"] == "***"
        assert data["api_key"] == "***"
        assert data["debug"] is True

        # With secrets
        data = config.to_dict(include_secrets=True)
        assert data["password"] == "secret123"
        assert data["api_key"] == "key123"

    def test_boolean_casting(self):
        """Test boolean type casting."""
        config = Config({})

        true_values = ["true", "yes", "1", "on", "True", "YES"]
        false_values = ["false", "no", "0", "off", "False", "NO"]

        for value in true_values:
            assert config.get("key", default=value, cast=bool) is True

        for value in false_values:
            assert config.get("key", default=value, cast=bool) is False

        with pytest.raises(ValueError):
            config.get("key", default="invalid", cast=bool)


class TestConfigUtils:
    """Test suite for ConfigUtils."""

    def test_load_file(self, tmp_path: Path):
        """Test loading configuration from file."""
        config_data = {"debug": True, "port": 8080, "nested": {"key": "value"}}

        # Create config file
        config_file = tmp_path / "config.json"
        with config_file.open("w") as f:
            json.dump(config_data, f)

        # Load config
        loaded = ConfigUtils.load_file(config_file)
        assert loaded == config_data

        # Test missing file
        with pytest.raises(FileNotFoundError):
            ConfigUtils.load_file(tmp_path / "nonexistent.json")

        # Test invalid JSON
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("invalid json")
        with pytest.raises(ValueError):
            ConfigUtils.load_file(invalid_file)

    def test_load_env(self, monkeypatch):
        """Test loading configuration from environment."""
        env_vars = {
            "APP_DEBUG": "true",
            "APP_PORT": "8080",
            "APP_DB__HOST": "localhost",
            "APP_DB__PORT": "5432",
        }

        # Set environment variables
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Load config
        config = ConfigUtils.load_env(prefix="APP_")
        assert config["debug"] is True
        assert config["port"] == 8080
        assert config["db"]["host"] == "localhost"
        assert config["db"]["port"] == 5432

    def test_load_config(self, tmp_path: Path, monkeypatch):
        """Test configuration loading priority."""
        # Create config file
        config_file = tmp_path / "config.json"
        with config_file.open("w") as f:
            json.dump(
                {"debug": False, "port": 8000, "db": {"host": "default"}}, f
            )

        # Set environment variables
        monkeypatch.setenv("APP_DEBUG", "true")
        monkeypatch.setenv("APP_DB__HOST", "override")

        # Load config with schema
        schema = {
            "debug": ConfigSchema(type=bool),
            "port": ConfigSchema(type=int),
            "db": ConfigSchema(
                type=dict, validator=lambda x: isinstance(x, dict)
            ),
        }

        config = ConfigUtils.load_config(
            path=config_file,
            env_prefix="APP_",
            schema=schema,
            defaults={"port": 5000},
        )

        # Check priority: env > file > defaults
        assert config.get("debug") is True  # from env
        assert config.get("port") == 8000  # from file
        assert config.get("db")["host"] == "override"  # from env

    def test_deep_update(self):
        """Test deep dictionary update."""
        base = {"a": 1, "b": {"c": 2, "d": 3}, "e": [1, 2, 3]}

        update = {"b": {"d": 4, "f": 5}, "e": [4, 5, 6]}

        result = ConfigUtils.deep_update(base, update)
        assert result["a"] == 1  # unchanged
        assert result["b"]["c"] == 2  # unchanged
        assert result["b"]["d"] == 4  # updated
        assert result["b"]["f"] == 5  # added
        assert result["e"] == [4, 5, 6]  # replaced
