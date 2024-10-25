"""Tests for JSON extraction functionality."""

import pytest

from lionfuncs.parse.to_json import to_json


def test_direct_json_parsing():
    """Test direct JSON string parsing."""
    # Simple JSON
    assert to_json('{"key": "value"}') == {"key": "value"}

    # Complex JSON
    complex_json = """{
        "string": "value",
        "number": 42,
        "array": [1, 2, 3],
        "nested": {"key": "value"}
    }"""
    expected = {
        "string": "value",
        "number": 42,
        "array": [1, 2, 3],
        "nested": {"key": "value"},
    }
    assert to_json(complex_json) == expected

    # Invalid JSON returns empty list
    assert to_json("{invalid}") == []


def test_single_markdown_block():
    """Test parsing from single markdown code block."""
    markdown = """
    Some text before
    ```json
    {"key": "value"}
    ```
    Some text after
    """
    assert to_json(markdown) == {"key": "value"}

    # With whitespace variations
    markdown_spaces = """
    ```json
        {
            "key": "value"
        }
    ```
    """
    assert to_json(markdown_spaces) == {"key": "value"}


def test_multiple_markdown_blocks():
    """Test parsing from multiple markdown code blocks."""
    markdown = """
    First block:
    ```json
    {"key1": "value1"}
    ```
    Second block:
    ```json
    {"key2": "value2"}
    ```
    """
    expected = [{"key1": "value1"}, {"key2": "value2"}]
    assert to_json(markdown) == expected


def test_list_input():
    """Test handling of list input."""
    lines = ["```json", '{"key": "value"}', "```"]
    assert to_json(lines) == {"key": "value"}

    # Multiple blocks in list
    lines = [
        "```json",
        '{"key1": "value1"}',
        "```",
        "```json",
        '{"key2": "value2"}',
        "```",
    ]
    expected = [{"key1": "value1"}, {"key2": "value2"}]
    assert to_json(lines) == expected


def test_no_json_content():
    """Test handling of input without JSON content."""
    # Plain text
    assert to_json("plain text") == []

    # Empty string
    assert to_json("") == []

    # Non-json markdown block
    markdown = """
    ```python
    def function():
        pass
    ```
    """
    assert to_json(markdown) == []
