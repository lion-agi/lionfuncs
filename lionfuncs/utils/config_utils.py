"""Configuration utilities for managing application settings."""

import json
import os
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union

T = TypeVar("T")


@dataclass
class ConfigSchema:
    """Configuration schema definition."""

    type: Type
    required: bool = True
    default: Any = None
    description: str = ""
    validator: Optional[callable] = None
    secret: bool = False


class Config:
    """Thread-safe configuration container with validation."""

    def __init__(
        self,
        data: Dict[str, Any],
        schema: Optional[Dict[str, ConfigSchema]] = None,
    ):
        """Initialize config."""
        self._data = {}
        self._schema = schema or {}

        # Process and validate data
        self.update(data)

    def get(
        self, key: str, default: Any = None, cast: Optional[Type] = None
    ) -> Any:
        """Get configuration value."""
        value = self._data.get(key, default)

        if cast and value is not None:
            try:
                if cast is bool and isinstance(value, str):
                    lower_val = value.lower()
                    if lower_val in ("true", "yes", "on", "1"):
                        return True
                    if lower_val in ("false", "no", "off", "0"):
                        return False
                    raise ValueError(f"Cannot convert '{value}' to bool")
                return cast(value)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Failed to cast {key}={value} to {cast.__name__}: {e}"
                )
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        if key in self._schema:
            if value is None and self._schema[key].required:
                if self._schema[key].default is not None:
                    value = self._schema[key].default
                else:
                    raise ValueError(f"{key} is required")

            if value is not None and not isinstance(
                value, self._schema[key].type
            ):
                raise TypeError(
                    f"Expected type {self._schema[key].type.__name__}, "
                    f"got {type(value).__name__}"
                )

            if value is not None and self._schema[key].validator:
                if not self._schema[key].validator(value):
                    raise ValueError(f"Validation failed for {key}")

        self._data[key] = value

    def update(self, data: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        # First validate all values
        errors = []
        for key in self._schema:
            if key not in data and self._schema[key].required:
                if self._schema[key].default is None:
                    errors.append(key)

        if errors:
            raise ValueError(f"Missing required keys: {errors}")

        # Then set values
        for key, value in data.items():
            self.set(key, value)

        # Set defaults for missing optional fields
        for key, schema in self._schema.items():
            if (
                key not in data
                and not schema.required
                and schema.default is not None
            ):
                self.set(key, schema.default)

    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Convert config to dictionary."""
        if not include_secrets:
            return {
                k: (
                    "***"
                    if self._schema.get(k, ConfigSchema(type=str)).secret
                    else v
                )
                for k, v in self._data.items()
            }
        return deepcopy(self._data)


class ConfigUtils:
    """Configuration utility functions."""

    @staticmethod
    def load_config(
        path: Optional[Union[str, Path]] = None,
        env_prefix: str = "",
        schema: Optional[Dict[str, ConfigSchema]] = None,
        defaults: Optional[Dict[str, Any]] = None,
        env_separator: str = "__",
        case_sensitive: bool = False,
    ) -> Config:
        """Load configuration from multiple sources."""
        config_data = defaults or {}

        # Load from file
        if path:
            file_config = ConfigUtils.load_file(path)
            ConfigUtils.deep_update(config_data, file_config)

        # Load from environment
        if env_prefix:
            env_config = ConfigUtils.load_env(
                prefix=env_prefix,
                separator=env_separator,
                case_sensitive=case_sensitive,
            )
            ConfigUtils.deep_update(config_data, env_config)

        return Config(config_data, schema)

    @staticmethod
    def load_file(path: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        try:
            with path.open() as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise IOError(f"Failed to load config file: {e}")

    @staticmethod
    def load_env(
        prefix: str = "", separator: str = "__", case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """Load configuration from environment."""
        config = {}

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            # Remove prefix and process key
            key = key[len(prefix) :]
            if not case_sensitive:
                key = key.lower()

            # Convert value type
            if value.lower() in ("true", "yes", "on", "1"):
                value = True
            elif value.lower() in ("false", "no", "off", "0"):
                value = False
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass

            # Build nested structure
            current = config
            parts = key.split(separator)
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = value

        return config

    @staticmethod
    def deep_update(
        base: Dict[str, Any],
        update: Dict[str, Any],
        create_missing: bool = True,
    ) -> Dict[str, Any]:
        """Deep update dictionary."""
        for key, value in update.items():
            if (
                isinstance(value, dict)
                and key in base
                and isinstance(base[key], dict)
            ):
                ConfigUtils.deep_update(base[key], value)
            elif create_missing or key in base:
                base[key] = deepcopy(value)
        return base
