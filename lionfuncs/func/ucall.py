"""Unified async function execution with error handling."""

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from lionfuncs.utils.async_utils import AsyncUtils

T = TypeVar("T")
ErrorHandler = Callable[[Exception], Any]


async def ucall(
    func: Callable[..., T],
    /,
    *args: Any,
    error_map: dict[type, ErrorHandler] | None = None,
    **kwargs: Any,
) -> T:
    """Execute a function asynchronously with error handling.

    Ensures asynchronous execution of both coroutine and regular functions,
    managing event loops and applying custom error handling.

    Args:
        func: The function to be executed (coroutine or regular).
        *args: Positional arguments for the function.
        error_map: Dict mapping exception types to error handlers.
        **kwargs: Keyword arguments for the function.

    Returns:
        T: The result of the function execution.

    Raises:
        Exception: Any unhandled exception from the function execution.
    """
    # Ensure async function
    if not AsyncUtils.is_coroutine_func(func):
        func = AsyncUtils.force_async(func)

    try:
        # Check for existing event loop
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                result = await func(*args, **kwargs)
                return result
        except RuntimeError:
            # No running loop, use context manager
            with AsyncUtils.event_loop() as loop:
                result = await func(*args, **kwargs)
                return result

    except Exception as e:
        if error_map:
            return await AsyncUtils.custom_error_handler(e, error_map)
        raise e
