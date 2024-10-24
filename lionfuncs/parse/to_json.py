"""
Module for extracting and parsing JSON from markdown code blocks.

Features:
- Extract JSON from markdown code blocks
- Direct JSON string parsing
- Fuzzy parsing support
- Multiple block handling
- Robust error handling
"""

import json
import re
from typing import Any, Dict, List, Union

from .fuzzy_parse_json import fuzzy_parse_json


def to_json(
    string: Union[str, List[str]], /, fuzzy_parse: bool = False
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extract and parse JSON content from string or markdown code blocks.

    Attempts direct JSON parsing first. If that fails, looks for JSON
    content within markdown code blocks (```json). Supports both single
    and multiple JSON objects.

    Args:
        string: Input string or string list (joined with newlines).
        fuzzy_parse: Enable lenient JSON parsing.

    Returns:
        - Dict for single JSON object
        - List of dicts for multiple objects
        - Empty list if no valid JSON found

    Examples:
        >>> to_json('{"key": "value"}')
        {'key': 'value'}

        >>> to_json('''
        ... ```json
        ... {"key": "value"}
        ... ```
        ... ''')
        {'key': 'value'}

        >>> to_json('''
        ... ```json
        ... {"key1": "value1"}
        ... ```
        ... ```json
        ... {"key2": "value2"}
        ... ```
        ... ''')
        [{'key1': 'value1'}, {'key2': 'value2'}]
    """
    # Handle list input
    if isinstance(string, list):
        string = "\n".join(string)

    # Try direct parsing
    try:
        return fuzzy_parse_json(string) if fuzzy_parse else json.loads(string)
    except Exception:
        pass

    # Extract JSON from markdown blocks
    pattern = r"```json\s*(.*?)\s*```"
    matches = re.findall(pattern, string, re.DOTALL)

    if not matches:
        return []

    # Handle single match
    if len(matches) == 1:
        try:
            return json.loads(matches[0])
        except json.JSONDecodeError as e:
            if not fuzzy_parse:
                raise ValueError(
                    "Failed to parse JSON block: {}".format(str(e))
                ) from e
            return fuzzy_parse_json(matches[0])

    # Handle multiple matches
    result = []
    for match in matches:
        try:
            if fuzzy_parse:
                result.append(fuzzy_parse_json(match))
            else:
                result.append(json.loads(match))
        except json.JSONDecodeError as e:
            raise ValueError(
                "Failed to parse JSON block: {}".format(str(e))
            ) from e

    return result


__all__ = ["to_json"]
