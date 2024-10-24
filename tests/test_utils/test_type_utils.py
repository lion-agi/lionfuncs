"""Tests for type checking and manipulation utilities."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union
import pytest

from lionfuncs.utils.type_utils import TypeUtils, TypeValidator, TypeInfo


# Test classes and types
@dataclass
class TestData:
    """Test data class."""

    value: int
    name: str


class CustomType:
    """Custom test type."""

    def __init__(self, value: str):
        self.value = value


class TestTypeUtils:
    """Test suite for TypeUtils."""

    def test_type_validation_basic(self):
        """Test basic type validation."""
        # Valid cases
        TypeValidator.validate_type(42, int)
        TypeValidator.validate_type("test", str)
        TypeValidator.validate_type(None, int, allow_none=True)

        # Invalid cases
        with pytest.raises(TypeError):
            TypeValidator.validate_type(42, str)

        with pytest.raises(TypeError):
            TypeValidator.validate_type("test", int)

        with pytest.raises(TypeError):
            TypeValidator.validate_type(None, int)

    def test_sequence_validation(self):
        """Test sequence validation."""
        # Valid cases
        TypeValidator.validate_sequence([1, 2, 3], int)
        TypeValidator.validate_sequence(
            ["a", "b"], str, min_length=1, max_length=3
        )

        # Invalid cases
        with pytest.raises(TypeError):
            TypeValidator.validate_sequence([1, "2", 3], int)

        with pytest.raises(ValueError):
            TypeValidator.validate_sequence([1], int, min_length=2)

        with pytest.raises(ValueError):
            TypeValidator.validate_sequence([], int, allow_empty=False)

    def test_mapping_validation(self):
        """Test mapping validation."""
        # Valid cases
        TypeValidator.validate_mapping({"a": 1, "b": 2}, str, int)
        TypeValidator.validate_mapping({"x": 1}, str, int, required_keys={"x"})

        # Invalid cases
        with pytest.raises(TypeError):
            TypeValidator.validate_mapping({1: "a"}, str, str)

        with pytest.raises(ValueError):
            TypeValidator.validate_mapping(
                {"a": 1}, str, int, required_keys={"b"}
            )

        with pytest.raises(ValueError):
            TypeValidator.validate_mapping(
                {"a": 1, "b": 2},
                str,
                int,
                required_keys={"a"},
                allow_extra=False,
            )

    def test_type_coercion(self):
        """Test type coercion."""
        # Basic coercion
        assert TypeUtils.coerce_type("42", int) == 42
        assert TypeUtils.coerce_type(42, str) == "42"

        # Boolean coercion
        assert TypeUtils.coerce_type("true", bool) is True
        assert TypeUtils.coerce_type("false", bool) is False
        assert TypeUtils.coerce_type("yes", bool) is True
        assert TypeUtils.coerce_type("no", bool) is False

        # Custom converters
        converters = {str: lambda s: CustomType(s)}
        custom = TypeUtils.coerce_type(
            "test", CustomType, custom_converters=converters
        )
        assert isinstance(custom, CustomType)
        assert custom.value == "test"

        # Strict mode
        with pytest.raises(TypeError):
            TypeUtils.coerce_type("42.0", int, strict=True)

    def test_type_info(self):
        """Test type information extraction."""
        # Simple types
        int_info = TypeUtils.get_type_info(int)
        assert not int_info.is_optional
        assert not int_info.is_sequence
        assert not int_info.is_mapping
        assert not int_info.is_union

        # Optional types
        opt_info = TypeUtils.get_type_info(Optional[int])
        assert opt_info.is_optional
        assert not opt_info.is_sequence
        assert opt_info.is_union

        # Sequence types
        list_info = TypeUtils.get_type_info(List[str])
        assert list_info.is_sequence
        assert list_info.is_generic
        assert list_info.args == (str,)

        # Mapping types
        dict_info = TypeUtils.get_type_info(Dict[str, int])
        assert dict_info.is_mapping
        assert dict_info.is_generic
        assert dict_info.args == (str, int)

    def test_subtype_checking(self):
        """Test subtype relationship checking."""

        # Basic inheritance
        class SubClass(CustomType):
            pass

        assert TypeUtils.check_subtype(SubClass, CustomType)
        assert not TypeUtils.check_subtype(CustomType, SubClass)

        # Generic types
        assert TypeUtils.check_subtype(List[int], Sequence[int])
        assert not TypeUtils.check_subtype(List[str], Sequence[int])

        # Union types
        assert TypeUtils.check_subtype(int, Union[int, str])
        assert not TypeUtils.check_subtype(bool, Union[int, str])

    def test_callable_validation(self):
        """Test callable validation."""

        # Valid cases
        def func1(x: int, y: str) -> bool:
            return True

        TypeUtils.validate_callable(func1, expected_params=2)
        TypeUtils.validate_callable(func1, return_type=bool)

        # Invalid cases
        def func2(x: int) -> None:
            pass

        with pytest.raises(ValueError):
            TypeUtils.validate_callable(func2, expected_params=2)

        with pytest.raises(TypeError):
            TypeUtils.validate_callable(func2, return_type=bool)

    def test_complex_types(self):
        """Test handling of complex type structures."""
        # Nested sequences
        type_info = TypeUtils.get_type_info(List[List[int]])
        assert type_info.is_sequence
        assert type_info.args[0].__origin__ is list

        # Mixed types
        complex_type = Dict[str, Union[int, List[str]]]
        type_info = TypeUtils.get_type_info(complex_type)
        assert type_info.is_mapping
        assert len(type_info.args) == 2
        assert TypeUtils.check_subtype(List[str], type_info.args[1])

    def test_validation_error_messages(self):
        """Test error message clarity."""
        # Type validation error
        with pytest.raises(TypeError) as exc:
            TypeValidator.validate_type(42, str, param_name="text")
        assert "parameter 'text'" in str(exc.value)
        assert "expected str" in str(exc.value)

        # Sequence validation error
        with pytest.raises(ValueError) as exc:
            TypeValidator.validate_sequence([1, 2], int, min_length=3)
        assert "minimum" in str(exc.value)

        # Mapping validation error
        with pytest.raises(ValueError) as exc:
            TypeValidator.validate_mapping({}, str, int, required_keys={"id"})
        assert "Missing required keys" in str(exc.value)

    def test_edge_cases(self):
        """Test edge case handling."""
        # None handling
        TypeValidator.validate_type(None, object, allow_none=True)

        # Empty collections
        TypeValidator.validate_sequence([], int, allow_empty=True)
        TypeValidator.validate_mapping({}, str, int)

        # Special types
        class Singleton(type):
            pass

        TypeValidator.validate_type(Singleton, type)

    def test_real_world_scenarios(self):
        """Test real-world usage scenarios."""
        # API response validation
        response = {
            "id": "123",
            "data": [1, 2, 3],
            "metadata": {"timestamp": "2024-01-01", "source": "api"},
        }

        # Validate structure
        TypeValidator.validate_mapping(response, str, object)
        TypeValidator.validate_sequence(response["data"], int)
        TypeValidator.validate_mapping(
            response["metadata"],
            str,
            str,
            required_keys={"timestamp", "source"},
        )

        # Configuration validation
        config = {
            "debug": True,
            "port": "8080",
            "limits": {"max_connections": "100", "timeout": "30"},
        }

        # Coerce types
        coerced_config = {
            "debug": TypeUtils.coerce_type(config["debug"], bool),
            "port": TypeUtils.coerce_type(config["port"], int),
            "limits": {
                k: TypeUtils.coerce_type(v, int)
                for k, v in config["limits"].items()
            },
        }

        assert isinstance(coerced_config["port"], int)
        assert isinstance(coerced_config["limits"]["timeout"], int)

    def test_performance(self, benchmark):
        """Test type utility performance."""

        def bench_operation():
            # Create complex type structure
            type_struct = List[Dict[str, Union[int, List[str]]]]

            # Get type info
            type_info = TypeUtils.get_type_info(type_struct)

            # Validate complex structure
            values = [
                {"id": 1, "tags": ["a", "b", "c"]},
                {"id": 2, "tags": ["d", "e", "f"]},
            ]

            TypeValidator.validate_sequence(values, dict)
            for item in values:
                TypeValidator.validate_mapping(item, str, object)
                TypeValidator.validate_sequence(item["tags"], str)

        benchmark(bench_operation)

    def test_error_handling(self):
        """Test error handling and recovery."""

        def validate_data(data: dict) -> bool:
            """Example validation with error handling."""
            try:
                # Validate structure
                TypeValidator.validate_mapping(
                    data, str, object, required_keys={"type", "value"}
                )

                # Type-specific validation
                if data["type"] == "number":
                    TypeUtils.coerce_type(data["value"], float)
                elif data["type"] == "text":
                    TypeValidator.validate_type(data["value"], str)
                else:
                    raise ValueError(f"Unknown type: {data['type']}")

                return True
            except (TypeError, ValueError) as e:
                return False

        # Test success case
        assert validate_data({"type": "number", "value": "42.0"})

        # Test various error cases
        assert not validate_data({"type": "number", "value": "invalid"})
        assert not validate_data({"type": "unknown", "value": "test"})
