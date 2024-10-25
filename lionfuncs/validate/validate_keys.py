"""
Dictionary key validation with fuzzy matching support.

Features:
- Fuzzy key matching
- Multiple handling strategies
- Custom similarity algorithms
- Flexible key mapping
- Comprehensive validation
"""

from collections.abc import Callable, Sequence
from typing import Any, Dict, Optional, Set, Union

from lionfuncs.algo.string_similarity import (
    SIMILARITY_ALGO_MAP,
    string_similarity,
)

# Type definitions
HandleUnmatchedType = str  # "ignore", "raise", "remove", "fill", "force"


class KeysDict(Dict[str, Any]):
    """Type for keys dictionary with flexible value types."""

    pass


def validate_keys(
    d_: Dict[str, Any],
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
) -> Dict[str, Any]:
    """
    Validate and correct dictionary keys using string similarity.

    Args:
        d_: Dictionary to validate.
        keys: Expected keys or key-type mapping.
        similarity_algo: Similarity algorithm or custom function.
        similarity_threshold: Minimum similarity score.
        fuzzy_match: Enable fuzzy matching.
        handle_unmatched: How to handle unmatched keys:
            - "ignore": Keep unmatched
            - "raise": Raise error
            - "remove": Remove unmatched
            - "fill": Fill with defaults
            - "force": Fill and remove
        fill_value: Default value for missing keys.
        fill_mapping: Custom mapping for missing keys.
        strict: Raise error if any expected key missing.

    Returns:
        Validated dictionary with corrected keys.

    Example:
        >>> data = {"namme": 1, "agge": 2}
        >>> expected = ["name", "age"]
        >>> validate_keys(data, expected, fuzzy_match=True)
        {'name': 1, 'age': 2}
    """
    # Validate inputs
    if not isinstance(d_, dict):
        raise TypeError("First argument must be a dictionary")
    if keys is None:
        raise TypeError("Keys argument cannot be None")
    if not 0.0 <= similarity_threshold <= 1.0:
        raise ValueError("similarity_threshold must be between 0.0 and 1.0")
    if handle_unmatched not in {"ignore", "raise", "remove", "fill", "force"}:
        raise ValueError(
            "handle_unmatched must be one of: ignore, raise, remove, fill, force"
        )

    # Extract expected keys
    fields_set: Set[str] = set(keys if isinstance(keys, list) else keys.keys())
    if not fields_set:
        return d_.copy()

    # Initialize tracking
    corrected_out: Dict[str, Any] = {}
    matched_expected: Set[str] = set()
    matched_input: Set[str] = set()

    # Get similarity function
    if isinstance(similarity_algo, str):
        if similarity_algo not in SIMILARITY_ALGO_MAP:
            raise ValueError(
                "Unknown similarity algorithm: {}".format(similarity_algo)
            )
        similarity_func = SIMILARITY_ALGO_MAP[similarity_algo]
    else:
        similarity_func = similarity_algo

    # Process exact matches
    for key in d_:
        if key in fields_set:
            corrected_out[key] = d_[key]
            matched_expected.add(key)
            matched_input.add(key)

    # Process fuzzy matches
    if fuzzy_match:
        remaining_input = set(d_.keys()) - matched_input
        remaining_expected = fields_set - matched_expected

        for key in remaining_input:
            if not remaining_expected:
                break

            matches = string_similarity(
                key,
                list(remaining_expected),
                algorithm=similarity_func,
                threshold=similarity_threshold,
                return_most_similar=True,
            )

            if matches:
                match = matches
                corrected_out[match] = d_[key]
                matched_expected.add(match)
                matched_input.add(key)
                remaining_expected.remove(match)
            elif handle_unmatched == "ignore":
                corrected_out[key] = d_[key]

    # Handle unmatched keys
    unmatched_input = set(d_.keys()) - matched_input
    unmatched_expected = fields_set - matched_expected

    if handle_unmatched == "raise" and unmatched_input:
        raise ValueError("Unmatched keys found: {}".format(unmatched_input))

    elif handle_unmatched == "ignore":
        for key in unmatched_input:
            corrected_out[key] = d_[key]

    elif handle_unmatched in ("fill", "force"):
        # Fill missing expected keys
        for key in unmatched_expected:
            if fill_mapping and key in fill_mapping:
                corrected_out[key] = fill_mapping[key]
            else:
                corrected_out[key] = fill_value

        # Keep unmatched originals in fill mode
        if handle_unmatched == "fill":
            for key in unmatched_input:
                corrected_out[key] = d_[key]

    # Handle strict mode
    if strict and unmatched_expected:
        raise ValueError(
            "Missing required keys: {}".format(unmatched_expected)
        )

    return corrected_out


__all__ = ["validate_keys", "KeysDict"]
