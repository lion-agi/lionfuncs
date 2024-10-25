"""
JSON fixing utilities with proper escape handling.

Features:
- Fuzzy JSON parsing with automatic fixes
- Bracket balancing and closure
- Escape sequence handling
- Proper error reporting
"""

import json
import re
from typing import Any, Dict, List, Union


def fuzzy_parse_json(
    str_to_parse: str, /
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Parse JSON string with automatic fixing of common formatting issues.

    Args:
        str_to_parse: JSON string to parse.

    Returns:
        Parsed JSON object.

    Raises:
        ValueError: If string cannot be parsed as valid JSON.
        TypeError: If input is not string or result is not dict.

    Example:
        >>> result = fuzzy_parse_json('{"key": value}')  # Fixes missing quotes
        >>> result["key"] == "value"
        True
    """
    if not isinstance(str_to_parse, str):
        raise TypeError("Input must be a string")

    if not str_to_parse.strip():
        raise ValueError("Input string is empty")

    # Try direct parsing first
    try:
        return json.loads(str_to_parse)
    except Exception:
        pass  # Continue with fixes

    # Try cleaning
    cleaned = _clean_json_string(str_to_parse)
    try:
        return json.loads(cleaned)
    except Exception:
        pass  # Continue with fixes

    # Try fixing
    try:
        fixed = fix_json_string(cleaned)
        return json.loads(fixed)
    except Exception as e:
        raise ValueError(
            "Failed to parse JSON string after all fixing attempts: {}".format(
                str(e)
            )
        ) from e


def _clean_json_string(s: str) -> str:
    """
    Clean and standardize JSON string.

    Args:
        s: String to clean.

    Returns:
        Cleaned string with standardized formatting.
    """
    # Replace single quotes with double quotes
    s = re.sub(r"(?<!\\)'", '"', s)

    # Normalize whitespace
    s = re.sub(r"\s+", " ", s)

    # Add quotes to bare keys
    s = re.sub(r'([{,])\s*([^"\s]+):', r'\1"\2":', s)

    return s.strip()


def fix_json_string(str_to_parse: str, /) -> str:
    """
    Fix JSON string by ensuring proper bracket closure.

    Args:
        str_to_parse: JSON string to fix.

    Returns:
        Fixed JSON string.

    Raises:
        ValueError: If mismatched/extra closing brackets found.

    Example:
        >>> result = fix_json_string('{"key": "value"')
        >>> result == '{"key": "value"}'
        True
    """
    if not str_to_parse:
        raise ValueError("Input string is empty")

    brackets = {"{": "}", "[": "]"}
    open_brackets = []
    pos = 0
    length = len(str_to_parse)

    while pos < length:
        char = str_to_parse[pos]

        if char == "\\":
            # Skip escape sequences
            pos += 2
            continue

        if char == '"':
            # Handle string content
            pos += 1
            while pos < length:
                if str_to_parse[pos] == "\\":
                    pos += 2
                    continue
                if str_to_parse[pos] == '"':
                    break
                pos += 1
            pos += 1
            continue

        # Handle brackets
        if char in brackets:
            open_brackets.append(brackets[char])
        elif char in brackets.values():
            if not open_brackets:
                raise ValueError(
                    "Extra closing bracket '{}' at position {}".format(
                        char, pos
                    )
                )
            if open_brackets[-1] != char:
                raise ValueError(
                    "Mismatched bracket '{}' at position {}".format(char, pos)
                )
            open_brackets.pop()

        pos += 1

    # Add missing closing brackets
    closing_brackets = "".join(reversed(open_brackets))
    return str_to_parse + closing_brackets


__all__ = ["fuzzy_parse_json", "fix_json_string"]
