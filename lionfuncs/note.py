"""
Container class for managing nested dictionary data structures.

Features:
- Rich nested data operations
- Dictionary-like interface
- Type-safe operations
- Flattening support
- Serialization support
"""

from collections.abc import ItemsView, Iterator, ValuesView
from typing import Any, Dict, List, Union

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from lionfuncs.data import flatten, nget, ninsert, npop, nset
from lionfuncs.ln_undefined import LN_UNDEFINED
from lionfuncs.parse.to_list import to_list
from lionfuncs.utils import copy

# Type definitions
INDICE_TYPE = Union[str, List[Union[str, int]]]


class Note(BaseModel):
    """A container for managing nested dictionary data structures."""

    content: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
        populate_by_name=True,
    )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Note instance with given keyword arguments."""
        super().__init__()
        self.content = kwargs

    @field_serializer("content")
    def _serialize_content(self, value: Any) -> Dict[str, Any]:
        """Serialize content with deep copy."""
        output_dict = copy(value, deep=True)
        return output_dict

    def pop(
        self,
        indices: INDICE_TYPE,
        /,
        default: Any = LN_UNDEFINED,
    ) -> Any:
        """
        Remove and return item from nested structure.

        Args:
            indices: Path to item.
            default: Value to return if item not found.
        """
        indices = to_list(indices, flatten=True, dropna=True)
        return npop(self.content, indices, default)

    def insert(self, indices: INDICE_TYPE, value: Any, /) -> None:
        """
        Insert value into nested structure.

        Args:
            indices: Path where to insert.
            value: Value to insert.
        """
        indices = to_list(indices, flatten=True, dropna=True)
        ninsert(self.content, indices, value)

    def set(self, indices: INDICE_TYPE, value: Any, /) -> None:
        """
        Set value in nested structure.

        Args:
            indices: Path where to set.
            value: Value to set.
        """
        indices = to_list(indices, flatten=True, dropna=True)

        if self.get(indices, None) is None:
            self.insert(indices, value)
        else:
            nset(self.content, indices, value)

    def get(
        self,
        indices: INDICE_TYPE,
        /,
        default: Any = LN_UNDEFINED,
    ) -> Any:
        """
        Get value from nested structure.

        Args:
            indices: Path to value.
            default: Value to return if not found.
        """
        indices = to_list(indices, flatten=True, dropna=True)
        return nget(self.content, indices, default)

    def keys(self, /, flat: bool = False, **kwargs: Any) -> List:
        """
        Get Note keys.

        Args:
            flat: Return flattened keys if True.
            kwargs: Additional flattening arguments.
        """
        if flat:
            return list(flatten(self.content, **kwargs).keys())
        return list(self.content.keys())

    def values(self, /, flat: bool = False, **kwargs: Any) -> ValuesView:
        """
        Get Note values.

        Args:
            flat: Return flattened values if True.
            kwargs: Additional flattening arguments.
        """
        if flat:
            return flatten(self.content, **kwargs).values()
        return self.content.values()

    def items(self, /, flat: bool = False, **kwargs: Any) -> ItemsView:
        """
        Get Note items.

        Args:
            flat: Return flattened items if True.
            kwargs: Additional flattening arguments.
        """
        if flat:
            return flatten(self.content, **kwargs).items()
        return self.content.items()

    def to_dict(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Convert Note to dictionary.

        Args:
            kwargs: Additional model_dump arguments.
        """
        output_dict = self.model_dump(**kwargs)
        return output_dict["content"]

    def clear(self) -> None:
        """Clear Note content."""
        self.content.clear()

    def update(
        self,
        indices: INDICE_TYPE,
        value: Any,
    ) -> None:
        """
        Update nested structure at indices.

        Args:
            indices: Path to update.
            value: Value to update with.
        """
        existing = None
        if not indices:
            existing = self.content
        else:
            existing = self.get(indices, None)

        if existing is None:
            if not isinstance(value, (list, dict)):
                value = [value]
            self.set(indices, value)

        if isinstance(existing, list):
            if isinstance(value, list):
                existing.extend(value)
            else:
                existing.append(value)

        elif isinstance(existing, dict):
            if isinstance(value, self.__class__):
                value = value.content

            if isinstance(value, dict):
                existing.update(value)
            else:
                raise ValueError(
                    "Cannot update dictionary with non-dictionary value"
                )

    @classmethod
    def from_dict(cls, kwargs: Any) -> "Note":
        """
        Create Note from dictionary.

        Args:
            kwargs: Dictionary to convert.
        """
        return cls(**kwargs)

    def __contains__(self, indices: INDICE_TYPE) -> bool:
        """Check if Note contains indices."""
        return self.content.get(indices, LN_UNDEFINED) is not LN_UNDEFINED

    def __len__(self) -> int:
        """Get length of Note content."""
        return len(self.content)

    def __iter__(self) -> Iterator[str]:
        """Get iterator over Note content."""
        return iter(self.content)

    def __next__(self) -> str:
        """Get next item in Note content."""
        return next(iter(self.content))

    def __str__(self) -> str:
        """Get string representation."""
        return str(self.content)

    def __repr__(self) -> str:
        """Get detailed string representation."""
        return repr(self.content)

    def __getitem__(self, indices: INDICE_TYPE) -> Any:
        """Get item using index notation."""
        indices = to_list(indices, flatten=True, dropna=True)
        return self.get(indices)

    def __setitem__(self, indices: INDICE_TYPE, value: Any) -> None:
        """Set item using index notation."""
        self.set(indices, value)


def note(**kwargs: Any) -> Note:
    """
    Create Note object from keyword arguments.

    Args:
        kwargs: Initial data for Note.

    Returns:
        New Note instance.
    """
    return Note(**kwargs)


__all__ = ["Note", "note"]
