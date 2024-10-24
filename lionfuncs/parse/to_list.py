"""List conversion utilities"""

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, TypeVar, overload

from pydantic import BaseModel
from pydantic_core import PydanticUndefinedType

from lionfuncs.ln_undefined import LionUndefinedType

T = TypeVar("T")


@overload
def to_list(
    input_: None | LionUndefinedType | PydanticUndefinedType, /
) -> list: ...


@overload
def to_list(
    input_: str | bytes | bytearray, /, *, use_values: bool = False
) -> list[str | int]: ...


@overload
def to_list(input_: Mapping, /, *, use_values: bool = False) -> list[Any]: ...


@overload
def to_list(
    input_: Sequence[T],
    /,
    *,
    flatten: bool = False,
    dropna: bool = False,
    unique: bool = False,
) -> list[T]: ...


@overload
def to_list(
    input_: Any,
    /,
    *,
    flatten: bool = False,
    dropna: bool = False,
    unique: bool = False,
    use_values: bool = False,
) -> list[Any]: ...


def to_list(
    input_: Any,
    /,
    *,
    flatten: bool = False,
    dropna: bool = False,
    unique: bool = False,
    use_values: bool = False,
) -> list[Any]:
    """Convert various Python objects to a list format.

    This function handles conversion of different Python objects into lists,
    with support for flattening nested structures, removing None values,
    and ensuring unique elements.

    Args:
        input_: Object to convert to list
        flatten: Whether to flatten nested structures
        dropna: Whether to remove None values
        unique: Whether to ensure unique elements (requires flatten=True)
        use_values: Whether to use .values() for dict-like objects

    Returns:
        A list representation of the input

    Raises:
        ValueError: If unique=True and flatten=False
        TypeError: If input type cannot be converted

    Examples:
        >>> to_list([1, [2, 3]], flatten=True)
        [1, 2, 3]

        >>> to_list([1, None, 2], dropna=True)
        [1, 2]

        >>> to_list({'a': 1, 'b': 2}, use_values=True)
        [1, 2]
    """
    # Validate parameters
    if unique and not flatten:
        raise ValueError(
            "unique=True requires flatten=True to ensure proper uniqueness"
        )

    # Convert input to initial list format
    result = _convert_to_list(input_, use_values=use_values)

    # Apply processing if needed
    if flatten or dropna:
        result = _process_list(lst=result, flatten=flatten, dropna=dropna)

    # Apply uniqueness if requested
    return list(dict.fromkeys(result)) if unique else result


def _convert_to_list(input_: Any, /, *, use_values: bool = False) -> list[Any]:
    """Convert input to initial list format."""
    # Handle None and undefined
    if isinstance(
        input_, (type(None), LionUndefinedType, PydanticUndefinedType)
    ):
        return []

    # Handle Pydantic models
    if isinstance(input_, BaseModel):
        return [input_]

    # Handle strings and bytes
    if isinstance(input_, (str, bytes, bytearray)):
        return list(input_) if use_values else [input_]

    # Handle mappings
    if isinstance(input_, Mapping):
        return list(input_.values()) if use_values else [input_]

    # Handle iterables
    if isinstance(input_, Iterable):
        return list(input_)

    # Handle all other types
    return [input_]


def _process_list(
    lst: list[Any],
    *,
    flatten: bool,
    dropna: bool,
) -> list[Any]:
    """Process a list with flattening and None removal.

    Args:
        lst: List to process
        flatten: Whether to flatten nested structures
        dropna: Whether to remove None values

    Returns:
        Processed list
    """
    result = []

    for item in lst:
        # Handle nested iterables
        if isinstance(item, Iterable) and not isinstance(
            item, (str, bytes, bytearray, Mapping)
        ):
            processed = _process_list(
                lst=list(item), flatten=flatten, dropna=dropna
            )
            if flatten:
                result.extend(processed)
            else:
                result.append(processed)

        # Handle non-iterable items
        elif not dropna or item is not None:
            result.append(item)

    return result


__all__ = ["to_list"]
