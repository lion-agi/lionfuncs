"""Type checking and manipulation utilities.

This module provides comprehensive utilities for type checking, validation,
and conversion with support for complex types and runtime validation.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from inspect import isclass
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)
from types import GenericAlias, UnionType

from .base import UtilityGroup
from .exceptions import ValidationError

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class TypeInfo:
    """Type information container."""

    type_: Type[Any]
    origin: Optional[Type[Any]]
    args: Tuple[Type[Any], ...]
    is_optional: bool
    is_sequence: bool
    is_mapping: bool
    is_union: bool
    is_generic: bool

    @classmethod
    def from_type(cls, type_: Type[Any]) -> "TypeInfo":
        """Create TypeInfo from type."""
        origin = get_origin(type_)
        args = get_args(type_)

        return cls(
            type_=type_,
            origin=origin,
            args=args,
            is_optional=_is_optional(type_),
            is_sequence=_is_sequence_type(type_),
            is_mapping=_is_mapping_type(type_),
            is_union=_is_union_type(type_),
            is_generic=origin is not None,
        )


class TypeValidator:
    """Type validation utilities."""

    @staticmethod
    def validate_type(
        value: Any,
        expected_type: Union[Type[Any], Tuple[Type[Any], ...]],
        allow_none: bool = False,
        param_name: Optional[str] = None,
    ) -> None:
        """Validate value matches expected type.

        Args:
            value: Value to validate
            expected_type: Expected type(s)
            allow_none: Allow None values
            param_name: Parameter name for error messages

        Raises:
            TypeError: If validation fails
        """
        if allow_none and value is None:
            return

        if isinstance(expected_type, tuple):
            valid = isinstance(value, expected_type)
        else:
            valid = isinstance(value, expected_type)

        if not valid:
            type_names = (
                tuple(t.__name__ for t in expected_type)
                if isinstance(expected_type, tuple)
                else expected_type.__name__
            )
            param_str = f" for parameter '{param_name}'" if param_name else ""
            raise TypeError(
                f"Expected type {type_names}{param_str}, "
                f"got {type(value).__name__}"
            )

    @staticmethod
    def validate_sequence(
        value: Any,
        item_type: Type[T],
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        allow_empty: bool = True,
    ) -> None:
        """Validate sequence type and contents.

        Args:
            value: Sequence to validate
            item_type: Expected item type
            min_length: Minimum length
            max_length: Maximum length
            allow_empty: Allow empty sequence
        """
        if not isinstance(value, Sequence):
            raise TypeError(f"Expected sequence, got {type(value).__name__}")

        if not allow_empty and not value:
            raise ValueError("Sequence cannot be empty")

        length = len(value)
        if min_length is not None and length < min_length:
            raise ValueError(
                f"Sequence length {length} is less than minimum {min_length}"
            )

        if max_length is not None and length > max_length:
            raise ValueError(
                f"Sequence length {length} is greater than maximum {max_length}"
            )

        for item in value:
            if not isinstance(item, item_type):
                raise TypeError(
                    f"Invalid sequence item type: expected {item_type.__name__}, "
                    f"got {type(item).__name__}"
                )

    @staticmethod
    def validate_mapping(
        value: Any,
        key_type: Type[T],
        value_type: Type[U],
        required_keys: Optional[Set[T]] = None,
        allow_extra: bool = True,
    ) -> None:
        """Validate mapping type and contents.

        Args:
            value: Mapping to validate
            key_type: Expected key type
            value_type: Expected value type
            required_keys: Required keys
            allow_extra: Allow extra keys
        """
        if not isinstance(value, Mapping):
            raise TypeError(f"Expected mapping, got {type(value).__name__}")

        # Check required keys
        if required_keys:
            missing = required_keys - set(value.keys())
            if missing:
                raise ValueError(f"Missing required keys: {missing}")

        # Check key/value types
        for k, v in value.items():
            if not isinstance(k, key_type):
                raise TypeError(
                    f"Invalid key type: expected {key_type.__name__}, "
                    f"got {type(k).__name__}"
                )

            if not isinstance(v, value_type):
                raise TypeError(
                    f"Invalid value type for key {k}: "
                    f"expected {value_type.__name__}, got {type(v).__name__}"
                )

        # Check extra keys
        if not allow_extra and required_keys:
            extra = set(value.keys()) - required_keys
            if extra:
                raise ValueError(f"Extra keys not allowed: {extra}")


class TypeUtils(UtilityGroup):
    """Type utility functions."""

    @classmethod
    def get_name(cls) -> str:
        return "type_utils"

    @staticmethod
    def coerce_type(
        value: Any,
        target_type: Type[T],
        strict: bool = False,
        custom_converters: Optional[
            Dict[Type[Any], Callable[[Any], T]]
        ] = None,
    ) -> T:
        """Coerce value to target type.

        Args:
            value: Value to coerce
            target_type: Target type
            strict: Use strict type checking
            custom_converters: Custom type converters

        Returns:
            Coerced value

        Raises:
            TypeError: If coercion fails
        """
        # Already correct type
        if isinstance(value, target_type):
            return value

        # Use custom converter if available
        if custom_converters and type(value) in custom_converters:
            return custom_converters[type(value)](value)

        try:
            # Handle bool specially
            if target_type == bool and isinstance(value, str):
                lower_value = value.lower()
                if lower_value in ("true", "1", "yes", "y", "on"):
                    return True
                if lower_value in ("false", "0", "no", "n", "off"):
                    return False
                raise ValueError(f"Cannot convert '{value}' to bool")

            # Try direct conversion
            result = target_type(value)

            # Strict check
            if strict and type(result) != target_type:
                raise TypeError(
                    f"Conversion resulted in type {type(result).__name__}, "
                    f"expected {target_type.__name__}"
                )

            return result
        except (ValueError, TypeError) as e:
            raise TypeError(
                f"Cannot coerce {value} ({type(value).__name__}) "
                f"to {target_type.__name__}: {e}"
            )

    @staticmethod
    def get_type_info(type_: Type[Any]) -> TypeInfo:
        """Get type information."""
        return TypeInfo.from_type(type_)

    @staticmethod
    def check_subtype(type_: Type[Any], parent_type: Type[Any]) -> bool:
        """Check if type is subtype of parent_type."""
        try:
            origin = get_origin(type_) or type_
            parent_origin = get_origin(parent_type) or parent_type

            # Handle Union types
            if _is_union_type(parent_type):
                return any(
                    TypeUtils.check_subtype(type_, t)
                    for t in get_args(parent_type)
                )

            # Handle generic types
            if parent_origin is not None and origin is not None:
                if not issubclass(origin, parent_origin):
                    return False

                # Check type arguments
                type_args = get_args(type_)
                parent_args = get_args(parent_type)

                if len(type_args) != len(parent_args):
                    return False

                return all(
                    TypeUtils.check_subtype(arg, parent_arg)
                    for arg, parent_arg in zip(type_args, parent_args)
                )

            return issubclass(origin, parent_origin)
        except TypeError:
            return False

    @staticmethod
    def validate_callable(
        func: Callable[..., Any],
        expected_params: Optional[int] = None,
        return_type: Optional[Type[Any]] = None,
    ) -> None:
        """Validate callable signature.

        Args:
            func: Callable to validate
            expected_params: Expected parameter count
            return_type: Expected return type
        """
        if not callable(func):
            raise TypeError(f"Expected callable, got {type(func).__name__}")

        # Check parameter count
        if expected_params is not None:
            import inspect

            sig = inspect.signature(func)
            param_count = len(sig.parameters)

            if param_count != expected_params:
                raise ValueError(
                    f"Expected {expected_params} parameters, got {param_count}"
                )

        # Check return type annotation
        if return_type is not None:
            hints = get_type_hints(func)
            if "return" not in hints:
                raise ValueError("Missing return type annotation")

            actual_return = hints["return"]
            if not TypeUtils.check_subtype(actual_return, return_type):
                raise TypeError(
                    f"Invalid return type: expected {return_type.__name__}, "
                    f"got {actual_return.__name__}"
                )


# Helper functions
def _is_optional(type_: Type[Any]) -> bool:
    """Check if type is Optional."""
    origin = get_origin(type_)
    args = get_args(type_)
    return origin is Union and len(args) == 2 and type(None) in args


def _is_sequence_type(type_: Type[Any]) -> bool:
    """Check if type is sequence type."""
    origin = get_origin(type_) or type_
    return (
        origin is not str  # Exclude str
        and isinstance(origin, type)
        and issubclass(origin, Sequence)
    )


def _is_mapping_type(type_: Type[Any]) -> bool:
    """Check if type is mapping type."""
    origin = get_origin(type_) or type_
    return isinstance(origin, type) and issubclass(origin, Mapping)


def _is_union_type(type_: Type[Any]) -> bool:
    """Check if type is Union type."""
    origin = get_origin(type_)
    return origin is Union or isinstance(type_, UnionType)
