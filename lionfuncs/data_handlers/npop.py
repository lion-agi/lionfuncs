from collections.abc import Sequence
from typing import Any

from lionfuncs.data_handlers.to_list import to_list
from lionfuncs.ln_undefined import LN_UNDEFINED


def npop(
    input_: dict[str, Any] | list[Any],
    /,
    indices: str | int | Sequence[str | int],
    default: Any = LN_UNDEFINED,
) -> Any:
    """
    Perform a nested pop operation on the input structure.

    This function navigates through the nested structure using the provided
    indices and removes and returns the value at the final location.

    Args:
        input_: The input nested structure (dict or list) to pop from.
        indices: A single index or a sequence of indices to navigate the
            nested structure.
        default: The value to return if the key is not found. If not
            provided, a KeyError will be raised.

    Returns:
        The value at the specified nested location.

    Raises:
        ValueError: If the indices list is empty.
        KeyError: If a key is not found in a dictionary.
        IndexError: If an index is out of range for a list.
        TypeError: If an operation is not supported on the current data type.
    """
    if not indices:
        raise ValueError("Indices list cannot be empty")

    indices = to_list(indices)

    current = input_
    for key in indices[:-1]:
        if isinstance(current, dict):
            if current.get(key):
                current = current[key]
            else:
                raise KeyError(f"{key} is not found in {current}")
        elif isinstance(current, list) and isinstance(key, int):
            if key >= len(current):
                raise KeyError(
                    f"{key} exceeds the length of the list {current}"
                )
            elif key < 0:
                raise ValueError("list index cannot be negative")
            current = current[key]

    last_key = indices[-1]
    try:
        return current.pop(
            last_key,
        )
    except Exception as e:
        if default is not LN_UNDEFINED:
            return default
        else:
            raise KeyError(f"Invalid npop. Error: {e}")
