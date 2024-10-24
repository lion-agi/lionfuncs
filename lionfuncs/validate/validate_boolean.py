"""
Boolean validation utilities with comprehensive value support.

Features:
- Handle multiple boolean string representations
- Support numeric and complex values
- Case-insensitive matching
- Clear error messages
- Type-safe validation
"""

from numbers import Complex
from typing import Any, FrozenSet

# Define constants for valid boolean string representations
TRUE_VALUES: FrozenSet[str] = frozenset(
    [
        "true",
        "1",
        "yes",
        "y",
        "on",
        "correct",
        "t",
        "enabled",
        "enable",
        "active",
        "activated",
    ]
)

FALSE_VALUES: FrozenSet[str] = frozenset(
    [
        "false",
        "0",
        "no",
        "n",
        "off",
        "incorrect",
        "f",
        "disabled",
        "disable",
        "inactive",
        "deactivated",
        "none",
        "null",
        "n/a",
        "na",
    ]
)


def validate_boolean(x: Any, /) -> bool:
    """
    Forcefully validate and convert input to boolean value.

    Converts various input types to boolean with extensive support for
    common string representations. Case-insensitive and whitespace-tolerant.

    Args:
        x: Input to convert. Supports:
           - Boolean: returned as-is
           - Number (including complex): uses Python bool rules
           - String: matches against common representations
           - None: raises TypeError
           - Others: converted to string first

    Returns:
        bool: Boolean representation of input.

    Raises:
        ValueError: If input cannot be unambiguously converted.
        TypeError: If input type unsupported or None.

    Examples:
        >>> validate_boolean(True)
        True
        >>> validate_boolean("yes")
        True
        >>> validate_boolean("OFF")
        False
        >>> validate_boolean(1)
        True
        >>> validate_boolean(0j)
        False
        >>> validate_boolean(1 + 1j)
        True

    Notes:
        - Case-insensitive matching
        - Strips whitespace
        - Numeric values use Python's bool()
        - Complex numbers: bool(0j) is False, others True
        - None values raise TypeError
        - Empty strings raise ValueError
    """
    # Handle None
    if x is None:
        raise TypeError("Cannot convert None to boolean")

    # Handle boolean
    if isinstance(x, bool):
        return x

    # Handle numeric types
    if isinstance(x, (int, float, Complex)):
        return bool(x)

    # Convert to string if needed
    if not isinstance(x, str):
        try:
            x = str(x)
        except Exception as e:
            raise TypeError(
                "Cannot convert {} to boolean: {}".format(
                    type(x).__name__, str(e)
                )
            )

    # Process string input
    x_cleaned = str(x).strip().lower()

    # Handle empty string
    if not x_cleaned:
        raise ValueError("Cannot convert empty string to boolean")

    # Check against known values
    if x_cleaned in TRUE_VALUES:
        return True

    if x_cleaned in FALSE_VALUES:
        return False

    # Try numeric conversion as last resort
    try:
        # Handle complex numbers
        if "j" in x_cleaned:
            try:
                return bool(complex(x_cleaned))
            except ValueError:
                pass
        # Handle regular numbers
        return bool(float(x_cleaned))
    except ValueError:
        pass

    # Raise detailed error if no conversion possible
    raise ValueError(
        "Cannot convert '{}' to boolean. Valid true values are: {}, "
        "valid false values are: {}".format(
            x, sorted(TRUE_VALUES), sorted(FALSE_VALUES)
        )
    )


__all__ = ["validate_boolean", "TRUE_VALUES", "FALSE_VALUES"]
