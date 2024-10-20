from collections.abc import Callable
from typing import Any

from lionfuncs.parse.extract_json_block import (
    extract_block,
    extract_json_blocks,
)
from lionfuncs.parse.fuzzy_parse_json import fuzzy_parse_json
from lionfuncs.parse.utils import md_json_char_map


def md_to_json(
    str_to_parse: str | list[str],
    *,
    expected_keys: list[str] | dict[str, Any] | None = None,
    parser: Callable[[str], Any] | None = None,
    suppress: bool = False,
    as_jsonl: bool = False,
) -> dict[str, Any] | list[dict[str, Any]] | None:
    """
    Parse JSON from Markdown string(s) and validate against expected keys.

    Args:
        str_to_parse: Markdown string(s) to parse.
        expected_keys: Keys expected in the JSON object.
        parser: Custom parser function for JSON strings.
        suppress: If True, return None instead of raising errors.
        as_jsonl: If True, return a list of JSON objects.

    Returns:
        Parsed JSON object(s) or None if suppress is True and parsing fails.

    Raises:
        ValueError: If parsing fails and suppress is False.
    """
    str_to_parse = [
        s.strip()
        for s in (
            str_to_parse if isinstance(str_to_parse, list) else [str_to_parse]
        )
    ]
    str_ = "\n".join(str_to_parse).strip()
    json_blocks = extract_json_blocks(
        str_to_parse=str_,
        suppress=suppress,
        fuzzy_parse=True,
        dropna=True,
    )

    if as_jsonl and json_blocks and len(json_blocks) > 1:
        return [
            obj
            for obj in json_blocks
            if _validate_keys(
                json_obj=obj,
                expected_keys=expected_keys,
                suppress=suppress,
            )
        ] or None
    else:
        return _md_to_single_json(
            str_to_parse=str_,
            expected_keys=expected_keys,
            parser=parser,
            suppress=suppress,
        )


def _md_to_single_json(
    str_to_parse: str,
    *,
    expected_keys: list[str] | dict[str, Any] | None = None,
    parser: Callable[[str], Any] | None = None,
    suppress: bool = False,
) -> dict[str, Any] | None:
    """
    Parse a single JSON block from a Markdown string and validate its keys.

    Args:
        str_to_parse: The Markdown string to parse.
        expected_keys: Keys expected to be present in the JSON object.
        parser: Custom parser function for the JSON string.
        suppress: If True, return None instead of raising errors.

    Returns:
        The parsed JSON object or None if suppress is True and parsing fails.

    Raises:
        ValueError: If parsing fails and suppress is False.
    """
    json_obj = extract_block(
        str_to_parse=str_to_parse,
        parser=parser or fuzzy_parse_json,
        suppress=suppress,
    )

    if not json_obj:
        return (
            None
            if suppress
            else ValueError("No JSON block found in the Markdown content.")
        )

    return (
        json_obj
        if _validate_keys(
            json_obj=json_obj,
            expected_keys=expected_keys,
            suppress=suppress,
        )
        else None
    )


def _validate_keys(
    json_obj: dict[str, Any],
    expected_keys: list[str] | dict[str, Any] | None,
    suppress: bool,
) -> bool:
    """
    Validate the presence of expected keys in a JSON object.

    Args:
        json_obj: The JSON object to validate.
        expected_keys: Keys expected to be present in the JSON object.
        suppress: If True, return False instead of raising an error.

    Returns:
        True if validation passes, False if it fails and suppress is True.

    Raises:
        ValueError: If validation fails and suppress is False.
    """
    if not expected_keys:
        return True

    expected_keys = (
        list(expected_keys.keys())
        if isinstance(expected_keys, dict)
        else expected_keys
    )
    missing_keys = [key for key in expected_keys if key not in json_obj]

    if missing_keys:
        if suppress:
            return False
        raise ValueError(
            "Missing expected keys in JSON "
            f"object: {', '.join(missing_keys)}"
        )
    return True


def escape_chars_in_json(
    value: str, char_map: dict[str, str] | None = None
) -> str:
    """
    Escape characters in a JSON string using a character map.

    Args:
        value: The string to escape.
        char_map: A dictionary mapping characters to their escaped versions.

    Returns:
        The escaped string.
    """
    char_map = char_map or md_json_char_map
    for k, v in char_map.items():
        value = value.replace(k, v)
    return value
