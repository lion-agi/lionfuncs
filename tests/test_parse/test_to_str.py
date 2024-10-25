# File: tests/test_parse/test_to_str.py

import json
from collections import OrderedDict, namedtuple
from datetime import datetime
from decimal import Decimal
from enum import Enum

import pytest
from pydantic import BaseModel

from lionfuncs.ln_undefined import LN_UNDEFINED
from lionfuncs.parse.to_str import strip_lower, to_str


class CustomModel(BaseModel):
    field: str = "value"


class CustomStr:
    def __str__(self):
        return "custom_str"


class CustomRepr:
    def __repr__(self):
        return "custom_repr"


class ErrorObject:
    def __str__(self):
        raise Exception("Str conversion error")


class Color(Enum):
    RED = 1
    GREEN = 2


class TestToStr:
    """Comprehensive test suite for to_str function."""

    def test_none_and_undefined(self):
        """Test None and undefined values."""
        assert to_str(None) == ""
        assert to_str(LN_UNDEFINED) == ""
        assert to_str([]) == ""
        assert to_str({}) == ""
        assert to_str(set()) == ""

    @pytest.mark.parametrize(
        "input_value, expected",
        [
            (123, "123"),
            (3.14, "3.14"),
            (True, "True"),
            (False, "False"),
            (1 + 2j, "(1+2j)"),
            (Decimal("123.45"), "123.45"),
        ],
    )
    def test_primitive_types(self, input_value, expected):
        """Test primitive type conversions."""
        assert to_str(input_value) == expected

    def test_string_processing(self):
        """Test string processing options."""
        # Basic string handling
        assert to_str("Hello") == "Hello"
        assert to_str("  HELLO  ", strip_lower=True) == "hello"
        assert to_str("__TEST__", strip_lower=True, chars="_") == "test"

        # Unicode handling
        assert to_str("こんにちは") == "こんにちは"
        assert to_str("  ЗДРАВСТВУЙ  ", strip_lower=True) == "здравствуй"

        # Escape characters
        text = 'Line 1\nLine 2\t"Quoted"'
        assert to_str(text) == text
        assert (
            to_str({"text": text})
            == '{"text": "Line 1\\nLine 2\\t\\"Quoted\\""}'
        )

    def test_bytes_handling(self):
        """Test bytes and bytearray handling."""
        assert to_str(b"hello") == "hello"
        assert to_str(bytearray(b"world")) == "world"
        assert to_str("こんにちは".encode()) == "こんにちは"
        assert to_str(b"\xff\xfe") == "��"  # Non-UTF8 bytes

        # Memoryview
        mv = memoryview(b"hello")
        assert to_str(mv).startswith("<memory at")

    def test_collections(self):
        """Test collection type conversions."""
        # Lists and tuples
        assert to_str([1, 2, 3]) == "[1, 2, 3]"
        assert to_str((1, 2, 3)) == "(1, 2, 3)"
        assert to_str([1, [2, 3], {"a": 4}]) == "[1, [2, 3], {'a': 4}]"

        # Dictionaries
        assert to_str({"a": 1, "b": 2}) == '{"a": 1, "b": 2}'
        assert to_str(OrderedDict([("a", 1), ("b", 2)])) == '{"a": 1, "b": 2}'

        # Mixed types
        mixed = [1, "two", 3.0, [4, 5], {"six": 6}]
        assert to_str(mixed) == "[1, 'two', 3.0, [4, 5], {'six': 6}]"

        # Named tuple
        Point = namedtuple("Point", ["x", "y"])
        assert to_str(Point(1, 2)) == "Point(x=1, y=2)"

    def test_model_and_custom_objects(self):
        """Test model and custom object conversions."""
        # Pydantic model
        model = CustomModel(field="test")
        assert (
            to_str(model, use_model_dump=True, serialize_as="json")
            == '{"field": "test"}'
        )
        assert "field='test'" in to_str(model, use_model_dump=False)

        # Custom objects
        assert to_str(CustomStr()) == "custom_str"
        assert to_str(CustomRepr()) == "custom_repr"

        # Enum
        assert to_str(Color.RED) == "Color.RED"

    def test_serialization(self):
        """Test JSON and XML serialization."""
        data = {"name": "John", "age": 30}

        # JSON serialization
        json_result = to_str(data, serialize_as="json")
        assert json.loads(json_result) == data

        # XML serialization
        xml_result = to_str(data, serialize_as="xml")
        assert "<name>John</name>" in xml_result
        assert "<age>30</age>" in xml_result

    def test_strip_lower(self):
        """Test strip_lower functionality."""

        @pytest.mark.parametrize(
            "input_,chars,expected",
            [
                ("  HELLO  ", None, "hello"),  # Basic whitespace
                ("...WORLD...", ".", "world"),  # With dots
                (
                    "  ...TEST...  ",
                    None,
                    "...test...",
                ),  # Only whitespace stripped
                ("__TEST__", "_", "test"),  # Custom chars
                ("  #HASH#  ", "#", "  hash  "),  # Only hash stripped
                ("  #HASH#  ", "# ", "hash"),  # Multiple chars stripped
                ("  ЗДРАВСТВУЙ  ", None, "здравствуй"),  # Unicode
                ("", None, ""),  # Empty string
                ("   ", None, ""),  # Only whitespace
                ("\n\t\r", None, ""),  # Special whitespace
            ],
        )
        def test_strip_lower_variations(self, input_, chars, expected):
            result = strip_lower(input_, chars=chars)
            assert result == expected

    def test_special_types(self):
        """Test special type conversions."""
        # Built-in types
        assert to_str(range(5)) == "range(0, 5)"
        assert to_str(slice(1, 5, 2)) == "slice(1, 5, 2)"

        # Function
        def test_func():
            pass

        assert "test_func" in to_str(test_func)

        # Module
        import math

        assert "module 'math'" in to_str(math)

    def test_error_cases(self):
        """Test error handling."""
        # Invalid serialization format
        with pytest.raises(ValueError):
            to_str({}, serialize_as="invalid")

        # Recursive structure
        recursive_dict = {}
        recursive_dict["self"] = recursive_dict
        with pytest.raises(ValueError):
            to_str(recursive_dict, serialize_as="json")

    def test_performance_edge_cases(self):
        """Test performance and edge cases."""
        # Large input handling
        large_list = list(range(1000))
        result = to_str(large_list)
        assert len(result.split(", ")) == 1000

        # Very long string
        long_string = "a" * 10000
        result = to_str(long_string)
        assert len(result) == 10000
