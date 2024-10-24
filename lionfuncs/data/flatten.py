"""Nested structure flattening utilities.

This module provides functionality to flatten nested data structures like
dictionaries and sequences into a single-level dictionary, preserving the
path to each value through key construction.
"""

from collections import deque
from collections.abc import Mapping, Sequence
from typing import Any, Literal, TypeVar, overload

# Type variable for generic type hints
T = TypeVar("T")

# Type aliases for clarity
KeyType = tuple | str
SequenceType = Literal["dict", "list", None]


@overload
def flatten(
    nested_structure: T,
    /,
    *,
    parent_key: tuple = (),
    sep: str = "|",
    coerce_keys: Literal[True] = True,
    dynamic: bool = True,
    coerce_sequence: Literal["dict", None] = None,
    max_depth: int | None = None,
) -> dict[str, Any] | None:
    """Overload for string key coercion."""
    ...


@overload
def flatten(
    nested_structure: T,
    /,
    *,
    parent_key: tuple = (),
    sep: str = "|",
    coerce_keys: Literal[False],
    dynamic: bool = True,
    coerce_sequence: SequenceType = None,
    max_depth: int | None = None,
) -> dict[tuple, Any] | None:
    """Overload for tuple key preservation."""
    ...


def flatten(
    nested_structure: Any,
    /,
    *,
    parent_key: tuple = (),
    sep: str = "|",
    coerce_keys: bool = True,
    dynamic: bool = True,
    coerce_sequence: SequenceType = None,
    max_depth: int | None = None,
) -> dict[KeyType, Any] | None:
    """Flatten a nested structure into a single-level dictionary.

    This function traverses a nested structure (dictionaries, lists, etc.) and
    creates a flattened dictionary where each key represents the path to a value
    in the original structure.

    Args:
        nested_structure: Structure to flatten (dict, list, etc.)
        parent_key: Current path in the structure traversal
        sep: Separator for string key construction
        coerce_keys: Convert keys to strings if True
        dynamic: Handle all sequences as nestable if True
        coerce_sequence: Force sequence handling mode
        max_depth: Maximum nesting depth to traverse

    Returns:
        Flattened dictionary with path-based keys

    Raises:
        ValueError: If incompatible options are specified

    Example:
        >>> nested = {"a": 1, "b": {"c": 2, "d": [3, 4]}}
        >>> flatten(nested)
        {'a': 1, 'b|c': 2, 'b|d|0': 3, 'b|d|1': 4}
    """
    # Validate sequence handling options
    if coerce_keys and coerce_sequence == "list":
        raise ValueError(
            "Cannot use list-style sequence handling with string keys"
        )

    # Determine sequence handling mode
    sequence_mode = _get_sequence_mode(dynamic, coerce_sequence)

    return _flatten_iterative(
        obj=nested_structure,
        parent_key=parent_key,
        sep=sep,
        coerce_keys=coerce_keys,
        dynamic=dynamic,
        **sequence_mode,
        max_depth=max_depth,
    )


def _get_sequence_mode(dynamic: bool, coerce_sequence: SequenceType) -> dict:
    """Determine sequence handling configuration based on options."""
    if not dynamic or not coerce_sequence:
        return {
            "coerce_sequence_to_list": False,
            "coerce_sequence_to_dict": False,
        }

    return {
        "coerce_sequence_to_list": coerce_sequence == "list",
        "coerce_sequence_to_dict": coerce_sequence == "dict",
    }


def _flatten_iterative(
    obj: Any,
    parent_key: tuple,
    sep: str,
    coerce_keys: bool,
    dynamic: bool,
    coerce_sequence_to_list: bool = False,
    coerce_sequence_to_dict: bool = False,
    max_depth: int | None = None,
) -> dict[KeyType, Any]:
    """Iteratively flatten nested structure using a stack."""
    stack = deque([(obj, parent_key, 0)])
    result = {}

    while stack:
        current_obj, current_key, depth = stack.pop()

        # Handle max depth limit
        if max_depth is not None and depth >= max_depth:
            result[_format_key(current_key, sep, coerce_keys)] = current_obj
            continue

        # Handle mappings (dictionaries)
        if isinstance(current_obj, Mapping):
            _process_mapping(
                current_obj,
                current_key,
                depth,
                stack,
                result,
                sep,
                coerce_keys,
            )

        # Handle sequences (lists, tuples, etc.)
        elif _is_sequence(current_obj, dynamic):
            _process_sequence(
                current_obj,
                current_key,
                depth,
                stack,
                coerce_sequence_to_dict,
                coerce_sequence_to_list,
                sep,
                coerce_keys,
            )

        # Handle leaf values
        else:
            result[_format_key(current_key, sep, coerce_keys)] = current_obj

    return result


def _is_sequence(obj: Any, dynamic: bool) -> bool:
    """Check if object should be treated as a sequence."""
    return (
        dynamic
        and isinstance(obj, Sequence)
        and not isinstance(obj, (str, bytes, bytearray))
    )


def _process_mapping(
    obj: Mapping,
    key: tuple,
    depth: int,
    stack: deque,
    result: dict,
    sep: str,
    coerce_keys: bool,
) -> None:
    """Process a mapping type object during flattening."""
    for k, v in obj.items():
        new_key = key + (k,)
        if _should_recurse(v):
            stack.appendleft((v, new_key, depth + 1))
        else:
            result[_format_key(new_key, sep, coerce_keys)] = v


def _process_sequence(
    obj: Sequence,
    key: tuple,
    depth: int,
    stack: deque,
    to_dict: bool,
    to_list: bool,
    sep: str,
    coerce_keys: bool,
) -> None:
    """Process a sequence type object during flattening."""
    if to_dict:
        for k, v in enumerate(obj):
            new_key = key + (str(k),)
            stack.appendleft((v, new_key, depth + 1))
    elif to_list:
        for i, v in enumerate(obj):
            new_key = key + (i,)
            stack.appendleft((v, new_key, depth + 1))
    else:
        for i, v in enumerate(obj):
            new_key = key + (str(i),)
            stack.appendleft((v, new_key, depth + 1))


def _should_recurse(value: Any) -> bool:
    """Check if a value should be recursed into."""
    return (
        value
        and isinstance(value, (Mapping, Sequence))
        and not isinstance(value, (str, bytes, bytearray))
    )


def _format_key(key: tuple, sep: str, coerce_keys: bool) -> KeyType:
    """Format a key tuple based on coercion settings."""
    if not key:
        return key
    return sep.join(map(str, key)) if coerce_keys else key
