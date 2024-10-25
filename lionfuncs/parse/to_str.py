"""
String conversion utilities with format support.

Features:
- Convert any input to string representation
- Support JSON and XML serialization
- Handle Pydantic models
- Custom formatting options
- Robust error handling
"""

import json
from collections.abc import Callable, Mapping
from typing import Any, Dict, Optional, TypeVar

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
    chars: Optional[str] = None,
    str_type: Optional[str] = None,
    serialize_as: Optional[str] = None,
    use_model_dump: bool = False,
    str_parser: Optional[Callable] = None,
    parser_kwargs: Dict = {},
    **kwargs: Any,
) -> str:
    """
    Convert any input to its string representation.

    Args:
        input_: Input to convert to string.
        strip_lower: If True, strip whitespace and convert to lowercase.
        chars: Specific characters to strip.
        str_type: Type of string input ("json" or "xml").
        serialize_as: Output format ("json" or "xml").
        use_model_dump: Use model_dump for Pydantic models.
        str_parser: Custom string parser function.
        parser_kwargs: Additional parser arguments.
        **kwargs: Additional serialization arguments.

    Returns:
        String representation of input.

    Example:
        >>> to_str(123)
        '123'
        >>> to_str("  HELLO  ", strip_lower=True)
        'hello'
    """
    if serialize_as and serialize_as not in ("json", "xml"):
        raise ValueError(
            "Invalid serialization format: {}".format(serialize_as)
        )

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
            "Failed to convert input of type {} to string".format(
                type(input_).__name__
            )
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
            "Could not convert input of type {} to string".format(
                type(input_).__name__
            )
        ) from e


def _serialize_as(
    input_: Any,
    /,
    *,
    serialize_as: str,
    strip_lower: bool = False,
    chars: Optional[str] = None,
    str_type: Optional[str] = None,
    use_model_dump: bool = False,
    str_parser: Optional[Callable] = None,
    parser_kwargs: Dict = {},
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
            "Failed to serialize input of type {} as {}".format(
                type(input_).__name__, serialize_as
            )
        ) from e


def strip_lower(
    input_: Any,
    /,
    *,
    chars: Optional[str] = None,
    str_type: Optional[str] = None,
    serialize_as: Optional[str] = None,
    use_model_dump: bool = False,
    str_parser: Optional[Callable] = None,
    parser_kwargs: Dict = {},
    **kwargs: Any,
) -> str:
    """
    Convenience function for stripped and lowercased string conversion.

    Args:
        input_: Input to convert.
        chars: Specific characters to strip.
        [Other args same as to_str]

    Returns:
        Stripped and lowercased string.

    Example:
        >>> strip_lower("  HELLO  ")
        'hello'
        >>> strip_lower("...WORLD...", chars=".")
        'world'
    """
    return to_str(
        input_,
        strip_lower=True,
        chars=chars,
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
    chars: Optional[str] = None,
) -> str:
    """Process string with optional stripping and lowercasing."""
    if not s:
        return ""

    if strip_lower:
        s = s.lower()
        if chars is not None:
            s = s.strip(chars)
        else:
            s = s.strip()

    return s


__all__ = ["to_str", "strip_lower"]
