"""String conversion utilities."""

import json
from collections.abc import Callable, Mapping
from typing import Any, Literal, TypeVar

from pydantic_core import PydanticUndefinedType

from lionfuncs.ln_undefined import LionUndefinedType
from lionfuncs.parse.to_dict import to_dict
from lionfuncs.parse.xml_parser import dict_to_xml

T = TypeVar("T")


def to_str(
    input_: Any,
    /,
    *,
    strip_lower: bool = False,
    chars: str | None = None,
    str_type: Literal["json", "xml"] | None = None,
    serialize_as: Literal["json", "xml"] | None = None,
    use_model_dump: bool = False,
    str_parser: Callable[[str], dict[str, Any]] | None = None,
    parser_kwargs: dict = {},
    **kwargs: Any,
) -> str:
    """Convert any input to its string representation.

    Handles various input types, with options for serialization and formatting.

    Args:
        input_: The input to convert to a string.
        strip_lower: If True, strip whitespace and convert to lowercase.
        chars: Specific characters to strip from the result.
        str_type: Type of string input ("json" or "xml") if applicable.
        serialize_as: Output serialization format ("json" or "xml").
        use_model_dump: Use model_dump for Pydantic models if available.
        str_parser: Custom parser function for string inputs.
        parser_kwargs: Additional keyword arguments for the parser.
        **kwargs: Additional arguments passed to json.dumps or serialization.

    Returns:
        str: The string representation of the input.

    Raises:
        ValueError: If serialization or conversion fails.

    Examples:
        >>> to_str(123)
        '123'
        >>> to_str("  HELLO  ", strip_lower=True)
        'hello'
        >>> to_str({"a": 1}, serialize_as="json")
        '{"a": 1}'
        >>> to_str({"a": 1}, serialize_as="xml")
        '<root><a>1</a></root>'
    """
    if serialize_as and serialize_as not in ("json", "xml"):
        raise ValueError(f"Invalid serialization format: {serialize_as}")

    try:
        if serialize_as:
            return _serialize_as(
                input_,
                serialize_as=serialize_as,
                strip_lower=strip_lower,
                chars=chars,
                str_type=str_type,
                use_model_dump=use_model_dump,
                str_parser=str_parser,
                parser_kwargs=parser_kwargs,
                **kwargs,
            )

        return _process_string(
            _to_str_type(input_),
            strip_lower=strip_lower,
            chars=chars,
        )
    except Exception as e:
        raise ValueError(
            f"Failed to convert input of type {type(input_).__name__} to string"
        ) from e


def _to_str_type(input_: Any, /) -> str:
    """Convert input to basic string representation."""
    if input_ in ([], {}, set()):
        return ""

    if isinstance(
        input_, (type(None), LionUndefinedType, PydanticUndefinedType)
    ):
        return ""

    if isinstance(input_, (bytes, bytearray)):
        return input_.decode("utf-8", errors="replace")

    if isinstance(input_, str):
        return input_

    if isinstance(input_, Mapping):
        return json.dumps(dict(input_))

    try:
        return str(input_)
    except Exception as e:
        raise ValueError(
            f"Could not convert input of type {type(input_).__name__} to string"
        ) from e


def _serialize_as(
    input_: Any,
    /,
    *,
    serialize_as: Literal["json", "xml"],
    strip_lower: bool = False,
    chars: str | None = None,
    str_type: Literal["json", "xml"] | None = None,
    use_model_dump: bool = False,
    str_parser: Callable[[str], dict[str, Any]] | None = None,
    parser_kwargs: dict = {},
    **kwargs: Any,
) -> str:
    """Serialize input as JSON or XML."""
    try:
        dict_input = to_dict(
            input_,
            use_model_dump=use_model_dump,
            str_type=str_type,
            suppress=True,
            parser=str_parser,
            **parser_kwargs,
        )

        if any((str_type, chars)):
            str_version = json.dumps(dict_input)
            str_version = _process_string(
                str_version,
                strip_lower=strip_lower,
                chars=chars,
            )
            dict_input = json.loads(str_version)

        if serialize_as == "json":
            return json.dumps(dict_input, **kwargs)

        return dict_to_xml(dict_input, **kwargs)

    except Exception as e:
        raise ValueError(
            f"Failed to serialize input of type {type(input_).__name__} "
            f"as {serialize_as}"
        ) from e


def strip_lower(
    input_: Any,
    /,
    *,
    chars: str | None = None,  # No default, use None
    str_type: Literal["json", "xml"] | None = None,
    serialize_as: Literal["json", "xml"] | None = None,
    use_model_dump: bool = False,
    str_parser: Callable[[str], dict[str, Any]] | None = None,
    parser_kwargs: dict = {},
    **kwargs: Any,
) -> str:
    """
    Convenience function for stripped and lowercased string conversion.

    Args:
        input_: The input to convert to a string
        chars: Optional specific characters to strip
        [other args same as to_str]

    Returns:
        Stripped and lowercased string. If chars is provided, strips those specific
        characters, otherwise uses standard string strip().

    Example:
        >>> strip_lower("  HELLO  ")
        'hello'
        >>> strip_lower("...WORLD...", chars=".")
        'world'
    """
    return to_str(
        input_,
        strip_lower=True,
        chars=chars,  # Pass through as-is
        str_type=str_type,
        serialize_as=serialize_as,
        use_model_dump=use_model_dump,
        str_parser=str_parser,
        parser_kwargs=parser_kwargs,
        **kwargs,
    )


def _process_string(
    s: str,
    strip_lower: bool = False,
    chars: str | None = None,
) -> str:
    """Process string with optional stripping and lowercasing."""
    if not s:
        return ""

    if strip_lower:
        s = s.lower()
        if chars is not None:
            s = s.strip(chars)
        else:
            s = s.strip()  # Regular strip for whitespace only

    return s
