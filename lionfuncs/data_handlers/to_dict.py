import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, Literal, TypeVar, overload

from pydantic_core import PydanticUndefinedType

from ..ln_undefined import LionUndefinedType
from ..parsers.fuzzy_parse_json import fuzzy_parse_json

T = TypeVar("T", bound=dict[str, Any] | list[dict[str, Any]])


@overload
def to_dict(
    input_: type[None] | LionUndefinedType | PydanticUndefinedType, /
) -> dict[str, Any]: ...


@overload
def to_dict(input_: Mapping, /) -> dict[str, Any]: ...


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
    **kwargs: Any,
) -> dict[str, Any]: ...


@overload
def to_dict(input_: set, /) -> dict[Any, Any]: ...


@overload
def to_dict(input_: Sequence, /) -> dict[str, Any]: ...


@overload
def to_dict(
    input_: Any,
    /,
    *,
    use_model_dump: bool = True,
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
    remove_root: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    """Convert various input types to a dictionary.

    Handles multiple input types, including None, Mappings, strings, and more.

    Args:
        input_: The input to convert to a dictionary.
        use_model_dump: Use model_dump() for Pydantic models if available.
        fuzzy_parse: Use fuzzy parsing for string inputs.
        suppress: Return empty dict on parsing errors if True.
        str_type: Input string type, either "json" or "xml".
        parser: Custom parser function for string inputs.
        remove_root: Remove root element from XML parsing result.
        **kwargs: Additional arguments passed to parsing functions.

    Returns:
        A dictionary derived from the input.

    Raises:
        ValueError: If string parsing fails and suppress is False.

    Examples:
        >>> to_dict({"a": 1, "b": 2})
        {'a': 1, 'b': 2}
        >>> to_dict('{"x": 10}', str_type="json")
        {'x': 10}
        >>> to_dict("<root><a>1</a></root>", str_type="xml")
        {'a': '1'}
    """
    if isinstance(input_, dict):
        return input_

    if use_model_dump and hasattr(input_, "model_dump"):
        return input_.model_dump(**kwargs)

    if isinstance(input_, type(None) | LionUndefinedType | PydanticUndefinedType):
        return _undefined_to_dict(input_)
    if isinstance(input_, Mapping):
        return _mapping_to_dict(input_)

    if isinstance(input_, str):
        if fuzzy_parse:
            parser = fuzzy_parse_json
        try:
            a = _str_to_dict(
                input_,
                str_type=str_type,
                parser=parser,
                remove_root=remove_root,
                **kwargs,
            )
            if isinstance(a, dict):
                return a
        except Exception as e:
            if suppress:
                return {}
            raise ValueError("Failed to convert string to dictionary") from e

    if isinstance(input_, set):
        return _set_to_dict(input_)
    if isinstance(input_, Iterable):
        return _iterable_to_dict(input_)

    return _generic_type_to_dict(input_, **kwargs)


def _undefined_to_dict(
    input_: type[None] | LionUndefinedType | PydanticUndefinedType,
    /,
) -> dict:
    return {}


def _mapping_to_dict(input_: Mapping, /) -> dict:
    return dict(input_)


def _str_to_dict(
    input_: str,
    /,
    *,
    str_type: Literal["json", "xml"] | None = "json",
    parser: Callable[[str], dict[str, Any]] | None = None,
    remove_root: bool = True,
    **kwargs: Any,
) -> dict[str, Any] | list[dict[str, Any]]:
    """Handle string inputs."""
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
            raise ValueError("Failed to parse JSON string") from e

    if str_type == "xml":
        try:
            if parser is None:
                from ..parsers.xml_parser import xml_to_dict

                return xml_to_dict(input_, remove_root=remove_root)
            return parser(input_, **kwargs)
        except Exception as e:
            raise ValueError("Failed to parse XML string") from e

    raise ValueError(
        f"Unsupported string type for `to_dict`: {str_type}, it should "
        "be 'json' or 'xml'."
    )


def _set_to_dict(input_: set, /) -> dict:
    return {value: value for value in input_}


def _iterable_to_dict(input_: Iterable, /) -> dict:
    return {idx: v for idx, v in enumerate(input_)}


def _generic_type_to_dict(
    input_,
    /,
    **kwargs: Any,
) -> dict[str, Any]:

    for method in ["to_dict", "dict", "json", "to_json"]:
        if hasattr(input_, method):
            result = getattr(input_, method)(**kwargs)
            return json.loads(result) if isinstance(result, str) else result

    if hasattr(input_, "__dict__"):
        return input_.__dict__

    try:
        return dict(input_)
    except Exception as e:
        raise ValueError(f"Unable to convert input to dictionary: {e}")