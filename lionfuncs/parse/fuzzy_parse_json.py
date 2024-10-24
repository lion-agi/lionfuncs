"""JSON fixing utilities with proper escape handling."""

import json
import re
from typing import Any


def fuzzy_parse_json(
    str_to_parse: str, /
) -> dict[str, Any] | list[dict[str, Any]]:
    """Parse a JSON string with automatic fixing of common formatting issues.

    Args:
        str_to_parse: The JSON string to parse

    Returns:
        The parsed JSON object as a dictionary

    Raises:
        ValueError: If the string cannot be parsed as valid JSON
        TypeError: If the input is not a string or the result is not a dict
    """
    if not isinstance(str_to_parse, str):
        raise TypeError("Input must be a string")

    if not str_to_parse.strip():
        raise ValueError("Input string is empty")

    try:
        return json.loads(str_to_parse)
    except Exception:
        pass

    cleaned = _clean_json_string(str_to_parse)
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    try:
        fixed = fix_json_string(cleaned)
        return json.loads(fixed)
    except Exception as e:
        raise ValueError(
            f"Failed to parse JSON string after all fixing attempts: {e}"
        ) from e


def _clean_json_string(s: str) -> str:
    """Clean and standardize a JSON string."""
    s = re.sub(r"(?<!\\)'", '"', s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r'([{,])\s*([^"\s]+):', r'\1"\2":', s)
    return s.strip()


def fix_json_string(str_to_parse: str, /) -> str:
    """Fix a JSON string by ensuring all brackets are properly closed.

    Args:
        str_to_parse: JSON string to fix

    Returns:
        Fixed JSON string with proper bracket closure

    Raises:
        ValueError: If mismatched or extra closing brackets are found
    """
    if not str_to_parse:
        raise ValueError("Input string is empty")

    brackets = {"{": "}", "[": "]"}
    open_brackets = []
    pos = 0
    length = len(str_to_parse)

    while pos < length:
        char = str_to_parse[pos]

        # Handle escape sequences
        if char == "\\":
            pos += 2  # Skip escape sequence
            continue

        # Handle string content
        if char == '"':
            pos += 1
            # Skip until closing quote, accounting for escapes
            while pos < length:
                if str_to_parse[pos] == "\\":
                    pos += 2  # Skip escape sequence
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
                    f"Extra closing bracket '{char}' at position {pos}"
                )
            if open_brackets[-1] != char:
                raise ValueError(
                    f"Mismatched bracket '{char}' at position {pos}"
                )
            open_brackets.pop()

        pos += 1

    # Add missing closing brackets
    closing_brackets = "".join(reversed(open_brackets))
    return str_to_parse + closing_brackets


__all__ = ["fuzzy_parse_json", "fix_json_string"]
