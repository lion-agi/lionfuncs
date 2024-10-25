"""
Mapping validation with flexible input support.

Features:
- Multiple input formats
- Fuzzy key matching
- Custom similarity algorithms
- Rich validation options
- Comprehensive error handling
"""

from collections.abc import Callable, Sequence
from typing import Any, Dict, Optional, Union

from lionfuncs.algo.string_similarity import SIMILARITY_TYPE
from lionfuncs.parse.to_dict import to_dict
from lionfuncs.parse.to_json import to_json
from lionfuncs.validate.validate_keys import KeysDict, validate_keys

# Type definitions
HandleUnmatchedType = str  # "ignore", "raise", "remove", "fill", "force"


def validate_mapping(
    d: Any,
    keys: Union[Sequence, KeysDict],
    /,
    *,
    similarity_algo: Union[str, Callable] = "jaro_winkler",
    similarity_threshold: float = 0.85,
    fuzzy_match: bool = True,
    handle_unmatched: HandleUnmatchedType = "ignore",
    fill_value: Any = None,
    fill_mapping: Optional[Dict[str, Any]] = None,
    strict: bool = False,
    suppress_conversion_errors: bool = False,
) -> Dict[str, Any]:
    """
    Validate and correct any input into dictionary with expected keys.

    Args:
        d: Input to validate. Supports:
            - Dictionary
            - JSON string/code block
            - XML string
            - Object with to_dict/model_dump
            - Convertible types
        keys: Expected keys or key mapping.
        similarity_algo: Similarity algorithm or function.
        similarity_threshold: Minimum similarity score.
        fuzzy_match: Enable fuzzy matching.
        handle_unmatched: Unmatched key handling:
            - "ignore": Keep unmatched
            - "raise": Raise error
            - "remove": Remove unmatched
            - "fill": Fill with defaults
            - "force": Fill and remove
        fill_value: Default for missing keys.
        fill_mapping: Key to default mapping.
        strict: Raise if expected key missing.
        suppress_conversion_errors: Return empty on errors.

    Returns:
        Validated dictionary.

    Example:
        >>> data = '{"namme": 1, "agge": 2}'
        >>> expected = ["name", "age"]
        >>> validate_mapping(data, expected, fuzzy_match=True)
        {'name': 1, 'age': 2}
    """
    if d is None:
        raise TypeError("Input cannot be None")

    # Convert to dictionary
    try:
        if isinstance(d, str):
            # Try JSON first
            try:
                json_result = to_json(d)
                dict_input = (
                    json_result[0]
                    if isinstance(json_result, list)
                    else json_result
                )
            except Exception:
                # Fall back to general conversion
                dict_input = to_dict(
                    d, str_type="json", fuzzy_parse=True, suppress=True
                )
        else:
            dict_input = to_dict(
                d, use_model_dump=True, fuzzy_parse=True, suppress=True
            )

        if not isinstance(dict_input, dict):
            if suppress_conversion_errors:
                dict_input = {}
            else:
                raise ValueError(
                    "Failed to convert input to dictionary: {}".format(
                        type(dict_input)
                    )
                )

    except Exception as e:
        if suppress_conversion_errors:
            dict_input = {}
        else:
            raise ValueError(
                "Failed to convert input to dictionary: {}".format(str(e))
            )

    # Validate dictionary
    return validate_keys(
        dict_input,
        keys,
        similarity_algo=similarity_algo,
        similarity_threshold=similarity_threshold,
        fuzzy_match=fuzzy_match,
        handle_unmatched=handle_unmatched,
        fill_value=fill_value,
        fill_mapping=fill_mapping,
        strict=strict,
    )


__all__ = ["validate_mapping", "KeysDict"]
