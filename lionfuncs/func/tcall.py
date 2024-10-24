import asyncio
from collections.abc import Callable
from typing import Any, TypeVar
from lionfuncs.utils.async_utils import AsyncUtils

T = TypeVar("T")
ErrorHandler = Callable[[Exception], None]
from lionfuncs.ln_undefined import LN_UNDEFINED


async def tcall(
    func: Callable[..., T],
    /,
    *args: Any,
    initial_delay: float = 0,
    timing: bool = False,
    timeout: float | None = None,
    timeout_default: Any = LN_UNDEFINED,  # priority 1
    error_default: Any = LN_UNDEFINED,  # priority 1
    error_msg: str | None = None,
    error_map: dict[type, ErrorHandler] | None = None,  # priority 2
    **kwargs: Any,
) -> T | tuple[T, float]:
    """Execute a function asynchronously with timing and error handling.

    Handles both coroutine and regular functions, supporting timing,
    timeout, and custom error handling.

    Args:
        func: The function to execute (coroutine or regular).
        *args: Positional arguments for the function.
        initial_delay: Delay before execution (seconds).
        error_msg: Custom error message prefix.
        retry_timing: If True, return execution duration.
        retry_timeout: Timeout for function execution (seconds).
        retry_default: Value to return if an error occurs and suppress_err
        is True.
        error_map: Dict mapping exception types to error handlers.
        **kwargs: Additional keyword arguments for the function.

    Returns:
        T | tuple[T, float]: Function result, optionally with duration.

    Raises:
        asyncio.TimeoutError: If execution exceeds the timeout.
        RuntimeError: If an error occurs and suppress_err is False.

    Examples:
        >>> async def slow_func(x):
        ...     await asyncio.sleep(1)
        ...     return x * 2
        >>> result, duration = await tcall(slow_func, 5, retry_timing=True)
        >>> print(f"Result: {result}, Duration: {duration:.2f}s")
        Result: 10, Duration: 1.00s

    Note:
        - Automatically handles both coroutine and regular functions.
        - Provides timing information for performance analysis.
        - Supports custom error handling and suppression.
    """
    start = AsyncUtils.time()

    try:
        await asyncio.sleep(initial_delay)
        result = None

        if not AsyncUtils.is_coroutine_func(func):
            func = AsyncUtils.force_async(func)

        if timeout is None:
            result = await func(*args, **kwargs)
        else:
            result = await asyncio.wait_for(
                func(*args, **kwargs), timeout=timeout
            )

        duration = AsyncUtils.time() - start
        return (result, duration) if timing else result

    except asyncio.TimeoutError as e:

        if timeout_default is not LN_UNDEFINED:
            return (timeout_default, duration) if timing else timeout_default

        if asyncio.TimeoutError in error_map:
            result = await AsyncUtils.custom_error_handler(e, error_map)
            duration = AsyncUtils.time() - start
            return (result, duration) if timing else result

        error_msg = f"{error_msg or ''} Timeout {timeout} seconds exceeded"
        raise asyncio.TimeoutError(error_msg) from e

    except Exception as e:

        if error_default is not LN_UNDEFINED:
            duration = AsyncUtils.time() - start
            return (error_default, duration) if timing else error_default

        if error_map and type(e) in error_map:
            result = await AsyncUtils.custom_error_handler(e, error_map)
            duration = AsyncUtils.time() - start
            return (result, duration) if timing else result

        error_msg = f"{error_msg or ''}Error: {e}"
        raise type(e)(error_msg) from e
