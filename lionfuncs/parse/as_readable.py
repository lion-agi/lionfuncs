"""
Utilities for converting Python objects to readable JSON strings.

Features:
- Human-readable JSON formatting
- Markdown output support
- Custom serialization options
- Robust error handling
"""

import json
from typing import Any, Dict

from lionfuncs.parse.to_dict import to_dict


def as_readable_json(input_: Any, /, **kwargs: Any) -> str:
    """
    Convert input to a human-readable JSON string.

    Args:
        input_: Object to convert to JSON.
        **kwargs: Additional arguments for json.dumps().
            - ensure_ascii: Force ASCII encoding.
            - indent: Indentation level.
            - separators: Custom separators.
            - cls: Custom JSON encoder class.

    Returns:
        Formatted JSON string.

    Raises:
        ValueError: If JSON conversion fails.

    Example:
        >>> data = {"name": "test", "value": 123}
        >>> print(as_readable_json(data))
        {
            "name": "test",
            "value": 123
        }
    """
    to_dict_config: Dict[str, Any] = {
        "use_model_dump": True,
        "fuzzy_parse": True,
        "recursive": True,
        "recursive_python_only": True,
        "max_recursive_depth": 5,
    }
    to_dict_config.update(kwargs)

    if not input_:
        if isinstance(input_, list):
            return ""
        return "{}"

    try:
        if isinstance(input_, list):
            items = []
            for item in input_:
                dict_ = to_dict(item, **to_dict_config)
                items.append(
                    json.dumps(
                        dict_,
                        indent=4,
                        ensure_ascii=False,
                        default=lambda o: to_dict(o),
                    )
                )
            return "\n\n".join(items)

        dict_ = to_dict(input_, **to_dict_config)

        json_config: Dict[str, Any] = {
            "indent": 4,
            "ensure_ascii": kwargs.get("ensure_ascii", False),
            "default": lambda o: to_dict(o),
        }

        for key in ["indent", "separators", "cls"]:
            if key in kwargs:
                json_config[key] = kwargs[key]

        if kwargs.get("ensure_ascii", False):
            return json.dumps(
                dict_,
                ensure_ascii=True,
                **{
                    k: v for k, v in json_config.items() if k != "ensure_ascii"
                },
            )

        return json.dumps(dict_, **json_config)

    except Exception as e:
        raise ValueError(
            f"Failed to convert input to readable JSON: {e}"
        ) from e


def as_readable(input_: Any, /, *, md: bool = False, **kwargs: Any) -> str:
    """
    Convert input to readable string with optional markdown.

    Args:
        input_: Object to convert.
        md: Whether to wrap in markdown code block.
        **kwargs: Additional arguments for as_readable_json().

    Returns:
        Formatted string representation.

    Example:
        >>> data = {"test": 123}
        >>> print(as_readable(data, md=True))
        ```json
        {
            "test": 123
        }
        ```
    """
    try:
        result = as_readable_json(input_, **kwargs)
        if md:
            return f"```json\n{result}\n```"
        return result
    except Exception:
        return str(input_)


__all__ = ["as_readable_json", "as_readable"]
