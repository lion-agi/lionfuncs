"""Utility functions for type checking and nested structure operations.

This module provides utilities for checking type homogeneity in data structures
and handling nested data structure operations.
"""

from typing import Any, Mapping, TypeVar, Union, Optional, Tuple, Type
from collections.abc import Sequence, Iterable

# Type aliases for clarity
NestedType = Union[list[Any], dict[Any, Any]]
TypeSpec = Union[Type, Tuple[Type, ...]]
TypeCheckResult = Union[bool, Tuple[bool, Optional[Type]]]

# Type variable for generic type hints
T = TypeVar("T")


class TypeChecker:
    """Utility class for type checking operations."""

    @staticmethod
    def is_homogeneous(iterables: NestedType, type_check: TypeSpec) -> bool:
        """Check if all elements in a structure are of the same type.

        Args:
            iterables: List or dictionary to check
            type_check: Type or tuple of types to check against

        Returns:
            True if all elements match the type specification
        """
        if isinstance(iterables, list):
            return all(isinstance(it, type_check) for it in iterables)
        elif isinstance(iterables, dict):
            return all(
                isinstance(val, type_check) for val in iterables.values()
            )
        return isinstance(iterables, type_check)

    @staticmethod
    def is_same_dtype(
        input_: NestedType,
        dtype: Optional[Type] = None,
        return_dtype: bool = False,
    ) -> TypeCheckResult:
        """Check if all elements have the same data type.

        Args:
            input_: List or dictionary to check
            dtype: Expected data type (uses first element type if None)
            return_dtype: Whether to return the detected type

        Returns:
            Boolean result or tuple of (result, type)
        """
        if not input_:
            return (True, None) if return_dtype else True

        # Get iterable and first element type
        iterable = input_.values() if isinstance(input_, dict) else input_
        first_element = next(iter(iterable), None)
        first_type = type(first_element) if first_element is not None else None

        # Use provided or detected type
        check_type = dtype or first_type
        if check_type is None:
            return (False, None) if return_dtype else False

        # Check all elements
        result = all(isinstance(elem, check_type) for elem in iterable)
        return (result, check_type) if return_dtype else result

    @staticmethod
    def is_structure_homogeneous(
        structure: Any, return_structure_type: bool = False
    ) -> TypeCheckResult:
        """Check if a nested structure contains uniform container types.

        Args:
            structure: Nested structure to check
            return_structure_type: Whether to return the container type

        Returns:
            Boolean result or tuple of (result, type)
        """

        def _check_structure(substructure: Any) -> Tuple[bool, Optional[Type]]:
            """Recursive structure checking."""
            structure_type = None

            # Handle list structures
            if isinstance(substructure, list):
                structure_type = list
                return _check_list_structure(substructure)

            # Handle dict structures
            elif isinstance(substructure, dict):
                structure_type = dict
                return _check_dict_structure(substructure)

            return True, structure_type

        def _check_list_structure(lst: list) -> Tuple[bool, Optional[Type]]:
            """Check homogeneity of list structure."""
            for item in lst:
                if isinstance(item, (list, dict)) and not isinstance(
                    item, list
                ):
                    return False, None
                result, _ = _check_structure(item)
                if not result:
                    return False, None
            return True, list

        def _check_dict_structure(dct: dict) -> Tuple[bool, Optional[Type]]:
            """Check homogeneity of dict structure."""
            for item in dct.values():
                if isinstance(item, (list, dict)) and not isinstance(
                    item, dict
                ):
                    return False, None
                result, _ = _check_structure(item)
                if not result:
                    return False, None
            return True, dict

        is_homogeneous, structure_type = _check_structure(structure)
        return (
            (is_homogeneous, structure_type)
            if return_structure_type
            else is_homogeneous
        )


class NestedOperations:
    """Utility class for nested structure operations."""

    @staticmethod
    def deep_update(
        original: dict[Any, Any], update: dict[Any, Any]
    ) -> dict[Any, Any]:
        """Recursively merge dictionaries.

        Updates nested dictionaries instead of overwriting them.

        Args:
            original: Base dictionary to update
            update: Dictionary with updates to apply

        Returns:
            Updated dictionary (modified in place)
        """
        for key, value in update.items():
            if isinstance(value, dict) and key in original:
                original[key] = NestedOperations.deep_update(
                    original.get(key, {}), value
                )
            else:
                original[key] = value
        return original

    @staticmethod
    def get_target_container(
        nested: NestedType, indices: list[Union[int, str]]
    ) -> NestedType:
        """Navigate to a specific container in a nested structure.

        Args:
            nested: The nested structure to navigate
            indices: Path to the target container

        Returns:
            The container at the specified path

        Raises:
            IndexError: Invalid list index
            KeyError: Invalid dictionary key
            TypeError: Invalid container type
        """
        current = nested
        for index in indices:
            if isinstance(current, list):
                # Convert string indices to integers if possible
                if isinstance(index, str) and index.isdigit():
                    index = int(index)

                if not isinstance(index, int):
                    raise TypeError(f"Invalid list index type: {type(index)}")

                if not 0 <= index < len(current):
                    raise IndexError(f"List index out of range: {index}")

                current = current[index]

            elif isinstance(current, dict):
                if index not in current:
                    raise KeyError(f"Dictionary key not found: {index}")
                current = current[index]

            else:
                raise TypeError(f"Invalid container type: {type(current)}")

        return current


# Convenience functions that use the class methods
is_homogeneous = TypeChecker.is_homogeneous
is_same_dtype = TypeChecker.is_same_dtype
is_structure_homogeneous = TypeChecker.is_structure_homogeneous
deep_update = NestedOperations.deep_update
get_target_container = NestedOperations.get_target_container
