# Validation Utilities Documentation

## Overview

The `ValidationUtils` module provides comprehensive validation utilities with support for:
- Basic value validation (required, type, range)
- String validation (pattern, email, URL)
- Collection validation (length, choice)
- Schema validation
- Custom validators
- Validator chaining
- Conditional validation

## Core Features

### Basic Validation
```python
from lionfuncs.utils import ValidationUtils

# Required value
validator = ValidationUtils.validate_required()
result = validator(value)

# Type checking
validator = ValidationUtils.validate_type(int)
result = validator(42)

# Range validation
validator = ValidationUtils.validate_range(0, 100)
result = validator(50)

# Length validation
validator = ValidationUtils.validate_length(2, 10)
result = validator("test")
```

### String Validation
```python
# Pattern validation
validator = ValidationUtils.validate_pattern(r"^\d{3}-\d{2}-\d{4}$")
result = validator("123-45-6789")

# Email validation
validator = ValidationUtils.validate_email()
result = validator("user@example.com")

# URL validation
validator = ValidationUtils.validate_url()
result = validator("https://example.com")
```

### Collection Validation
```python
# Choice validation
validator = ValidationUtils.validate_choice(["a", "b", "c"])
result = validator("a")

# Enum validation
validator = ValidationUtils.validate_choice(UserType)
result = validator(UserType.ADMIN)
```

## Best Practices

### 1. Schema Validation
```python
# Define schema
user_schema = {
    "username": ValidationUtils.validate_required()
        .chain(ValidationUtils.validate_type(str))
        .chain(ValidationUtils.validate_length(3, 20)),
    "email": ValidationUtils.validate_email(),
    "age": ValidationUtils.validate_type(int)
        .chain(ValidationUtils.validate_range(0, 150))
}

# Create validator
validator = ValidationUtils.validate_schema(user_schema)

# Validate data
result = validator({
    "username": "testuser",
    "email": "test@example.com",
    "age": 25
})
```

### 2. Validator Chaining
```python
# Chain multiple validators
validator = (
    ValidationUtils.validate_required()
    .chain(
        ValidationUtils.validate_type(str),
        ValidationUtils.validate_length(3, 20),
        ValidationUtils.validate_pattern(r"^[a-zA-Z0-9]+$")
    )
)

# Validate
result = validator("testuser123")
```

### 3. Conditional Validation
```python
def is_premium(user):
    return user.get("type") == "premium"

# Create conditional validator
validator = ValidationUtils.validate_range(1000)
    .when(is_premium)

# Validate based on condition
result = validator({"type": "premium", "credit": 2000})
```

## Common Patterns

### Form Validation
```python
def validate_form(form_data: dict) -> ValidationResult:
    """Validate form data."""
    schema = {
        "name": ValidationUtils.validate_required()
            .chain(ValidationUtils.validate_type(str))
            .chain(ValidationUtils.validate_length(2, 50)),
        "email": ValidationUtils.validate_required()
            .chain(ValidationUtils.validate_email()),
        "age": ValidationUtils.validate_type(int)
            .chain(ValidationUtils.validate_range(18, 150)),
        "preferences": ValidationUtils.validate_schema({
            "newsletter": ValidationUtils.validate_type(bool),
            "theme": ValidationUtils.validate_choice(
                ["light", "dark"]
            )
        })
    }

    validator = ValidationUtils.validate_schema(schema)
    return validator(form_data)
```

### Data Validation
```python
class DataValidator:
    """Data validation service."""

    def __init__(self):
        """Initialize validators."""
        self.validators = {
            'user': self._create_user_validator(),
            'order': self._create_order_validator(),
            'product': self._create_product_validator()
        }

    def _create_user_validator(self):
        return ValidationUtils.validate_schema({
            "id": ValidationUtils.validate_type(str),
            "email": ValidationUtils.validate_email(),
            "status": ValidationUtils.validate_choice(
                ["active", "inactive", "pending"]
            )
        })

    def validate(self, data_type: str, data: dict) -> ValidationResult:
        """Validate data by type."""
        validator = self.validators.get(data_type)
        if not validator:
            raise ValueError(f"Unknown data type: {data_type}")
        return validator(data)
```

### API Validation
```python
class APIValidator:
    """API request/response validation."""

    def validate_request(self, endpoint: str, data: dict) -> ValidationResult:
        """Validate API request data."""
        schema = {
            "/users": {
                "name": ValidationUtils.validate_required()
                    .chain(ValidationUtils.validate_type(str)),
                "email": ValidationUtils.validate_email()
            },
            "/orders": {
                "user_id": ValidationUtils.validate_required(),
                "items": ValidationUtils.validate_type(list)
                    .chain(ValidationUtils.validate_length(min_length=1))
            }
        }

        validator = ValidationUtils.validate_schema(
            schema.get(endpoint, {})
        )
        return validator(data)
```

## Error Handling

### Validation Results
```python
def process_validation(result: ValidationResult) -> None:
    """Handle validation result."""
    if not result.is_valid:
        if result.field:
            print(f"Validation failed for {result.field}")
        for error in result.errors:
            print(f"Error: {error}")
```

### Custom Error Messages
```python
# Set custom messages for validators
validator = ValidationUtils.validate_required(
    error_message="This field cannot be empty"
)

validator = ValidationUtils.validate_length(
    min_length=3,
    max_length=20,
    error_message="Length must be between 3 and 20 characters"
)
```

### Error Aggregation
```python
def validate_multiple(items: list) -> list[ValidationResult]:
    """Validate multiple items."""
    validator = ValidationUtils.validate_schema({
        "id": ValidationUtils.validate_required(),
        "value": ValidationUtils.validate_type(int)
    })

    results = []
    for item in items:
        result = validator(item)
        if not result.is_valid:
            results.append(result)
    return results
```

## Advanced Usage

### Custom Validators
```python
def create_custom_validator():
    """Create validator with custom logic."""
    def validate_password_strength(value: str) -> bool:
        has_upper = any(c.isupper() for c in value)
        has_lower = any(c.islower() for c in value)
        has_digit = any(c.isdigit() for c in value)
        return has_upper and has_lower and has_digit

    return ValidationUtils.create_validator(
        validate_password_strength,
        error_message="Password must contain upper, lower and digits"
    )
```

### Complex Validation Logic
```python
def create_dependent_validator():
    """Create validator with dependent fields."""
    def validate_dates(data: dict) -> bool:
        start = data.get("start_date")
        end = data.get("end_date")
        if not (start and end):
            return False
        return start < end

    return ValidationUtils.validate_schema({
        "start_date": ValidationUtils.validate_date(),
        "end_date": ValidationUtils.validate_date()
    }).chain(
        ValidationUtils.create_validator(
            validate_dates,
            error_message="End date must be after start date"
        )
    )
```

## Performance Considerations

### Optimization Tips
1. Cache validators for reuse
2. Use appropriate validation chains
3. Consider validation order
4. Handle large datasets efficiently

### Resource Management
```python
class ValidatorCache:
    """Cache commonly used validators."""

    def __init__(self):
        self._validators = {}

    def get_validator(self, key: str) -> Validator:
        """Get or create validator."""
        if key not in self._validators:
            self._validators[key] = self._create_validator(key)
        return self._validators[key]

    def _create_validator(self, key: str) -> Validator:
        """Create new validator."""
        # Create based on key
        pass
```

## Integration Patterns

### Framework Integration
```python
class ValidationMiddleware:
    """Validation middleware for web framework."""

    def __init__(self, schema: dict):
        self.validator = ValidationUtils.validate_schema(schema)

    async def __call__(self, request):
        """Validate request data."""
        data = await request.json()
        result = self.validator(data)
        if not result.is_valid:
            return JSONResponse({
                "errors": result.errors
            }, status_code=400)
        return await self.next(request)
```

### Service Integration
```python
class ValidationService:
    """Validation service for application."""

    def __init__(self):
        self.validators = self._load_validators()

    def _load_validators(self) -> dict:
        """Load validators from configuration."""
        config = load_config()
        return {
            name: self._create_validator(schema)
            for name, schema in config.items()
        }

    def validate(
        self,
        name: str,
        data: Any
    ) -> ValidationResult:
        """Validate data using named validator."""
        validator = self.validators.get(name)
        if not validator:
            raise ValueError(f"Unknown validator: {name}")
        return validator(data)
```

## Testing

### Test Strategies
1. Test basic validation
2. Test error conditions
3. Test custom validators
4. Test integration points
5. Test performance

### Example Tests
```python
def test_validation():
    """Test validation scenarios."""
    # Create validator
    validator = ValidationUtils.validate_schema({
        "id": ValidationUtils.validate_required(),
        "name": ValidationUtils.validate_type(str),
        "age": ValidationUtils.validate_range(0, 150)
    })

    # Test valid case
    result = validator({
        "id": "123",
        "name": "Test",
        "age": 25
    })
    assert result.is_valid

    # Test invalid case
    result = validator({
        "name": 123,  # Wrong type
        "age": -1     # Out of range
    })
    assert not result.is_valid
```

## Additional Resources
- Python type hints documentation
- Regular expression patterns
- Validation best practices
- Performance optimization tips

## Next Steps

### Learning More
1. Study common validation patterns
2. Review error handling strategies
3. Learn about custom validators
4. Understand integration patterns

### Getting Help
1. Check documentation examples
2. Review test cases
3. Join developer community
4. Contribute improvements
