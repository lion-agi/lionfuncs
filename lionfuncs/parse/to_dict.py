"""
Type-safe dictionary conversion utilities.

This module provides comprehensive functionality for converting various Python
objects to dictionaries, with support for recursive conversion, custom parsers,
and multiple input types.

Features:
- Multiple input type support
- Recursive conversion
- Custom parsers
- Type safety
- Error handling
"""

import json
from collections.abc import Callable, Iterable, Mapping
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

from pydantic_core import PydanticUndefinedType

from lionfuncs.ln_undefined import LionUndefinedType

from .fuzzy_parse_json import fuzzy_parse_json

T = TypeVar("T", bound=Union[Dict[str, Any], List[Dict[str, Any]]])

# Constants
MAX_RECURSION_DEPTH = 10
DEFAULT_RECURSION_DEPTH = 5


def to_dict(
    input_: Any,
    /,
    *,
    use_model_dump: bool = True,
    fuzzy_parse: bool = False,
    suppress: bool = False,
    str_type: Optional[str] = "json",
    parser: Optional[Callable] = None,
    recursive: bool = False,
    max_recursive_depth: Optional[int] = None,
    exclude_types: Tuple = (),
    recursive_python_only: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Convert various Python objects to dictionary format.

    Args:
        input_: Object to convert.
        use_model_dump: Use model_dump() for Pydantic models.
        fuzzy_parse: Enable lenient string parsing.
        suppress: Return empty dict on errors instead of raising.
        str_type: Type of string input ("json" or "xml").
        parser: Custom parser function for strings.
        recursive: Enable recursive conversion.
        max_recursive_depth: Maximum recursion depth.
        exclude_types: Types to exclude from conversion.
        recursive_python_only: Only convert Python built-ins recursively.
        **kwargs: Additional parsing arguments.

    Returns:
        Dictionary representation of input.

    Raises:
        ValueError: On conversion failure if suppress=False.
        RecursionError: If max recursion depth exceeded.
        TypeError: If input type cannot be converted.

    Example:
        >>> to_dict({"a": 1, "b": 2})
        {'a': 1, 'b': 2}
        >>> to_dict([1, 2, 3])
        {0: 1, 1: 2, 2: 3}
    """
    try:
        if recursive:
            return _recursive_to_dict(
                input_,
                max_recursive_depth=max_recursive_depth
                or DEFAULT_RECURSION_DEPTH,
                exclude_types=exclude_types,
                recursive_custom_types=not recursive_python_only,
                use_model_dump=use_model_dump,
                fuzzy_parse=fuzzy_parse,
                str_type=str_type,
                parser=parser,
                **kwargs,
            )

        result = _to_dict(
            input_,
            use_model_dump=use_model_dump,
            fuzzy_parse=fuzzy_parse,
            str_type=str_type,
            parser=parser,
            exclude_types=exclude_types,
            **kwargs,
        )

        if not isinstance(result, dict):
            raise TypeError(
                "Conversion produced {}, expected dict".format(type(result))
            )

        return result

    except Exception as e:
        if suppress:
            return {}
        raise ValueError(
            "Dictionary conversion failed: {}".format(str(e))
        ) from e


def _to_dict(
    input_: Any,
    /,
    *,
    use_model_dump: bool = True,
    fuzzy_parse: bool = False,
    str_type: Optional[str] = "json",
    parser: Optional[Callable] = None,
    exclude_types: Tuple = (),
    **kwargs: Any,
) -> Dict[str, Any]:
    """Core dictionary conversion logic."""
    # Handle excluded types
    if exclude_types and isinstance(input_, exclude_types):
        if isinstance(input_, dict):
            return input_
        raise TypeError(
            "Type {} is excluded from conversion".format(type(input_))
        )

    # Direct dictionary return
    if isinstance(input_, dict):
        return input_

    # Handle model_dump() method
    if use_model_dump and hasattr(input_, "model_dump"):
        return input_.model_dump(**kwargs)

    # Handle None and undefined types
    if isinstance(
        input_, (type(None), LionUndefinedType, PydanticUndefinedType)
    ):
        return {}

    # Handle mappings
    if isinstance(input_, Mapping):
        return dict(input_)

    # Handle strings
    if isinstance(input_, str):
        if fuzzy_parse:
            result = fuzzy_parse_json(input_)
            if isinstance(result, dict):
                return result

        result = _str_to_dict(
            input_,
            str_type=str_type,
            parser=parser,
            **kwargs,
        )
        if isinstance(result, dict):
            return result
        raise TypeError(
            "String parsing produced {}, expected dict".format(type(result))
        )

    # Handle sets
    if isinstance(input_, set):
        return {value: value for value in input_}

    # Handle iterables
    if isinstance(input_, Iterable):
        return {idx: value for idx, value in enumerate(input_)}

    # Try conversion methods
    for method in ["to_dict", "dict", "json", "to_json"]:
        if hasattr(input_, method):
            try:
                result = getattr(input_, method)(**kwargs)
                if isinstance(result, str):
                    return json.loads(result)
                if isinstance(result, dict):
                    return result
            except Exception:
                continue

    # Try __dict__
    if hasattr(input_, "__dict__"):
        return input_.__dict__

    # Final dict conversion attempt
    try:
        return dict(input_)
    except Exception as e:
        raise TypeError(
            "Cannot convert {} to dictionary: {}".format(type(input_), str(e))
        )


def _str_to_dict(
    input_: str,
    /,
    *,
    str_type: Optional[str] = "json",
    parser: Optional[Callable] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Convert string to dictionary using specified parser."""
    if not input_:
        return {}

    if str_type == "json":
        try:
            return (
                json.loads(input_, **kwargs)
                if parser is None
                else parser(input_, **kwargs)
            )
        except json.JSONDecodeError as e:
            raise ValueError("JSON parsing failed: {}".format(str(e))) from e

    if str_type == "xml":
        try:
            if parser is None:
                from .xml_parser import xml_to_dict

                return xml_to_dict(input_, **kwargs)
            return parser(input_, **kwargs)
        except Exception as e:
            raise ValueError("XML parsing failed: {}".format(str(e))) from e

    raise ValueError("Unsupported string type: {}".format(str_type))


def _recursive_to_dict(
    input_: Any,
    /,
    *,
    max_recursive_depth: int = DEFAULT_RECURSION_DEPTH,
    current_depth: int = 0,
    recursive_custom_types: bool = False,
    exclude_types: Tuple = (),
    **kwargs: Any,
) -> Any:
    """Recursively convert nested structures to dictionaries."""
    if current_depth >= max_recursive_depth:
        raise RecursionError(
            "Maximum recursion depth ({}) exceeded".format(max_recursive_depth)
        )

    # Handle strings
    if isinstance(input_, str):
        try:
            parsed = _to_dict(input_, **kwargs)
            return _recursive_to_dict(
                parsed,
                max_recursive_depth=max_recursive_depth,
                current_depth=current_depth + 1,
                recursive_custom_types=recursive_custom_types,
                exclude_types=exclude_types,
                **kwargs,
            )
        except Exception:
            return input_

    # Handle dictionaries
    if isinstance(input_, dict):
        return {
            key: _recursive_to_dict(
                value,
                max_recursive_depth=max_recursive_depth,
                current_depth=current_depth + 1,
                recursive_custom_types=recursive_custom_types,
                exclude_types=exclude_types,
                **kwargs,
            )
            for key, value in input_.items()
        }

    # Handle lists and tuples
    if isinstance(input_, (list, tuple)):
        return type(input_)(
            _recursive_to_dict(
                item,
                max_recursive_depth=max_recursive_depth,
                current_depth=current_depth + 1,
                recursive_custom_types=recursive_custom_types,
                exclude_types=exclude_types,
                **kwargs,
            )
            for item in input_
        )

    # Handle custom types
    if recursive_custom_types:
        try:
            converted = to_dict(input_, **kwargs)
            return _recursive_to_dict(
                converted,
                max_recursive_depth=max_recursive_depth,
                current_depth=current_depth + 1,
                recursive_custom_types=recursive_custom_types,
                exclude_types=exclude_types,
                **kwargs,
            )
        except Exception:
            return input_

    return input_


__all__ = ["to_dict"]
