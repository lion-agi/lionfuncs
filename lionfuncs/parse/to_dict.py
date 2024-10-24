"""Type-safe dictionary conversion utilities."""

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, Literal, TypeVar, overload

from pydantic_core import PydanticUndefinedType

from lionfuncs.ln_undefined import LionUndefinedType

from .fuzzy_parse_json import fuzzy_parse_json

T = TypeVar("T", bound=dict[str, Any] | list[dict[str, Any]])

# Maximum allowed recursion depth
MAX_RECURSION_DEPTH = 10
DEFAULT_RECURSION_DEPTH = 5


@overload
def to_dict(
    input_: type[None] | LionUndefinedType | PydanticUndefinedType, /
) -> dict[str, Any]: ...


@overload
def to_dict(input_: Mapping, /) -> dict[str, Any]: ...


@overload
def to_dict(input_: set, /) -> dict[str, Any]: ...


@overload
def to_dict(input_: Sequence, /) -> dict[str, Any]: ...


@overload
def to_dict(
    input_: Any,
    /,
    *,
    use_model_dump: bool = True,
    fuzzy_parse: bool = False,
    suppress: bool = False,
    str_type: Literal["json", "xml"] | None = "json",
    parser: Callable[[str], dict[str, Any]] | None = None,
    recursive: bool = False,
    max_recursive_depth: int | None = None,
    exclude_types: tuple = (),
    recursive_python_only: bool = True,
    **kwargs: Any,
) -> dict[str, Any]: ...


def to_dict(
    input_: Any,
    /,
    *,
    use_model_dump: bool = True,
    fuzzy_parse: bool = False,
    suppress: bool = False,
    str_type: Literal["json", "xml"] | None = "json",
    parser: Callable[[str], dict[str, Any]] | None = None,
    recursive: bool = False,
    max_recursive_depth: int | None = None,
    exclude_types: tuple = (),
    recursive_python_only: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    """Convert various Python objects to dictionary format.

    This function provides comprehensive conversion of Python objects to
    dictionaries, supporting multiple input types and conversion strategies.
    It can handle recursive structures, custom parsers, and various data formats.

    Args:
        input_: Object to convert to dictionary
        use_model_dump: Use model_dump() for Pydantic models
        fuzzy_parse: Enable lenient parsing for string inputs
        suppress: Return empty dict on errors instead of raising
        str_type: Type of string input ("json" or "xml")
        parser: Custom parser function for string inputs
        recursive: Enable recursive conversion of nested structures
        max_recursive_depth: Maximum recursion depth (default: 5, max: 10)
        exclude_types: Types to exclude from conversion
        recursive_python_only: Only recursively convert Python built-in types
        **kwargs: Additional arguments for parsing functions

    Returns:
        Dictionary representation of the input

    Raises:
        ValueError: On conversion failure if suppress=False
        RecursionError: If max recursion depth is exceeded
        TypeError: If input type cannot be converted

    Examples:
        >>> to_dict({"a": 1, "b": 2})
        {'a': 1, 'b': 2}

        >>> to_dict([1, 2, 3])
        {0: 1, 1: 2, 2: 3}

        >>> to_dict('{"x": 10}', str_type="json")
        {'x': 10}

        >>> class MyModel:
        ...     def model_dump(self):
        ...         return {"field": "value"}
        >>> to_dict(MyModel())
        {'field': 'value'}
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
                f"Conversion produced {type(result)}, expected dict"
            )

        return result

    except Exception as e:
        if suppress:
            return {}
        raise ValueError(f"Dictionary conversion failed: {e}") from e


def _to_dict(
    input_: Any,
    /,
    *,
    use_model_dump: bool = True,
    fuzzy_parse: bool = False,
    str_type: Literal["json", "xml"] | None = "json",
    parser: Callable[[str], dict[str, Any]] | None = None,
    exclude_types: tuple = (),
    **kwargs: Any,
) -> dict[str, Any]:
    """Core dictionary conversion logic."""
    # Handle excluded types
    if exclude_types and isinstance(input_, exclude_types):
        if isinstance(input_, dict):
            return input_
        raise TypeError(f"Type {type(input_)} is excluded from conversion")

    # Direct dictionary return
    if isinstance(input_, dict):
        return input_

    # Handle model_dump() method (e.g., Pydantic models)
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

    # Handle strings with optional fuzzy parsing
    if isinstance(input_, str):
        if fuzzy_parse:
            result = fuzzy_parse_json(input_)
            if isinstance(result, dict):
                return result

        # Use standard parsing
        result = _str_to_dict(
            input_,
            str_type=str_type,
            parser=parser,
            **kwargs,
        )
        if isinstance(result, dict):
            return result
        raise TypeError(
            f"String parsing produced {type(result)}, expected dict"
        )

    # Handle sets
    if isinstance(input_, set):
        return {value: value for value in input_}

    # Handle other iterables
    if isinstance(input_, Iterable):
        return {idx: value for idx, value in enumerate(input_)}

    # Try various conversion methods
    for method in ["to_dict", "dict", "json", "to_json"]:
        if hasattr(input_, method):
            try:
                result = getattr(input_, method)(**kwargs)
                if isinstance(result, str):
                    # Parse JSON string result
                    return json.loads(result)
                if isinstance(result, dict):
                    return result
            except Exception:
                continue

    # Fall back to __dict__
    if hasattr(input_, "__dict__"):
        return input_.__dict__

    # Final attempt to convert to dict
    try:
        return dict(input_)
    except Exception as e:
        raise TypeError(f"Cannot convert {type(input_)} to dictionary: {e}")


def _str_to_dict(
    input_: str,
    /,
    *,
    str_type: Literal["json", "xml"] | None = "json",
    parser: Callable[[str], dict[str, Any]] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
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
            raise ValueError(f"JSON parsing failed: {e}") from e

    if str_type == "xml":
        try:
            if parser is None:
                from .xml_parser import xml_to_dict

                return xml_to_dict(input_, **kwargs)
            return parser(input_, **kwargs)
        except Exception as e:
            raise ValueError(f"XML parsing failed: {e}") from e

    raise ValueError(f"Unsupported string type: {str_type}")


def _recursive_to_dict(
    input_: Any,
    /,
    *,
    max_recursive_depth: int = DEFAULT_RECURSION_DEPTH,
    current_depth: int = 0,
    recursive_custom_types: bool = False,
    exclude_types: tuple = (),
    **kwargs: Any,
) -> Any:
    """Recursively convert nested structures to dictionaries."""
    # Check recursion depth
    if current_depth >= max_recursive_depth:
        raise RecursionError(
            f"Maximum recursion depth ({max_recursive_depth}) exceeded"
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

    # Handle custom types if enabled
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
