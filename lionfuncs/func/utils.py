"""
Async utilities for handling concurrent operations and error management.
"""

import asyncio
import functools
import logging
import time
from ast import Dict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache, wraps
from typing import Any, TypeVar

from lionfuncs.utils import time as _t

T = TypeVar("T")

ErrorHandler = TypeVar("ErrorHandler", bound=Callable)


class Throttle:
    """
    Provide a throttling mechanism for function calls.

    When used as a decorator, it ensures that the decorated function can only
    be called once per specified period. Subsequent calls within this period
    are delayed to enforce this constraint.

    Attributes:
        period: The minimum time period (in seconds) between successive calls.

    Example:
        >>> throttle = Throttle(1.0)  # 1 second delay
        >>> @throttle
        ... def frequent_call():
        ...     return "Called"
    """

    def __init__(self, period: float) -> None:
        """
        Initialize a new instance of Throttle.

        Args:
            period: The minimum time period (in seconds) between
                successive calls.
        """
        self.period = period
        self.last_called = 0

    def __call__(self, func: Callable) -> Callable:
        """
        Decorate a synchronous function with the throttling mechanism.

        Args:
            func: The synchronous function to be throttled.

        Returns:
            The throttled synchronous function.

        Example:
            >>> @Throttle(1.0)
            ... def sync_func():
            ...     return "Called"
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            elapsed = _t() - self.last_called
            if elapsed < self.period:
                time.sleep(self.period - elapsed)
            self.last_called = _t()
            return func(*args, **kwargs)

        return wrapper

    def __call_async__(self, func: Callable) -> Callable:
        """
        Decorate an asynchronous function with the throttling mechanism.

        Args:
            func: The asynchronous function to be throttled.

        Returns:
            The throttled asynchronous function.

        Example:
            >>> @Throttle(1.0)
            ... async def async_func():
            ...     return "Called"
        """

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            elapsed = _t() - self.last_called
            if elapsed < self.period:
                await asyncio.sleep(self.period - elapsed)
            self.last_called = _t()
            return await func(*args, **kwargs)

        return wrapper


__all__ = ["Throttle"]


# Type conversion utilities
def force_async(fn: Callable) -> Callable:
    """
    Convert a synchronous function to an asynchronous function using a thread pool.

    Args:
        fn: The synchronous function to convert.

    Returns:
        The asynchronous version of the function.

    Example:
        >>> @force_async
        ... def sync_func(x):
        ...     return x * 2
        >>> async def main():
        ...     result = await sync_func(5)
        ...     print(result)  # 10
    """
    pool = ThreadPoolExecutor()

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        future = pool.submit(fn, *args, **kwargs)
        return asyncio.wrap_future(future)

    return wrapper


@lru_cache(maxsize=None)
def is_coroutine_func(func: Callable) -> bool:
    """
    Check if a function is a coroutine function.

    Args:
        func: The function to check.

    Returns:
        True if the function is a coroutine function, False otherwise.

    Example:
        >>> async def async_func(): pass
        >>> is_coroutine_func(async_func)
        True
        >>> is_coroutine_func(lambda x: x)
        False
    """
    return asyncio.iscoroutinefunction(func)


# Error handling utilities
async def custom_error_handler(error: Exception, error_map: Dict) -> None:
    """
    Handle errors according to a provided error mapping.

    Args:
        error: The exception to handle.
        error_map: Dictionary mapping exception types to handler functions.

    Returns:
        None: If no handler is found, logs the error.
        Any: Result from the error handler if one is found.

    Example:
        >>> error_map = {ValueError: lambda e: "Invalid value"}
        >>> await custom_error_handler(ValueError("bad"), error_map)
        'Invalid value'
    """
    for error_type, handler in error_map.items():
        if isinstance(error, error_type):
            if is_coroutine_func(handler):
                return await handler(error)
            return handler(error)
    logging.error(f"Unhandled error: {error}")


# Concurrency control utilities
def max_concurrent(func: Callable, limit: int) -> Callable:
    """
    Limit the concurrency of function execution using a semaphore.

    Args:
        func: The function to limit concurrency for.
        limit: The maximum number of concurrent executions.

    Returns:
        The function wrapped with concurrency control.

    Example:
        >>> @max_concurrent(limit=2)
        ... async def limited_func():
        ...     await asyncio.sleep(1)
    """
    if not is_coroutine_func(func):
        func = force_async(func)
    semaphore = asyncio.Semaphore(limit)

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        async with semaphore:
            return await func(*args, **kwargs)

    return wrapper


def throttle(func: Callable, period: float) -> Callable:
    """
    Throttle function execution to limit the rate of calls.

    Args:
        func: The function to throttle.
        period: The minimum time interval between consecutive calls.

    Returns:
        The throttled function.

    Example:
        >>> @throttle(period=1.0)
        ... async def rate_limited():
        ...     return "Called"
    """
    if not is_coroutine_func(func):
        func = force_async(func)
    throttle_instance = Throttle(period)

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        await throttle_instance(func)(*args, **kwargs)
        return await func(*args, **kwargs)

    return wrapper


__all__ = [
    "force_async",
    "is_coroutine_func",
    "custom_error_handler",
    "max_concurrent",
    "throttle",
]
