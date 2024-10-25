"""
Numeric type conversion utilities with comprehensive format support.

Features:
- Convert various inputs to numeric types
- Support multiple numeric formats
- Handle complex numbers
- Bounds checking and precision
- Comprehensive error handling
"""

import re
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

# Type definitions and constants
NumericType = TypeVar("NumericType", int, float, complex)

# Type mapping
TYPE_MAP = {"int": int, "float": float, "complex": complex}

# Regex patterns for numeric formats
PATTERNS = {
    "scientific": r"[-+]?(?:\d*\.)?\d+[eE][-+]?\d+",
    "complex_sci": r"[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?[-+](?:\d*\.)?\d+(?:[eE][-+]?\d+)?[jJ]",
    "complex": r"[-+]?(?:\d*\.)?\d+[-+](?:\d*\.)?\d+[jJ]",
    "pure_imaginary": r"[-+]?(?:\d*\.)?\d*[jJ]",
    "percentage": r"[-+]?(?:\d*\.)?\d+%",
    "fraction": r"[-+]?\d+/\d+",
    "decimal": r"[-+]?(?:\d*\.)?\d+",
    "special": r"[-+]?(?:inf|infinity|nan)",
}


def extract_numbers(text: str) -> List[Tuple[str, str]]:
    """
    Extract numeric values from text using ordered regex patterns.

    Args:
        text: Text to extract numbers from.

    Returns:
        List of tuples (pattern_type, matched_value).
    """
    combined_pattern = "|".join(PATTERNS.values())
    matches = re.finditer(combined_pattern, text, re.IGNORECASE)
    numbers = []

    for match in matches:
        value = match.group()
        for pattern_name, pattern in PATTERNS.items():
            if re.fullmatch(pattern, value, re.IGNORECASE):
                numbers.append((pattern_name, value))
                break

    return numbers


def validate_num_type(num_type: Union[str, Type]) -> Type:
    """
    Validate and normalize numeric type specification.

    Args:
        num_type: Numeric type to validate.

    Returns:
        Normalized Python type object.

    Raises:
        ValueError: If type specification invalid.
    """
    if isinstance(num_type, str):
        if num_type not in TYPE_MAP:
            raise ValueError("Invalid number type: {}".format(num_type))
        return TYPE_MAP[num_type]

    if num_type not in (int, float, complex):
        raise ValueError("Invalid number type: {}".format(num_type))
    return num_type


def infer_type(value: Tuple[str, str]) -> Type:
    """Infer appropriate numeric type from value."""
    pattern_type, _ = value
    if pattern_type in ("complex", "complex_sci", "pure_imaginary"):
        return complex
    return float


def convert_special(value: str) -> float:
    """Convert special float values (inf, -inf, nan)."""
    value = value.lower()
    if "infinity" in value or "inf" in value:
        return float("-inf") if value.startswith("-") else float("inf")
    return float("nan")


def convert_percentage(value: str) -> float:
    """Convert percentage string to float."""
    try:
        return float(value.rstrip("%")) / 100
    except ValueError as e:
        raise ValueError("Invalid percentage value: {}".format(value)) from e


def convert_complex(value: str) -> complex:
    """Convert complex number string to complex."""
    try:
        if value.endswith("j") or value.endswith("J"):
            if value in ("j", "J", "+j", "+J"):
                return complex(0, 1)
            if value in ("-j", "-J"):
                return complex(0, -1)
            if "+" not in value and "-" not in value[1:]:
                imag = float(value[:-1] or "1")
                return complex(0, imag)
        return complex(value.replace(" ", ""))
    except ValueError as e:
        raise ValueError("Invalid complex number: {}".format(value)) from e


def convert_type(
    value: Union[float, complex],
    target_type: Type,
    inferred_type: Type,
) -> Union[int, float, complex]:
    """Convert value to target type if specified."""
    try:
        if target_type is float and inferred_type is complex:
            return value
        if target_type is int and isinstance(value, complex):
            raise TypeError("Cannot convert complex number to int")
        return target_type(value)
    except (ValueError, TypeError) as e:
        raise TypeError(
            "Cannot convert {} to {}".format(value, target_type.__name__)
        ) from e


def apply_bounds(
    value: Union[float, complex],
    upper_bound: Optional[float] = None,
    lower_bound: Optional[float] = None,
) -> Union[float, complex]:
    """Apply bounds checking to numeric value."""
    if isinstance(value, complex):
        return value

    if upper_bound is not None and value > upper_bound:
        raise ValueError(
            "Value {} exceeds upper bound {}".format(value, upper_bound)
        )
    if lower_bound is not None and value < lower_bound:
        raise ValueError(
            "Value {} below lower bound {}".format(value, lower_bound)
        )
    return value


def apply_precision(
    value: Union[float, complex],
    precision: Optional[int],
) -> Union[float, complex]:
    """Apply precision rounding to numeric value."""
    if precision is None or isinstance(value, complex):
        return value
    if isinstance(value, float):
        return round(value, precision)
    return value


def parse_number(type_and_value: Tuple[str, str]) -> Union[float, complex]:
    """Parse string to numeric value based on pattern type."""
    num_type, value = type_and_value
    value = value.strip()

    try:
        # Handle different numeric types
        if num_type == "special":
            return convert_special(value)
        elif num_type == "percentage":
            return convert_percentage(value)
        elif num_type == "fraction":
            if "/" not in value or value.count("/") > 1:
                raise ValueError("Invalid fraction: {}".format(value))
            num, denom = value.split("/")
            if not (num.strip("-").isdigit() and denom.isdigit()):
                raise ValueError("Invalid fraction: {}".format(value))
            denom_val = float(denom)
            if denom_val == 0:
                raise ValueError("Division by zero")
            return float(num) / denom_val
        elif num_type in ("complex", "complex_sci", "pure_imaginary"):
            return convert_complex(value)
        elif num_type == "scientific":
            if "e" not in value.lower():
                raise ValueError(
                    "Invalid scientific notation: {}".format(value)
                )
            parts = value.lower().split("e")
            if len(parts) != 2 or not parts[1].lstrip("+-").isdigit():
                raise ValueError(
                    "Invalid scientific notation: {}".format(value)
                )
            return float(value)
        elif num_type == "decimal":
            return float(value)
        else:
            raise ValueError("Unknown number type: {}".format(num_type))

    except Exception as e:
        raise type(e)(
            "Failed to parse {} as {}: {}".format(value, num_type, str(e))
        )


def to_num(
    input_value: Any,
    *,
    upper_bound: Optional[Union[int, float]] = None,
    lower_bound: Optional[Union[int, float]] = None,
    num_type: Union[str, Type] = float,
    precision: Optional[int] = None,
    num_count: int = 1,
) -> Union[int, float, complex, List[Union[int, float, complex]]]:
    """
    Convert input to numeric type(s) with validation.

    Args:
        input_value: Input to convert.
        upper_bound: Maximum allowed value.
        lower_bound: Minimum allowed value.
        num_type: Target numeric type.
        precision: Decimal places for rounding.
        num_count: Number of values to extract.

    Returns:
        Converted number(s).

    Example:
        >>> to_num("42.5", num_type="int")
        42
        >>> to_num("1.5 + 2.5j", num_type="complex")
        (1.5+2.5j)
    """
    # Validate input
    if isinstance(input_value, (list, tuple)):
        raise TypeError("Input cannot be a sequence")

    # Handle boolean input
    if isinstance(input_value, bool):
        return validate_num_type(num_type)(input_value)

    # Handle direct numeric input
    if isinstance(input_value, (int, float, complex, Decimal)):
        inferred_type = type(input_value)
        if isinstance(input_value, Decimal):
            inferred_type = float
        value = (
            float(input_value)
            if not isinstance(input_value, complex)
            else input_value
        )
        value = apply_bounds(value, upper_bound, lower_bound)
        value = apply_precision(value, precision)
        return convert_type(value, validate_num_type(num_type), inferred_type)

    # Convert input to string and extract numbers
    input_str = str(input_value)
    number_matches = extract_numbers(input_str)

    if not number_matches:
        raise ValueError("No valid numbers found in: {}".format(input_str))

    # Process numbers
    results = []
    target_type = validate_num_type(num_type)

    for type_and_value in number_matches[:num_count]:
        try:
            inferred_type = infer_type(type_and_value)
            value = parse_number(type_and_value)
            value = apply_bounds(value, upper_bound, lower_bound)
            value = apply_precision(value, precision)
            value = convert_type(value, target_type, inferred_type)
            results.append(value)
        except Exception as e:
            raise type(e)(
                "Error processing {}: {}".format(type_and_value[1], str(e))
            )

    return results[0] if num_count == 1 else results


__all__ = ["to_num"]
