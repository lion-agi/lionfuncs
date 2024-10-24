"""Validation utilities.

This module provides comprehensive validation utilities with support for complex
validation rules, chaining, and customizable error handling.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Pattern,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from enum import Enum

from .base import UtilityGroup
from .exceptions import ValidationError

T = TypeVar("T")


@dataclass
class ValidationResult:
    """Validation result container."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    value: Any = None
    field: Optional[str] = None

    def __bool__(self) -> bool:
        return self.is_valid


class Validator(Generic[T]):
    """Base validator class."""

    def __init__(
        self, error_message: Optional[str] = None, field: Optional[str] = None
    ):
        self.error_message = error_message
        self.field = field
        self._chain: List[Validator] = []
        self._conditions: List[Callable[[T], bool]] = []

    def __call__(self, value: T) -> ValidationResult:
        """Validate value."""
        # Check conditions
        for condition in self._conditions:
            if not condition(value):
                return ValidationResult(
                    False,
                    [self.error_message or "Validation failed"],
                    value,
                    self.field,
                )

        # Run validation
        try:
            is_valid = self.validate(value)
            if not is_valid:
                return ValidationResult(
                    False,
                    [self.error_message or "Validation failed"],
                    value,
                    self.field,
                )
        except Exception as e:
            return ValidationResult(False, [str(e)], value, self.field)

        # Run chain
        for validator in self._chain:
            result = validator(value)
            if not result.is_valid:
                return result

        return ValidationResult(True, value=value, field=self.field)

    def validate(self, value: T) -> bool:
        """Perform validation."""
        raise NotImplementedError

    def chain(self, *validators: "Validator") -> "Validator":
        """Chain additional validators."""
        self._chain.extend(validators)
        return self

    def when(self, condition: Callable[[T], bool]) -> "Validator":
        """Add condition for validation."""
        self._conditions.append(condition)
        return self


class RequiredValidator(Validator[Any]):
    """Validate value is not None."""

    def validate(self, value: Any) -> bool:
        return value is not None


class TypeValidator(Validator[Any]):
    """Validate value type."""

    def __init__(
        self,
        expected_type: Union[Type[Any], Tuple[Type[Any], ...]],
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.expected_type = expected_type

    def validate(self, value: Any) -> bool:
        return isinstance(value, self.expected_type)


class RangeValidator(Validator[Union[int, float]]):
    """Validate numeric range."""

    def __init__(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Union[int, float]) -> bool:
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True


class LengthValidator(Validator[Union[str, Sequence]]):
    """Validate length."""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value: Union[str, Sequence]) -> bool:
        length = len(value)
        if self.min_length is not None and length < self.min_length:
            return False
        if self.max_length is not None and length > self.max_length:
            return False
        return True


class PatternValidator(Validator[str]):
    """Validate string pattern."""

    def __init__(
        self, pattern: Union[str, Pattern], *args: Any, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.pattern = (
            re.compile(pattern) if isinstance(pattern, str) else pattern
        )

    def validate(self, value: str) -> bool:
        return bool(self.pattern.match(value))


class EmailValidator(Validator[str]):
    """Validate email address."""

    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    def validate(self, value: str) -> bool:
        return bool(self.EMAIL_PATTERN.match(value))


class URLValidator(Validator[str]):
    """Validate URL."""

    URL_PATTERN = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    def validate(self, value: str) -> bool:
        return bool(self.URL_PATTERN.match(value))


class DateValidator(Validator[str]):
    """Validate date string."""

    def __init__(self, format: str = "%Y-%m-%d", *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.format = format

    def validate(self, value: str) -> bool:
        try:
            datetime.strptime(value, self.format)
            return True
        except ValueError:
            return False


class ChoiceValidator(Validator[Any]):
    """Validate value in choices."""

    def __init__(
        self,
        choices: Union[Sequence[Any], Set[Any], Type[Enum]],
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.choices = (
            set(choices)
            if not isinstance(choices, type) or not issubclass(choices, Enum)
            else set(choices.__members__.values())
        )

    def validate(self, value: Any) -> bool:
        return value in self.choices


class SchemaValidator(Validator[Dict[str, Any]]):
    """Validate dictionary schema."""

    def __init__(
        self,
        schema: Dict[str, Validator],
        allow_extra: bool = True,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.schema = schema
        self.allow_extra = allow_extra

    def validate(self, value: Dict[str, Any]) -> bool:
        if not isinstance(value, dict):
            return False

        # Check required fields
        for field, validator in self.schema.items():
            if isinstance(validator, RequiredValidator):
                if field not in value:
                    return False
                result = validator(value[field])
                if not result.is_valid:
                    return False

        # Check all fields
        for field, field_value in value.items():
            if field in self.schema:
                validator = self.schema[field]
                result = validator(field_value)
                if not result.is_valid:
                    return False
            elif not self.allow_extra:
                return False

        return True


class ValidationUtils(UtilityGroup):
    """Validation utility functions."""

    @classmethod
    def get_name(cls) -> str:
        return "validation_utils"

    @staticmethod
    def validate_required(
        error_message: Optional[str] = None, field: Optional[str] = None
    ) -> Validator[Any]:
        """Create required validator."""
        return RequiredValidator(error_message, field)

    @staticmethod
    def validate_type(
        expected_type: Union[Type[Any], Tuple[Type[Any], ...]],
        error_message: Optional[str] = None,
        field: Optional[str] = None,
    ) -> Validator[Any]:
        """Create type validator."""
        return TypeValidator(expected_type, error_message, field)

    @staticmethod
    def validate_range(
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        error_message: Optional[str] = None,
        field: Optional[str] = None,
    ) -> Validator[Union[int, float]]:
        """Create range validator."""
        return RangeValidator(min_value, max_value, error_message, field)

    @staticmethod
    def validate_length(
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        error_message: Optional[str] = None,
        field: Optional[str] = None,
    ) -> Validator[Union[str, Sequence]]:
        """Create length validator."""
        return LengthValidator(min_length, max_length, error_message, field)

    @staticmethod
    def validate_pattern(
        pattern: Union[str, Pattern],
        error_message: Optional[str] = None,
        field: Optional[str] = None,
    ) -> Validator[str]:
        """Create pattern validator."""
        return PatternValidator(pattern, error_message, field)

    @staticmethod
    def validate_email(
        error_message: Optional[str] = None, field: Optional[str] = None
    ) -> Validator[str]:
        """Create email validator."""
        return EmailValidator(error_message, field)

    @staticmethod
    def validate_url(
        error_message: Optional[str] = None, field: Optional[str] = None
    ) -> Validator[str]:
        """Create URL validator."""
        return URLValidator(error_message, field)

    @staticmethod
    def validate_date(
        format: str = "%Y-%m-%d",
        error_message: Optional[str] = None,
        field: Optional[str] = None,
    ) -> Validator[str]:
        """Create date validator."""
        return DateValidator(format, error_message, field)

    @staticmethod
    def validate_choice(
        choices: Union[Sequence[Any], Set[Any], Type[Enum]],
        error_message: Optional[str] = None,
        field: Optional[str] = None,
    ) -> Validator[Any]:
        """Create choice validator."""
        return ChoiceValidator(choices, error_message, field)

    @staticmethod
    def validate_schema(
        schema: Dict[str, Validator],
        allow_extra: bool = True,
        error_message: Optional[str] = None,
        field: Optional[str] = None,
    ) -> Validator[Dict[str, Any]]:
        """Create schema validator."""
        return SchemaValidator(schema, allow_extra, error_message, field)

    @staticmethod
    def create_validator(
        validation_func: Callable[[T], bool],
        error_message: Optional[str] = None,
        field: Optional[str] = None,
    ) -> Validator[T]:
        """Create custom validator."""

        class CustomValidator(Validator[T]):
            def validate(self, value: T) -> bool:
                return validation_func(value)

        return CustomValidator(error_message, field)
