"""Provide utility for converting various inputs to readable JSON strings."""

import json
from typing import Any

from lionfuncs.data.to_dict import to_dict


def as_readable_json(input_: Any, /, **kwargs) -> str:
    """
    Convert the input to a readable JSON string.

    This function attempts to convert the input to a dictionary and then
    to a formatted JSON string. If conversion to a dictionary fails, it
    returns the string representation of the input.

    Args:
        input_: The input to be converted to a readable JSON string.
        kwargs for to_dict

    Returns:
        A formatted JSON string if the input can be converted to a
        dictionary, otherwise the string representation of the input.

    Raises:
        ValueError: If the input cannot be converted to a readable dict.
    """
    try:
        dict_ = to_dict(
            input_,
            use_model_dump=True,
            fuzzy_parse=True,
            recursive=True,
            recursive_python_only=False,
            max_recursive_depth=5,
            **kwargs,
        )
        return json.dumps(dict_, indent=4)

    except Exception as e:
        raise ValueError(
            f"Could not convert given input to readable dict: {e}"
        ) from e
