# Configuration Utilities Documentation

This document describes the configuration management system provided by the ConfigUtils module. The system provides secure, type-safe configuration management with support for multiple sources and validation.

## Core Features

### Basic Configuration

```python
from lionfuncs.utils import ConfigUtils

# Load configuration
config = ConfigUtils.load_config(
    path="config.json",
    env_prefix="APP_",
    defaults={"debug": False}
)

# Access values
debug = config.get("debug")
port = config.get("port", cast=int)
```

### Schema Validation

```python
from lionfuncs.utils import ConfigUtils, ConfigSchema

# Define schema
schema = ConfigUtils.create_schema({
    "debug": {"type": bool, "default": False},
    "port": {"type": int, "required": True},
    "secret": {"type": str, "secret": True}
})

# Load with validation
config = ConfigUtils.load_config(
    path="config.json",
    schema=schema
)
```

## Configuration Sources

The system supports multiple configuration sources with the following priority:

1. Environment variables (highest)
2. Configuration file
3. Default values (lowest)

### Environment Variables

```bash
# Set environment variables
export APP_DEBUG=true
export APP_DB__HOST=localhost
export APP_DB__PORT=5432
```

```python
# Load from environment
config = ConfigUtils.load_env(prefix="APP_")
assert config["db"]["host"] == "localhost"
```

### Configuration File

```json
{
    "debug": false,
    "port": 8080,
    "db": {
        "host": "localhost",
        "port": 5432
    }
}
```

### Default Values

```python
defaults = {
    "debug": False,
    "port": 8080,
    "timeout": 30
}

config = ConfigUtils.load_config(defaults=defaults)
```

## Schema Definition

### Basic Schema

```python
schema = {
    "debug": ConfigSchema(type=bool, default=False),
    "port": ConfigSchema(
        type=int,
        required=True,
        validator=lambda x: 1024 <= x <= 65535
    ),
    "api_key": ConfigSchema(type=str, secret=True)
}
```

### Schema Attributes

- `type`: Expected value type
- `required`: Whether value is required
- `default`: Default value
- `secret`: Whether value should be masked
- `validator`: Optional validation function
- `description`: Schema documentation

## Best Practices

### 1. Security

- Use `secret=True` for sensitive values
- Never commit configuration files with secrets
- Use environment variables for sensitive data

```python
schema = {
    "api_key": ConfigSchema(type=str, secret=True),
    "password": ConfigSchema(type=str, secret=True)
}
```

### 2. Validation

- Define schemas for all configurations
- Use custom validators for complex rules
- Include type validation

```python
def validate_port(port: int) -> None:
    if not 1024 <= port <= 65535:
        raise ValueError("Invalid port number")

schema = {
    "port": ConfigSchema(type=int, validator=validate_port)
}
```

### 3. Organization

- Use nested configurations for related settings
- Group configurations logically
- Use consistent naming

```python
config = {
    "db": {
        "host": "localhost",
        "port": 5432,
        "credentials": {
            "username": "user",
            "password": "secret"
        }
    }
}
```

## Common Patterns

### 1. Application Configuration

```python
def load_app_config():
    schema = ConfigUtils.create_schema({
        "debug": {"type": bool, "default": False},
        "log_level": {"type": str, "default": "INFO"},
        "port": {"type": int, "required": True}
    })

    return ConfigUtils.load_config(
        path="config.json",
        env_prefix="APP_",
        schema=schema
    )
```

### 2. Database Configuration

```python
def load_db_config():
    schema = ConfigUtils.create_schema({
        "db": {
            "type": dict,
            "schema": {
                "host": {"type": str, "required": True},
                "port": {"type": int, "default": 5432},
                "username": {"type": str, "required": True},
                "password": {"type": str, "secret": True}
            }
        }
    })

    return ConfigUtils.load_config(
        path="db_config.json",
        env_prefix="DB_",
        schema=schema
    )
```

## Error Handling

Handle common configuration errors:

1. Missing required values
2. Invalid types
3. Validation failures
4. File loading errors
5. Environment variable issues

## Testing

Test configuration handling:

```python
def test_config():
    # Test with valid config
    config = ConfigUtils.load_config(...)
    assert config.get("debug") is False

    # Test missing required
    with pytest.raises(ValueError):
        ConfigUtils.load_config(...)

    # Test invalid type
    with pytest.raises(TypeError):
        ConfigUtils.load_config(...)
```

## Migration

Tips for configuration updates:

1. Maintain backwards compatibility
2. Use schema versioning
3. Provide migration utilities
4. Document changes
5. Handle defaults appropriately

## Additional Resources

- JSON Schema documentation
- Environment variable best practices
- Security guidelines
- Python typing documentation
