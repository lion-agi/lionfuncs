"""Nested data structure manipulation operations.

This module provides high-level operations for manipulating nested data structures,
building on the core utilities for validation and type checking.
"""

from collections import defaultdict
from collections.abc import Callable, Sequence
from itertools import chain
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

from lionfuncs.data.utils import (
    ensure_container_capacity,
    get_target_container,
    is_homogeneous,
    validate_indices,
    validate_nested_structure,
)
from lionfuncs.ln_undefined import LN_UNDEFINED
from lionfuncs.parse.to_list import to_list

T = TypeVar("T")
NestedStructure = Union[Dict[str, Any], List[Any]]


def nmerge(
    structures: Sequence,
    /,
    *,
    overwrite: bool = False,
    dict_sequence: bool = False,
    sort_list: bool = False,
    custom_sort: Optional[Callable] = None,
) -> NestedStructure:
    """Merge multiple nested structures.

    Args:
        structures: Sequence of structures to merge.
        overwrite: Whether to overwrite existing keys in dictionaries.
        dict_sequence: Generate unique keys for duplicates if not overwriting.
        sort_list: Whether to sort resulting lists.
        custom_sort: Optional custom sorting function.

    Returns:
        Merged structure (dictionary or list).

    Raises:
        TypeError: If structures aren't compatible for merging.
        ValueError: If input sequence is empty.
    """
    # Validate input
    validate_nested_structure(structures, (list,))
    if not structures:
        raise ValueError("No structures to merge")

    # Check structure types
    if is_homogeneous(structures, dict):
        return _merge_dicts(structures, overwrite, dict_sequence)
    elif is_homogeneous(structures, list):
        return _merge_sequences(structures, sort_list, custom_sort)
    else:
        raise TypeError(
            "All structures must be of the same type (dict or list)"
        )


def npop(
    structure: NestedStructure,
    /,
    indices: Union[str, int, Sequence],
    default: Any = LN_UNDEFINED,
) -> Any:
    """Remove and return a value from a nested structure.

    Args:
        structure: Structure to modify.
        indices: Path to target value.
        default: Optional value to return if target not found.

    Returns:
        Removed value or default if provided and target not found.

    Raises:
        ValueError: If indices is empty.
        TypeError: If structure or indices are invalid types.
        KeyError/IndexError: If target not found and no default provided.
    """
    # Validate inputs
    validate_nested_structure(structure)
    _indices = validate_indices(indices)

    try:
        # Navigate to parent container
        parent = get_target_container(
            structure, _indices[:-1], default=LN_UNDEFINED
        )
        if parent is LN_UNDEFINED:
            if default is LN_UNDEFINED:
                raise KeyError("Invalid path to target")
            return default

        # Pop value from parent
        key = _indices[-1]
        try:
            if isinstance(parent, list):
                if not isinstance(key, int):
                    if default is not LN_UNDEFINED:
                        return default
                    raise TypeError("List indices must be integers")
                return parent.pop(key)
            elif isinstance(parent, dict):
                return parent.pop(key)
            else:
                if default is not LN_UNDEFINED:
                    return default
                raise TypeError(f"Cannot pop from {type(parent).__name__}")
        except (KeyError, IndexError, TypeError) as e:
            if default is not LN_UNDEFINED:
                return default
            raise
    except (KeyError, IndexError, TypeError) as e:
        if default is not LN_UNDEFINED:
            return default
        raise


def nset(
    structure: NestedStructure,
    /,
    indices: Union[str, int, Sequence],
    value: Any,
) -> None:
    """Set a value within a nested structure.

    Args:
        structure: Structure to modify.
        indices: Path to target location.
        value: Value to set.

    Raises:
        ValueError: If indices is empty.
        TypeError: If structure or indices are invalid types.
    """
    # Validate inputs
    validate_nested_structure(structure)
    _indices = validate_indices(indices)

    # Navigate to parent container, creating path as needed
    current = structure
    for i, idx in enumerate(_indices[:-1]):
        next_idx = _indices[i + 1]
        next_container = [] if isinstance(next_idx, int) else {}

        if isinstance(current, dict):
            if not isinstance(idx, str):
                raise TypeError("Dictionary keys must be strings")
            if idx not in current or not isinstance(
                current[idx], (dict, list)
            ):
                current[idx] = next_container
            current = current[idx]

        elif isinstance(current, list):
            if not isinstance(idx, int):
                raise TypeError("List indices must be integers")
            ensure_container_capacity(current, idx)
            if current[idx] is None or not isinstance(
                current[idx], (dict, list)
            ):
                current[idx] = next_container
            current = current[idx]
        else:
            raise TypeError(
                f"Invalid container type: {type(current).__name__}"
            )

    # Set value
    last_idx = _indices[-1]
    if isinstance(current, dict):
        if not isinstance(last_idx, str):
            raise TypeError("Dictionary keys must be strings")
        current[last_idx] = value
    elif isinstance(current, list):
        if not isinstance(last_idx, int):
            raise TypeError("List indices must be integers")
        ensure_container_capacity(current, last_idx)
        current[last_idx] = value
    else:
        raise TypeError(f"Cannot set value in {type(current).__name__}")


def unflatten(
    flat_dict: Dict[str, Any], sep: str = "|", inplace: bool = False
) -> NestedStructure:
    """Convert a flat dictionary into a nested structure.

    Args:
        flat_dict: Dictionary with delimited keys.
        sep: Key delimiter.
        inplace: Whether to modify input dictionary.

    Returns:
        Nested structure (dictionary or list).

    Raises:
        TypeError: If input is not a dictionary.
    """
    validate_nested_structure(flat_dict, (dict,))

    def _unflatten(data: Dict[str, Any]) -> NestedStructure:
        result: Dict[str, Any] = {}

        for key, value in data.items():
            parts = key.split(sep)
            current = result

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = (
                _unflatten(value) if isinstance(value, dict) else value
            )

        # Convert to list if appropriate
        if result and is_homogeneous(result.keys(), str):
            if all(k.isdigit() for k in result):
                return [result[str(i)] for i in range(len(result))]
        return result

    if inplace:
        unflattened = _unflatten(flat_dict)
        flat_dict.clear()
        if isinstance(unflattened, list):
            flat_dict.update({str(i): v for i, v in enumerate(unflattened)})
        else:
            flat_dict.update(unflattened)
        return flat_dict

    return _unflatten(flat_dict)


def flatten(
    structure: NestedStructure,
    /,
    *,
    prefix: Union[str, Tuple[Any, ...]] = "",
    sep: str = "|",
    max_depth: Optional[int] = None,
    _parent_key: Tuple = (),
    _current_depth: int = 0,
) -> Dict[str, Any]:
    """Flatten a nested structure into a single-level dictionary.

    Recursively traverses the structure, creating a flat dictionary where keys
    represent the path to each value in the original structure.

    Args:
        structure: The nested structure to flatten.
        prefix: Optional prefix for all generated keys.
        sep: Separator for joining key components.
        max_depth: Maximum depth to flatten. None for unlimited.
        _parent_key: Internal use for key path tracking.
        _current_depth: Internal use for depth tracking.

    Returns:
        A flattened dictionary with path-based keys.

    Raises:
        TypeError: If structure is not a dictionary or list.
        ValueError: If max_depth is negative.

    Examples:
        >>> flatten({'a': {'b': 1, 'c': [2, 3]}})
        {'a|b': 1, 'a|c|0': 2, 'a|c|1': 3}

        >>> flatten([1, {'a': 2}], sep='.')
        {'0': 1, '1.a': 2}

        >>> flatten({'a': {'b': {'c': 1}}}, max_depth=1)
        {'a': {'b': {'c': 1}}}
    """
    # Validate inputs
    validate_nested_structure(structure)
    if max_depth is not None and max_depth < 0:
        raise ValueError("max_depth must be non-negative")

    # Initialize key prefix
    if isinstance(prefix, str):
        _parent_key = (prefix,) if prefix else ()
    else:
        _parent_key = tuple(prefix)

    result = {}

    # Stop at max_depth
    if max_depth is not None and _current_depth >= max_depth:
        key = _format_key(_parent_key, sep)
        result[key] = structure
        return result

    # Process dictionary
    if isinstance(structure, dict):
        for key, value in structure.items():
            new_key = _parent_key + (str(key),)
            if isinstance(value, (dict, list)) and value:
                result.update(
                    flatten(
                        value,
                        sep=sep,
                        max_depth=max_depth,
                        _parent_key=new_key,
                        _current_depth=_current_depth + 1,
                    )
                )
            else:
                result[_format_key(new_key, sep)] = value

    # Process list
    elif isinstance(structure, list):
        for i, value in enumerate(structure):
            new_key = _parent_key + (str(i),)
            if isinstance(value, (dict, list)) and value:
                result.update(
                    flatten(
                        value,
                        sep=sep,
                        max_depth=max_depth,
                        _parent_key=new_key,
                        _current_depth=_current_depth + 1,
                    )
                )
            else:
                result[_format_key(new_key, sep)] = value

    return result


def nget(
    structure: NestedStructure,
    /,
    indices: Union[str, int, Sequence],
    default: Any = LN_UNDEFINED,
) -> Any:
    """Get a value from a nested structure.

    Args:
        structure: Structure to get value from.
        indices: Path to target value.
        default: Optional value to return if target not found.

    Returns:
        Value at target location or default if provided and target not found.

    Raises:
        ValueError: If indices is empty.
        TypeError: If structure or indices are invalid types.
        KeyError/IndexError: If target not found and no default provided.

    Example:
        >>> data = {'a': [{'b': 1}, {'c': 2}]}
        >>> nget(data, ['a', 1, 'c'])
        2
        >>> nget(data, ['a', 2, 'd'], default='not found')
        'not found'
    """
    # Validate inputs
    validate_nested_structure(structure)
    _indices = validate_indices(indices)

    try:
        # Get target container
        target = get_target_container(
            structure, _indices[:-1], default=LN_UNDEFINED
        )
        if target is LN_UNDEFINED:
            if default is LN_UNDEFINED:
                raise KeyError("Path not found")
            return default

        # Get final value
        last_idx = _indices[-1]
        if isinstance(target, list):
            if not isinstance(last_idx, int):
                if default is not LN_UNDEFINED:
                    return default
                raise TypeError("List indices must be integers")

            if not 0 <= last_idx < len(target):
                if default is not LN_UNDEFINED:
                    return default
                raise IndexError("List index out of range")

            return target[last_idx]

        elif isinstance(target, dict):
            if last_idx not in target:
                if default is not LN_UNDEFINED:
                    return default
                raise KeyError(f"Key not found: {last_idx}")
            return target[last_idx]

        else:
            if default is not LN_UNDEFINED:
                return default
            raise TypeError(f"Cannot get from {type(target).__name__}")

    except (KeyError, IndexError, TypeError) as e:
        if default is not LN_UNDEFINED:
            return default
        raise


def ndelete(
    structure: NestedStructure,
    /,
    indices: Union[str, int, Sequence],
    missing_ok: bool = False,
) -> None:
    """Delete a value from a nested structure.

    Similar to npop but doesn't return the value and has missing_ok option.

    Args:
        structure: Structure to modify.
        indices: Path to target value.
        missing_ok: Whether to ignore if target doesn't exist.

    Raises:
        ValueError: If indices is empty.
        TypeError: If structure or indices are invalid types.
        KeyError/IndexError: If target not found and missing_ok is False.

    Example:
        >>> data = {'a': {'b': [1, 2, 3]}}
        >>> ndelete(data, ['a', 'b', 1])
        >>> data
        {'a': {'b': [1, 3]}}
    """
    try:
        npop(structure, indices)
    except (KeyError, IndexError) as e:
        if not missing_ok:
            raise


def ncopy(
    source: NestedStructure,
    target: NestedStructure,
    /,
    source_indices: Union[str, int, Sequence],
    target_indices: Union[str, int, Sequence],
    *,
    missing_ok: bool = False,
) -> None:
    """Copy a value from one nested structure to another.

    Args:
        source: Structure to copy from.
        target: Structure to copy to.
        source_indices: Path to source value.
        target_indices: Path to target location.
        missing_ok: Whether to ignore if source doesn't exist.

    Raises:
        ValueError: If indices are empty.
        TypeError: If structures or indices are invalid types.
        KeyError/IndexError: If source not found and missing_ok is False.

    Example:
        >>> source = {'a': {'b': 1}}
        >>> target = {'x': {}}
        >>> ncopy(source, target, ['a', 'b'], ['x', 'y'])
        >>> target
        {'x': {'y': 1}}
    """
    # Get value from source
    try:
        value = nget(source, source_indices)
    except (KeyError, IndexError) as e:
        if missing_ok:
            return
        raise

    # Set value in target
    nset(target, target_indices, value)


def nmove(
    source: NestedStructure,
    target: NestedStructure,
    /,
    source_indices: Union[str, int, Sequence],
    target_indices: Union[str, int, Sequence],
    *,
    missing_ok: bool = False,
) -> None:
    """Move a value from one nested structure to another.

    Args:
        source: Structure to move from.
        target: Structure to move to.
        source_indices: Path to source value.
        target_indices: Path to target location.
        missing_ok: Whether to ignore if source doesn't exist.

    Raises:
        ValueError: If indices are empty.
        TypeError: If structures or indices are invalid types.
        KeyError/IndexError: If source not found and missing_ok is False.

    Example:
        >>> source = {'a': {'b': 1}}
        >>> target = {'x': {}}
        >>> nmove(source, target, ['a', 'b'], ['x', 'y'])
        >>> source
        {'a': {}}
        >>> target
        {'x': {'y': 1}}
    """
    # Copy value to target
    ncopy(
        source, target, source_indices, target_indices, missing_ok=missing_ok
    )

    # Delete from source if copy succeeded
    try:
        ndelete(source, source_indices, missing_ok=missing_ok)
    except (KeyError, IndexError):
        # If deletion fails, roll back the copy
        ndelete(target, target_indices, missing_ok=True)
        raise


# ---- Private Helper Functions ----


def _format_key(components: Tuple[Any, ...], sep: str) -> str:
    """Format key components into a string key.

    Args:
        components: Tuple of key components.
        sep: Separator to use between components.

    Returns:
        Formatted key string.
    """
    if not components:
        raise ValueError("Key components cannot be empty")
    return sep.join(str(c) for c in components)


def _merge_dicts(
    dicts: Sequence,
    overwrite: bool,
    use_sequence: bool,
) -> Dict[str, Any]:
    """Merge multiple dictionaries."""
    result = {}
    sequence_counters = defaultdict(int)
    list_values = {}

    for d in dicts:
        for key, value in d.items():
            if key not in result or overwrite:
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = _merge_dicts(
                        [result[key], value], overwrite, use_sequence
                    )
                else:
                    result[key] = value
                    if isinstance(value, list):
                        list_values[key] = True
            elif use_sequence:
                sequence_counters[key] += 1
                new_key = f"{key}{sequence_counters[key]}"
                result[new_key] = value
            else:
                if not isinstance(result[key], list) or list_values.get(
                    key, False
                ):
                    result[key] = [result[key]]
                result[key].append(value)

    return result


def _merge_sequences(
    sequences: Sequence,
    sort_result: bool = False,
    sort_key: Optional[Callable] = None,
) -> List[Any]:
    """Merge multiple sequences."""
    result = list(chain(*sequences))

    if sort_result:
        if sort_key is not None:
            return sorted(result, key=sort_key)
        return sorted(result, key=lambda x: (isinstance(x, str), x))

    return result


def ninsert(
    nested_structure: Union[Dict[Any, Any], List[Any]],
    /,
    indices: List[Union[str, int]],
    value: Any,
    *,
    current_depth: int = 0,
) -> None:
    """
    Inserts a value into a nested structure at a specified path.

    Navigates a nested dictionary or list based on a sequence of indices or
    keys and inserts `value` at the final location. This method can create
    intermediate dictionaries or lists as needed.

    Args:
        nested_structure: The nested structure to modify.
        indices: The sequence of keys or indices defining the insertion path.
        value: The value to insert at the specified location.
        current_depth: Internal use only; tracks the current depth during
            recursive calls.

    Raises:
        ValueError: If the indices list is empty.
        TypeError: If an invalid key or container type is encountered.

    Examples:
        >>> subject_ = {'a': {'b': [1, 2]}}
        >>> ninsert(subject_, ['a', 'b', 2], 3)
        >>> assert subject_ == {'a': {'b': [1, 2, 3]}}

        >>> subject_ = []
        >>> ninsert(subject_, [0, 'a'], 1)
        >>> assert subject_ == [{'a': 1}]
    """
    if not indices:
        raise ValueError("Indices list cannot be empty")

    indices = to_list(indices)
    for i, part in enumerate(indices[:-1]):
        if isinstance(part, int):
            if isinstance(nested_structure, dict):
                raise TypeError(
                    f"Unsupported key type: {type(part).__name__}."
                    "Only string keys are acceptable.",
                )
            while len(nested_structure) <= part:
                nested_structure.append(None)
            if nested_structure[part] is None or not isinstance(
                nested_structure[part], (dict, list)
            ):
                next_part = indices[i + 1]
                nested_structure[part] = (
                    [] if isinstance(next_part, int) else {}
                )
        elif isinstance(nested_structure, dict):
            if part is None:
                raise TypeError("Cannot use NoneType as a key in a dictionary")
            if isinstance(part, (float, complex)):
                raise TypeError(
                    f"Unsupported key type: {type(part).__name__}."
                    "Only string keys are acceptable.",
                )
            if part not in nested_structure:
                next_part = indices[i + 1]
                nested_structure[part] = (
                    [] if isinstance(next_part, int) else {}
                )
        else:
            raise TypeError(
                f"Invalid container type: {type(nested_structure)} "
                "encountered during insertion"
            )

        nested_structure = nested_structure[part]
        current_depth += 1

    last_part = indices[-1]
    if isinstance(last_part, int):
        if isinstance(nested_structure, dict):
            raise TypeError(
                f"Unsupported key type: {type(last_part).__name__}."
                "Only string keys are acceptable.",
            )
        while len(nested_structure) <= last_part:
            nested_structure.append(None)
        nested_structure[last_part] = value
    elif isinstance(nested_structure, list):
        raise TypeError("Cannot use non-integer index on a list")
    else:
        if last_part is None:
            raise TypeError("Cannot use NoneType as a key in a dictionary")
        if isinstance(last_part, (float, complex)):
            raise TypeError(
                f"Unsupported key type: {type(last_part).__name__}."
                "Only string keys are acceptable.",
            )
        nested_structure[last_part] = value


def nfilter(
    nested_structure: Union[Dict, List],
    /,
    condition: Callable,
) -> Union[Dict, List]:
    """Filter elements in a nested structure based on a condition.

    Args:
        nested_structure: The nested structure (dict or list) to filter.
        condition: Function returning True for elements to keep, False to
            discard.

    Returns:
        The filtered nested structure.

    Raises:
        TypeError: If nested_structure is not a dict or list.

    Example:
        >>> data = {"a": 1, "b": {"c": 2, "d": 3}, "e": [4, 5, 6]}
        >>> nfilter(data, lambda x: isinstance(x, int) and x > 2)
        {'b': {'d': 3}, 'e': [4, 5, 6]}
    """
    if isinstance(nested_structure, dict):
        return _filter_dict(nested_structure, condition)
    elif isinstance(nested_structure, list):
        return _filter_list(nested_structure, condition)
    else:
        raise TypeError(
            "The nested_structure must be either a dict or a list."
        )


def _filter_dict(
    dictionary: Dict[Any, Any], condition: Callable
) -> Dict[Any, Any]:
    return {
        k: nfilter(v, condition) if isinstance(v, (dict, list)) else v
        for k, v in dictionary.items()
        if condition(v) or isinstance(v, (dict, list))
    }


def _filter_list(lst: List[Any], condition: Callable) -> List[Any]:
    return [
        nfilter(item, condition) if isinstance(item, (dict, list)) else item
        for item in lst
        if condition(item) or isinstance(item, (dict, list))
    ]


__all__ = [
    "nmerge",
    "npop",
    "nset",
    "unflatten",
    "flatten",
    "nget",
    "ndelete",
    "ncopy",
    "nmove",
    "ninsert",
    "nfilter",
]
