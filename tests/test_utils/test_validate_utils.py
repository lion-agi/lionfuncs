"""Tests for validation utilities."""

from enum import Enum
from typing import Any, Dict, List
import pytest

from lionfuncs.utils.validation_utils import (
    ValidationUtils,
    ValidationResult,
    Validator,
)


class UserType(Enum):
    """Test enum for validation."""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class TestValidationUtils:
    """Test suite for ValidationUtils."""

    def test_required_validator(self):
        """Test required value validation."""
        validator = ValidationUtils.validate_required()

        # Valid cases
        assert validator("")
        assert validator(0)
        assert validator(False)

        # Invalid cases
        assert not validator(None)

        # Test with custom message
        validator = ValidationUtils.validate_required(
            error_message="Value required"
        )
        result = validator(None)
        assert not result
        assert result.errors == ["Value required"]

    def test_type_validator(self):
        """Test type validation."""
        # Single type
        validator = ValidationUtils.validate_type(int)
        assert validator(42)
        assert not validator("42")

        # Multiple types
        validator = ValidationUtils.validate_type((int, float))
        assert validator(42)
        assert validator(42.0)
        assert not validator("42")

        # Test with field name
        validator = ValidationUtils.validate_type(str, field="username")
        result = validator(42)
        assert not result
        assert result.field == "username"

    def test_range_validator(self):
        """Test numeric range validation."""
        validator = ValidationUtils.validate_range(0, 100)

        # Valid cases
        assert validator(0)
        assert validator(50)
        assert validator(100)

        # Invalid cases
        assert not validator(-1)
        assert not validator(101)

        # Test min only
        validator = ValidationUtils.validate_range(min_value=0)
        assert validator(0)
        assert validator(100)
        assert not validator(-1)

        # Test max only
        validator = ValidationUtils.validate_range(max_value=100)
        assert validator(0)
        assert validator(100)
        assert not validator(101)

    def test_length_validator(self):
        """Test length validation."""
        validator = ValidationUtils.validate_length(2, 5)
        # Valid cases
        assert validator("ab")
        assert validator("abc")
        assert validator("abcde")
        assert validator([1, 2, 3])

        # Invalid cases
        assert not validator("a")
        assert not validator("abcdef")
        assert not validator([])
        assert not validator([1, 2, 3, 4, 5, 6])

        # Test with custom message
        validator = ValidationUtils.validate_length(
            min_length=2, error_message="Invalid length"
        )
        result = validator("a")
        assert result.errors == ["Invalid length"]

    def test_pattern_validator(self):
        """Test pattern validation."""
        # Test with string pattern
        validator = ValidationUtils.validate_pattern(r"^\d{3}-\d{2}-\d{4}$")
        assert validator("123-45-6789")
        assert not validator("123-456-789")

        # Test with compiled pattern
        import re

        pattern = re.compile(r"^[A-Z][a-z]+$")
        validator = ValidationUtils.validate_pattern(pattern)
        assert validator("Hello")
        assert not validator("hello")
        assert not validator("Hello123")

    def test_email_validator(self):
        """Test email validation."""
        validator = ValidationUtils.validate_email()

        # Valid cases
        assert validator("user@example.com")
        assert validator("user.name+tag@example.co.uk")
        assert validator("123@example.com")

        # Invalid cases
        assert not validator("not.an.email")
        assert not validator("@example.com")
        assert not validator("user@.com")
        assert not validator("user@example.")
        assert not validator("user@exam ple.com")

    def test_url_validator(self):
        """Test URL validation."""
        validator = ValidationUtils.validate_url()

        # Valid cases
        assert validator("http://example.com")
        assert validator("https://example.com")
        assert validator("http://example.com/path")
        assert validator("http://example.com:8080")
        assert validator("http://localhost")
        assert validator("http://192.168.1.1")

        # Invalid cases
        assert not validator("not.a.url")
        assert not validator("ftp://example.com")
        assert not validator("http:/example.com")
        assert not validator("http://")
        assert not validator("http://invalid domain.com")

    def test_date_validator(self):
        """Test date validation."""
        # Test default format
        validator = ValidationUtils.validate_date()
        assert validator("2024-01-01")
        assert not validator("2024/01/01")

        # Test custom format
        validator = ValidationUtils.validate_date("%d/%m/%Y")
        assert validator("01/01/2024")
        assert not validator("2024-01-01")

        # Test invalid dates
        validator = ValidationUtils.validate_date()
        assert not validator("2024-13-01")  # Invalid month
        assert not validator("2024-01-32")  # Invalid day
        assert not validator("not-a-date")

    def test_choice_validator(self):
        """Test choice validation."""
        # Test with sequence
        validator = ValidationUtils.validate_choice([1, 2, 3])
        assert validator(1)
        assert validator(2)
        assert not validator(4)

        # Test with set
        validator = ValidationUtils.validate_choice({"a", "b", "c"})
        assert validator("a")
        assert not validator("d")

        # Test with enum
        validator = ValidationUtils.validate_choice(UserType)
        assert validator(UserType.ADMIN)
        assert validator(UserType.USER)
        assert not validator("admin")

    def test_schema_validator(self):
        """Test schema validation."""
        schema = {
            "username": ValidationUtils.validate_required()
            .chain(ValidationUtils.validate_type(str))
            .chain(ValidationUtils.validate_length(3, 20)),
            "age": ValidationUtils.validate_type(int).chain(
                ValidationUtils.validate_range(0, 150)
            ),
            "email": ValidationUtils.validate_email(),
        }

        validator = ValidationUtils.validate_schema(schema)

        # Valid case
        valid_data = {
            "username": "testuser",
            "age": 25,
            "email": "test@example.com",
        }
        assert validator(valid_data)

        # Invalid cases
        assert not validator({})  # Missing required
        assert not validator(
            {
                "username": "te",  # Too short
                "age": 25,
                "email": "test@example.com",
            }
        )
        assert not validator(
            {
                "username": "testuser",
                "age": -1,  # Out of range
                "email": "test@example.com",
            }
        )
        assert not validator(
            {
                "username": "testuser",
                "age": 25,
                "email": "not.an.email",  # Invalid email
            }
        )

    def test_validator_chaining(self):
        """Test validator chaining."""
        validator = ValidationUtils.validate_required().chain(
            ValidationUtils.validate_type(str),
            ValidationUtils.validate_length(3, 10),
        )

        # Valid case
        assert validator("test")

        # Invalid cases - fails different parts of chain
        assert not validator(None)  # Fails required
        assert not validator(123)  # Fails type
        assert not validator("ab")  # Fails length

    def test_conditional_validation(self):
        """Test conditional validation."""

        def is_premium(user: dict) -> bool:
            return user.get("type") == "premium"

        schema = {
            "type": ValidationUtils.validate_choice({"basic", "premium"}),
            "credit": ValidationUtils.validate_type(int)
            .when(is_premium)
            .chain(ValidationUtils.validate_range(min_value=1000)),
        }

        validator = ValidationUtils.validate_schema(schema)

        # Valid cases
        assert validator({"type": "basic", "credit": 100})
        assert validator({"type": "premium", "credit": 1000})

        # Invalid case - premium requires minimum credit
        assert not validator({"type": "premium", "credit": 500})

    def test_custom_validator(self):
        """Test custom validator creation."""

        def is_even(value: int) -> bool:
            return value % 2 == 0

        validator = ValidationUtils.create_validator(
            is_even, error_message="Must be even"
        )

        assert validator(2)
        assert validator(0)
        assert not validator(1)

        result = validator(3)
        assert result.errors == ["Must be even"]

    def test_real_world_validation(self):
        """Test real-world validation scenarios."""
        # User registration validation
        user_schema = {
            "username": ValidationUtils.validate_required()
            .chain(ValidationUtils.validate_type(str))
            .chain(ValidationUtils.validate_length(3, 20))
            .chain(ValidationUtils.validate_pattern(r"^[a-zA-Z0-9_]+$")),
            "email": ValidationUtils.validate_required().chain(
                ValidationUtils.validate_email()
            ),
            "password": ValidationUtils.validate_required()
            .chain(ValidationUtils.validate_type(str))
            .chain(ValidationUtils.validate_length(8, 50))
            .chain(
                ValidationUtils.validate_pattern(
                    r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$"
                )
            ),
            "age": ValidationUtils.validate_type(int).chain(
                ValidationUtils.validate_range(13, 150)
            ),
            "preferences": ValidationUtils.validate_schema(
                {
                    "newsletter": ValidationUtils.validate_type(bool),
                    "theme": ValidationUtils.validate_choice(
                        ["light", "dark"]
                    ),
                }
            ),
        }

        validator = ValidationUtils.validate_schema(user_schema)

        # Valid user
        valid_user = {
            "username": "testuser123",
            "email": "test@example.com",
            "password": "SecurePass123",
            "age": 25,
            "preferences": {"newsletter": True, "theme": "dark"},
        }
        assert validator(valid_user)

        # Invalid cases
        invalid_users = [
            {  # Invalid username
                "username": "test@user",
                "email": "test@example.com",
                "password": "SecurePass123",
                "age": 25,
                "preferences": {"newsletter": True, "theme": "dark"},
            },
            {  # Weak password
                "username": "testuser123",
                "email": "test@example.com",
                "password": "weak",
                "age": 25,
                "preferences": {"newsletter": True, "theme": "dark"},
            },
            {  # Invalid theme
                "username": "testuser123",
                "email": "test@example.com",
                "password": "SecurePass123",
                "age": 25,
                "preferences": {"newsletter": True, "theme": "blue"},
            },
        ]

        for user in invalid_users:
            assert not validator(user)

    def test_performance(self, benchmark):
        """Test validation performance."""

        def bench_validation():
            # Create complex schema
            schema = {
                "id": ValidationUtils.validate_type(int),
                "name": ValidationUtils.validate_required()
                .chain(ValidationUtils.validate_type(str))
                .chain(ValidationUtils.validate_length(1, 100)),
                "email": ValidationUtils.validate_email(),
                "settings": ValidationUtils.validate_schema(
                    {
                        "notifications": ValidationUtils.validate_type(bool),
                        "theme": ValidationUtils.validate_choice(
                            ["light", "dark"]
                        ),
                    }
                ),
                "tags": ValidationUtils.validate_type(list).chain(
                    ValidationUtils.validate_length(max_length=10)
                ),
            }

            validator = ValidationUtils.validate_schema(schema)

            # Validate multiple objects
            data = [
                {
                    "id": i,
                    "name": f"test{i}",
                    "email": f"test{i}@example.com",
                    "settings": {"notifications": True, "theme": "light"},
                    "tags": ["tag1", "tag2"],
                }
                for i in range(100)
            ]

            for item in data:
                validator(item)

        benchmark(bench_validation)
