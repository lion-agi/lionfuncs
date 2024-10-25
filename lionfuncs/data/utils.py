"""Core utility functions for data structure operations."""

from collections.abc import Sequence
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from lionfuncs.ln_undefined import LN_UNDEFINED

T = TypeVar("T")
NestedStructure = Union[Dict[Any, Any], List[Any]]


def ensure_container_capacity(
    container: List[Any], index: int, default: Any = None
) -> None:
    """Ensure list has sufficient capacity.

    Args:
        container: List to modify.
        index: Target index.
        default: Default value for new elements.
    """
    if not isinstance(container, list):
        raise TypeError(f"Expected list, got {type(container).__name__}")

    if not isinstance(index, int):
        raise TypeError(f"Expected integer index, got {type(index).__name__}")

    while len(container) <= index:
        container.append(default)


def get_target_container(
    nested: NestedStructure,
    indices: List[Union[int, str]],
    *,
    default: Any = LN_UNDEFINED,
) -> Any:
    """Navigate to a specific container in nested structure.

    Args:
        nested: The nested structure to navigate.
        indices: Path to the target container.
        default: Value to return if target not found. If not provided,
            raises appropriate error.

    Returns:
        The container at the specified path, or default if provided and
        target not found.

    Raises:
        IndexError: For invalid list indices if no default provided.
        KeyError: For missing dictionary keys if no default provided.
        TypeError: For invalid container types.
    """
    current = nested
    for index in indices:
        try:
            if isinstance(current, list):
                if isinstance(index, str) and index.isdigit():
                    index = int(index)

                if not isinstance(index, int):
                    if default is not LN_UNDEFINED:
                        return default
                    raise TypeError("List indices must be integers")

                if not 0 <= index < len(current):
                    if default is not LN_UNDEFINED:
                        return default
                    raise IndexError("List index out of range")

                current = current[index]

            elif isinstance(current, dict):
                if index not in current:
                    if default is not LN_UNDEFINED:
                        return default
                    raise KeyError(f"Key not found: {index}")
                current = current[index]
            else:
                if default is not LN_UNDEFINED:
                    return default
                raise TypeError(
                    f"Invalid container type: {type(current).__name__}"
                )
        except (IndexError, KeyError, TypeError) as e:
            if default is not LN_UNDEFINED:
                return default
            raise

    return current


def is_homogeneous(
    iterables: Union[List[Any], Dict[Any, Any]],
    type_check: Union[Type, Tuple[Type, ...]],
) -> bool:
    """Check if all elements in a list or dict values are of same type."""
    if not iterables:
        return True

    if isinstance(iterables, list):
        return all(isinstance(it, type_check) for it in iterables)
    elif isinstance(iterables, dict):
        return all(isinstance(val, type_check) for val in iterables.values())
    else:
        return isinstance(iterables, type_check)


def is_same_dtype(
    input_: Union[List[Any], Dict[Any, Any]],
    dtype: Optional[Type] = None,
    return_dtype: bool = False,
) -> Union[bool, Tuple[bool, Optional[Type]]]:
    """Check if all elements in input share the same data type."""
    if not input_:
        return (True, None) if return_dtype else True

    iterable = input_.values() if isinstance(input_, dict) else input_
    first_element_type = type(next(iter(iterable)))

    dtype = dtype or first_element_type
    result = all(isinstance(element, dtype) for element in iterable)

    return (result, dtype) if return_dtype else result


def is_structure_homogeneous(
    structure: Any, return_structure_type: bool = False
) -> Union[bool, Tuple[bool, Optional[Type]]]:
    """Check if nested structure consistently uses lists or dicts."""

    def _check_structure(substructure: Any) -> Tuple[bool, Optional[Type]]:
        structure_type = None
        if isinstance(substructure, list):
            structure_type = list
            for item in substructure:
                if isinstance(item, (list, dict)):
                    if not isinstance(item, structure_type):
                        return False, None
                    result, _ = _check_structure(item)
                    if not result:
                        return False, None
        elif isinstance(substructure, dict):
            structure_type = dict
            for item in substructure.values():
                if isinstance(item, (list, dict)):
                    if not isinstance(item, structure_type):
                        return False, None
                    result, _ = _check_structure(item)
                    if not result:
                        return False, None
        return True, structure_type

    is_homogeneous, structure_type = _check_structure(structure)
    return (
        (is_homogeneous, structure_type)
        if return_structure_type
        else is_homogeneous
    )


def deep_update(
    original: Dict[Any, Any], update: Dict[Any, Any]
) -> Dict[Any, Any]:
    """Recursively merge two dictionaries."""
    for key, value in update.items():
        if isinstance(value, dict) and key in original:
            original[key] = deep_update(original.get(key, {}), value)
        else:
            original[key] = value
    return original


def validate_nested_structure(
    structure: Any,
    allowed_types: Optional[Tuple[Type, ...]] = None,
    check_homogeneity: bool = True,
) -> None:
    """Validate a nested data structure."""
    types = allowed_types or (dict, list)

    if not isinstance(structure, types):
        raise TypeError(
            f"Expected {' or '.join(t.__name__ for t in types)}, "
            f"got {type(structure).__name__}"
        )

    if check_homogeneity and not is_structure_homogeneous(structure):
        raise ValueError(
            "Structure must consistently use either lists or dictionaries"
        )


def validate_indices(
    indices: Union[str, int, Sequence],
    allow_empty: bool = False,
) -> List[Union[str, int]]:
    """Validate and normalize structure indices."""
    if not isinstance(indices, (str, int, Sequence)):
        raise TypeError(f"Invalid indices type: {type(indices).__name__}")

    _indices = [indices] if isinstance(indices, (str, int)) else list(indices)

    if not allow_empty and not _indices:
        raise ValueError("Indices cannot be empty")

    if not all(isinstance(idx, (str, int)) for idx in _indices):
        invalid = next(i for i in _indices if not isinstance(i, (str, int)))
        raise TypeError(
            f"Invalid index type: {type(invalid).__name__}. "
            "Must be string or integer."
        )

    return _indices


__all__ = [
    "ensure_container_capacity",
    "get_target_container",
    "is_homogeneous",
    "is_same_dtype",
    "is_structure_homogeneous",
    "deep_update",
    "validate_nested_structure",
    "validate_indices",
]
