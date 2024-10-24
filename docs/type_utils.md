# Type Utilities Documentation

## Overview

The `TypeUtils` module provides comprehensive utilities for type checking, validation, and conversion with support for complex types and runtime validation.

## Core Features

### Type Validation
```python
from lionfuncs.utils import TypeValidator, TypeUtils

# Basic type validation
TypeValidator.validate_type(42, int)
TypeValidator.validate_type("test", str)

# Sequence validation
TypeValidator.validate_sequence([1, 2, 3], int)

# Mapping validation
TypeValidator.validate_mapping(
    {"a": 1, "b": 2},
    str,  # key type
    int   # value type
)
```

### Type Coercion
```python
# Basic coercion
num = TypeUtils.coerce_type("42", int)  # 42
text = TypeUtils.coerce_type(42, str)   # "42"

# Boolean coercion
TypeUtils.coerce_type("yes", bool)  # True
TypeUtils.coerce_type("no", bool)   # False

# Custom converters
converters = {str: CustomType}
obj = TypeUtils.coerce_type("test", CustomType, custom_converters=converters)
```

### Type Information
```python
# Get type information
type_info = TypeUtils.get_type_info(List[int])
print(type_info.is_sequence)  # True
print(type_info.args)        # (int,)

# Check subtype relationships
TypeUtils.check_subtype(List[int], Sequence[int])  # True
```

## Best Practices

### 1. Type Validation
```python
def process_data(data: Any) -> None:
    # Validate input type
    TypeValidator.validate_type(data, dict)

    # Validate structure
    TypeValidator.validate_mapping(
        data,
        str,
        object,
        required_keys={"id", "value"}
    )

    # Validate nested data
    TypeValidator.validate_sequence(
        data["items"],
        dict,
        min_length=1
    )
```

### 2. Safe Type Conversion
```python
def parse_config(config: dict) -> dict:
    return {
        "debug": TypeUtils.coerce_type(
            config.get("debug", False),
            bool
        ),
        "port": TypeUtils.coerce_type(
            config.get("port", "8080"),
            int,
            strict=True
        )
    }
```

### 3. Error Handling
```python
def safe_convert(value: Any, target_type: Type[T]) -> Optional[T]:
    try:
        return TypeUtils.coerce_type(value, target_type)
    except TypeError:
        return None
```

## Common Patterns

### API Data Validation
```python
def validate_api_response(response: dict) -> bool:
    try:
        # Validate overall structure
        TypeValidator.validate_mapping(
            response,
            str,
            object,
            required_keys={"data", "metadata"}
        )

        # Validate data section
        if isinstance(response["data"], list):
            TypeValidator.validate_sequence(
                response["data"],
                dict
            )

        # Validate metadata
        TypeValidator.validate_mapping(
            response["metadata"],
            str,
            str,
            required_keys={"timestamp"}
        )

        return True
    except (TypeError, ValueError):
        return False
```

### Configuration Parsing
```python
def parse_settings(settings: dict) -> dict:
    """Parse and validate configuration settings."""
    validated = {}

    # Define type mappings
    type_map = {
        "server.port": int,
        "server.host": str,
        "limits.max_connections": int,
        "debug": bool
    }

    # Convert and validate each setting
    for key, value in settings.items():
        if key in type_map:
            target_type = type_map[key]
            try:
                validated[key] = TypeUtils.coerce_type(
                    value,
                    target_type
                )
            except TypeError as e:
                raise ValueError(f"Invalid {key}: {e}")

    return validated
```

### Type-Safe Data Processing
```python
def process_typed_data(data: Any, schema: dict) -> dict:
    """Process data according to schema."""
    result = {}

    for key, type_info in schema.items():
        if key in data:
            # Get type information
            info = TypeUtils.get_type_info(type_info)

            if info.is_sequence:
                # Handle sequences
                TypeValidator.validate_sequence(
                    data[key],
                    info.args[0]
                )
                result[key] = [
                    TypeUtils.coerce_type(item, info.args[0])
                    for item in data[key]
                ]
            else:
                # Handle simple types
                result[key] = TypeUtils.coerce_type(
                    data[key],
                    type_info
                )

    return result
```

## Error Handling

### Common Errors
1. TypeError for invalid types
2. ValueError for invalid values
3. KeyError for missing mappings
4. IndexError for sequences

### Error Prevention
```python
try:
    TypeValidator.validate_type(value, expected_type)
except TypeError as e:
    handle_type_error(e)

try:
    result = TypeUtils.coerce_type(value, target_type)
except ValueError as e:
    handle_value_error(e)
```

## Performance Considerations

### Optimization Tips
1. Cache type information
2. Batch validations
3. Use appropriate strictness
4. Handle common cases first

### Resource Management
1. Limit validation depth
2. Handle large collections
3. Use generators for sequences
4. Clean up temporary objects

## Integration Patterns

### Data Validation Layer
```python
class ValidationLayer:
    def __init__(self, schema: dict):
        self.schema = schema
        self._type_info = {
            key: TypeUtils.get_type_info(type_)
            for key, type_ in schema.items()
        }

    def validate(self, data: dict) -> dict:
        """Validate and convert data."""
        result = {}
        for key, type_info in self._type_info.items():
            if key in data:
                value = self
        value = self._validate_value(key, data[key])
                result[key] = value
        return result

    def _validate_value(self, key: str, value: Any) -> Any:
        """Validate and convert single value."""
        type_info = self._type_info[key]

        if type_info.is_optional and value is None:
            return None

        if type_info.is_sequence:
            return self._validate_sequence(value, type_info)

        if type_info.is_mapping:
            return self._validate_mapping(value, type_info)

        return TypeUtils.coerce_type(value, type_info.type_)
```

### Service Integration
```python
class TypeSafeService:
    """Service with type-safe operations."""

    def __init__(self, config: dict):
        self.config = self._validate_config(config)

    def _validate_config(self, config: dict) -> dict:
        """Validate service configuration."""
        required_keys = {"host", "port", "timeout"}

        TypeValidator.validate_mapping(
            config,
            str,
            object,
            required_keys=required_keys
        )

        return {
            "host": TypeUtils.coerce_type(config["host"], str),
            "port": TypeUtils.coerce_type(config["port"], int),
            "timeout": TypeUtils.coerce_type(config["timeout"], float)
        }

    def process_request(self, request: dict) -> dict:
        """Process request with type validation."""
        try:
            # Validate request
            TypeValidator.validate_mapping(
                request,
                str,
                object,
                required_keys={"action", "data"}
            )

            # Process based on action
            action = request["action"]
            data = request["data"]

            if action == "process_numbers":
                return self._process_numbers(data)
            elif action == "process_text":
                return self._process_text(data)
            else:
                raise ValueError(f"Unknown action: {action}")

        except (TypeError, ValueError) as e:
            return {"error": str(e)}

    def _process_numbers(self, data: Any) -> dict:
        """Process numeric data."""
        TypeValidator.validate_sequence(data, (int, float))
        return {
            "sum": sum(data),
            "count": len(data)
        }

    def _process_text(self, data: Any) -> dict:
        """Process text data."""
        TypeValidator.validate_type(data, str)
        return {
            "length": len(data),
            "words": len(data.split())
        }
```

## Advanced Usage

### Custom Type Handlers
```python
def register_type_handlers(service: TypeSafeService) -> None:
    """Register custom type handlers."""

    def handle_datetime(value: str) -> datetime:
        """Convert string to datetime."""
        try:
            return datetime.fromisoformat(value)
        except ValueError as e:
            raise TypeError(f"Invalid datetime: {e}")

    def handle_enum(value: str) -> Enum:
        """Convert string to enum."""
        try:
            return UserType[value.upper()]
        except KeyError as e:
            raise TypeError(f"Invalid enum value: {e}")

    # Register handlers
    service.type_handlers = {
        datetime: handle_datetime,
        UserType: handle_enum
    }
```

### Type-Safe Data Pipeline
```python
class DataPipeline:
    """Type-safe data processing pipeline."""

    def __init__(self, schema: dict):
        self.validator = ValidationLayer(schema)
        self.processors = []

    def add_processor(
        self,
        func: Callable[[dict], dict],
        input_schema: dict,
        output_schema: dict
    ) -> None:
        """Add type-safe processor."""
        self.processors.append({
            "func": func,
            "input_validator": ValidationLayer(input_schema),
            "output_validator": ValidationLayer(output_schema)
        })

    def process(self, data: dict) -> dict:
        """Process data through pipeline."""
        # Validate input
        current = self.validator.validate(data)

        # Run processors
        for processor in self.processors:
            # Validate processor input
            current = processor["input_validator"].validate(current)

            # Process data
            current = processor["func"](current)

            # Validate processor output
            current = processor["output_validator"].validate(current)

        return current
```

## Testing

### Test Strategies
1. Test basic type validation
2. Test complex type structures
3. Test error conditions
4. Test custom converters
5. Test integration patterns

### Example Tests
```python
def test_validation_layer():
    """Test validation layer."""
    schema = {
        "id": int,
        "name": str,
        "tags": List[str],
        "metadata": Dict[str, str]
    }

    validator = ValidationLayer(schema)

    # Test valid data
    data = {
        "id": "123",
        "name": "Test",
        "tags": ["a", "b", "c"],
        "metadata": {"source": "test"}
    }

    result = validator.validate(data)
    assert isinstance(result["id"], int)
    assert isinstance(result["tags"], list)
    assert all(isinstance(x, str) for x in result["tags"])
```

## Resources
- Python type hints documentation
- Type checking best practices
- Data validation patterns
- Performance optimization tips

## Next Steps

### Learning More
1. Study Python's type system
2. Explore type checking tools
3. Learn validation patterns
4. Review error handling

### Getting Help
1. Check documentation examples
2. Review test cases
3. Join developer community
4. Contribute improvements
