import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from lionfuncs.func.utils import (
    custom_error_handler,
    force_async,
    is_coroutine_func,
)

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
        T: The result of the function call.

    Raises:
        Exception: Any unhandled exception from the function execution.

    Examples:
        >>> async def example_func(x):
        ...     return x * 2
        >>> await ucall(example_func, 5)
        10
        >>> await ucall(lambda x: x + 1, 5)  # Non-coroutine function
        6

    Note:
        - Automatically wraps non-coroutine functions for async execution.
        - Manages event loop creation and closure when necessary.
        - Applies custom error handling based on the provided error_map.
    """
    try:
        if not is_coroutine_func(func):
            func = force_async(func)

        # Checking for a running event loop
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                return await func(*args, **kwargs)
            else:
                return await asyncio.run(func(*args, **kwargs))

        except RuntimeError:  # No running event loop
            loop = asyncio.new_event_loop()
            result = await func(*args, **kwargs)
            loop.close()
            return result

    except Exception as e:
        if error_map:

            return await custom_error_handler(e, error_map)
        raise e
