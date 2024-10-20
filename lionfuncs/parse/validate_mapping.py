import re
from collections.abc import Callable, Sequence
from typing import Any, Literal, TypedDict, cast

from lionfuncs.parse.fuzzy_parse_json import fuzzy_parse_json
from lionfuncs.parse.md_to_json import md_to_json
from lionfuncs.parse.validate_keys import validate_keys

ScoreFunc = Callable[[str, str], float]
HandleUnmatched = Literal["ignore", "raise", "remove", "fill", "force"]


class KeysDict(TypedDict, total=False):
    """TypedDict for keys dictionary."""

    key: Any  # Represents any key-type pair


def validate_mapping(
    d: dict[str, Any] | str,
    keys: Sequence[str] | KeysDict,
    /,
    *,
    score_func: ScoreFunc | None = None,
    fuzzy_match: bool = True,
    handle_unmatched: HandleUnmatched = "ignore",
    fill_value: Any = None,
    fill_mapping: dict[str, Any] | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    """
    Validate and correct a mapping against a set of expected keys.

    This function attempts to convert the input into a dictionary if it's a string,
    then validates the dictionary against expected keys using the `validate_keys` function.

    Args:
        d: Input to be validated. Can be a dictionary or a string representing a dictionary.
        keys: List of expected keys or dictionary mapping keys to types.
        score_func: Function returning similarity score (0-1) for two strings.
        fuzzy_match: If True, use fuzzy matching for key correction.
        handle_unmatched: Specifies how to handle unmatched keys.
        fill_value: Default value for filling unmatched keys.
        fill_mapping: Dictionary mapping unmatched keys to default values.
        strict: If True, raise ValueError if any expected key is missing.

    Returns:
        The validated and corrected dictionary.

    Raises:
        ValueError: If the input cannot be converted to a valid dictionary or if validation fails.

    Example:
        >>> input_str = "{'name': 'John', 'age': 30}"
        >>> keys = ['name', 'age', 'city']
        >>> validated_dict = validate_mapping(input_str, keys, handle_unmatched="fill")
        >>> validated_dict
        {'name': 'John', 'age': 30, 'city': None}
    """
    if isinstance(d, str):
        d = _parse_string_to_dict(d)

    if not isinstance(d, dict):
        raise ValueError(f"Failed to convert input to dictionary: {d}")

    try:
        return validate_keys(
            d,
            keys,
            score_func=score_func,
            fuzzy_match=fuzzy_match,
            handle_unmatched=handle_unmatched,
            fill_value=fill_value,
            fill_mapping=fill_mapping,
            strict=strict,
        )
    except Exception as e:
        raise ValueError(f"Failed to validate mapping for input: {d}") from e


def _parse_string_to_dict(s: str) -> dict[str, Any]:
    """
    Parse a string into a dictionary using various methods.

    Args:
        s: The string to parse.

    Returns:
        The parsed dictionary.

    Raises:
        ValueError: If the string cannot be parsed into a dictionary.
    """
    parsing_methods = [
        lambda: fuzzy_parse_json(s),
        lambda: md_to_json(s),
        lambda: _extract_json_from_codeblock(s),
        lambda: fuzzy_parse_json(s.replace("'", '"')),
    ]

    for method in parsing_methods:
        try:
            result = method()
            if isinstance(result, dict):
                return result
        except Exception:
            continue

    raise ValueError(f"Failed to parse string to dictionary: {s}")


def _extract_json_from_codeblock(s: str) -> dict[str, Any]:
    """
    Extract and parse JSON from a Markdown code block.

    Args:
        s: The string containing a possible JSON code block.

    Returns:
        The parsed dictionary.

    Raises:
        ValueError: If no valid JSON is found in the code block.
    """
    match = re.search(r"```(?:json)?\s*\n(.*?)\n\s*```", s, re.DOTALL)
    if match:
        json_str = match.group(1)
        result = fuzzy_parse_json(json_str)
        if isinstance(result, dict):
            return result
    raise ValueError("No valid JSON found in code block")
