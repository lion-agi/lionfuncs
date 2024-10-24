"""Base classes and types for the utility system."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, TypeVar, Union
from pathlib import Path

T = TypeVar("T")
PathLike = Union[str, Path]


class UtilityError(Exception):
    """Base exception for utility errors."""

    pass


class UtilityGroup(ABC):
    """Base class for utility groups."""

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Get utility group name."""
        pass

    @classmethod
    def register_utility(cls, name: str, func: Callable) -> None:
        """Register a utility function."""
        if not hasattr(cls, "_registry"):
            cls._registry = {}
        cls._registry[name] = func

    @classmethod
    def get_utility(cls, name: str) -> Optional[Callable]:
        """Get a registered utility function."""
        if not hasattr(cls, "_registry"):
            return None
        return cls._registry.get(name)
