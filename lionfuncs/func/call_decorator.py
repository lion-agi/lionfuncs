"""
Collection of decorators for enhancing function calls with async capabilities,
retry logic, throttling, and composition.

Features:
- Retry mechanism with configurable backoff
- Throttling for rate limiting
- Concurrency control
- Function composition
- Pre/post processing
- Result mapping
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any, Dict, Optional, TypeVar

from lionfuncs.func.call_ import rcall, ucall
from lionfuncs.func.utils import Throttle, force_async, is_coroutine_func
from lionfuncs.ln_undefined import LN_UNDEFINED

T = TypeVar("T")
F = TypeVar("F", bound=Callable)
ErrorHandler = TypeVar("ErrorHandler", bound=Callable)


class CallDecorator:
    """A collection of decorators to enhance function calls."""

    @staticmethod
    def retry(
        num_retries: int = 0,
        initial_delay: float = 0,
        retry_delay: float = 0,
        backoff_factor: float = 1,
        retry_default: Any = LN_UNDEFINED,
        retry_timeout: Optional[float] = None,
        retry_timing: bool = False,
        verbose_retry: bool = True,
        error_msg: Optional[str] = None,
        error_map: Optional[Union[Dict, None]] = None,
    ) -> Callable:
        """
        Decorator to automatically retry a function call on failure.

        Args:
            num_retries: Number of retry attempts.
            initial_delay: Initial delay before retrying.
            retry_delay: Delay between retries.
            backoff_factor: Factor to increase delay after each retry.
            retry_default: Default value to return on failure.
            retry_timeout: Timeout for each function call.
            retry_timing: If True, logs the time taken for each call.
            verbose_retry: If True, logs the retries.
            error_msg: Custom error message on failure.
            error_map: A map of exception types to handler functions.

        Returns:
            The decorated function.

        Example:
            >>> @CallDecorator.retry(num_retries=3, retry_delay=1)
            ... async def flaky_operation():
            ...     # May fail occasionally
            ...     pass
        """

        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await rcall(
                    func,
                    *args,
                    num_retries=num_retries,
                    initial_delay=initial_delay,
                    retry_delay=retry_delay,
                    backoff_factor=backoff_factor,
                    retry_default=retry_default,
                    retry_timeout=retry_timeout,
                    retry_timing=retry_timing,
                    verbose_retry=verbose_retry,
                    error_msg=error_msg,
                    error_map=error_map,
                    **kwargs,
                )

            return wrapper

        return decorator

    @staticmethod
    def throttle(period: float) -> Callable:
        """
        Decorator to limit the execution frequency of a function.

        Args:
            period: Minimum time in seconds between function calls.

        Returns:
            The decorated function.

        Example:
            >>> @CallDecorator.throttle(1.0)
            ... async def rate_limited():
            ...     # Maximum one call per second
            ...     pass
        """

        def decorator(func: F) -> F:
            if not is_coroutine_func(func):
                func = force_async(func)
            throttle_instance = Throttle(period)

            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                await throttle_instance(func)(*args, **kwargs)
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def max_concurrent(limit: int) -> Callable:
        """
        Decorator to limit the maximum number of concurrent executions.

        Args:
            limit: Maximum number of concurrent executions.

        Returns:
            The decorated function.

        Example:
            >>> @CallDecorator.max_concurrent(5)
            ... async def limited_concurrency():
            ...     # Maximum 5 concurrent executions
            ...     pass
        """

        def decorator(func: F) -> F:
            if not is_coroutine_func(func):
                func = force_async(func)
            semaphore = asyncio.Semaphore(limit)

            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                async with semaphore:
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def compose(*functions: Callable) -> Callable:
        """
        Decorator to compose multiple functions, applying in sequence.

        Args:
            functions: Functions to apply in sequence.

        Returns:
            The decorated function.

        Example:
            >>> def double(x): return x * 2
            >>> def add_one(x): return x + 1
            >>> @CallDecorator.compose(double, add_one)
            ... async def base_func(x):
            ...     return x
            >>> # Result will be (x * 2) + 1
        """

        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                value = await ucall(func, *args, **kwargs)
                for function in functions:
                    try:
                        value = await ucall(function, value)
                    except Exception as e:
                        raise ValueError(
                            f"Error in function {function.__name__}: {e}"
                        )
                return value

            return wrapper

        return decorator

    @staticmethod
    def pre_post_process(
        preprocess: Optional[Callable] = None,
        postprocess: Optional[Callable] = None,
        preprocess_args: tuple = (),
        preprocess_kwargs: dict = {},
        postprocess_args: tuple = (),
        postprocess_kwargs: dict = {},
    ) -> Callable:
        """
        Decorator to apply pre-processing and post-processing functions.

        Args:
            preprocess: Function to apply before main function.
            postprocess: Function to apply after main function.
            preprocess_args: Arguments for preprocess function.
            preprocess_kwargs: Keyword arguments for preprocess.
            postprocess_args: Arguments for postprocess function.
            postprocess_kwargs: Keyword arguments for postprocess.

        Returns:
            The decorated function.

        Example:
            >>> def validate(x):
            ...     if x < 0: raise ValueError("Negative")
            ...     return x
            >>> def format_result(x): return f"Result: {x}"
            >>> @CallDecorator.pre_post_process(
            ...     preprocess=validate,
            ...     postprocess=format_result
            ... )
            ... async def process(x):
            ...     return x * 2
        """

        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Pre-processing
                if preprocess:
                    processed_args = [
                        await ucall(
                            preprocess,
                            arg,
                            *preprocess_args,
                            **preprocess_kwargs,
                        )
                        for arg in args
                    ]
                    processed_kwargs = {
                        k: await ucall(
                            preprocess,
                            v,
                            *preprocess_args,
                            **preprocess_kwargs,
                        )
                        for k, v in kwargs.items()
                    }
                else:
                    processed_args = args
                    processed_kwargs = kwargs

                # Main function execution
                result = await ucall(func, *processed_args, **processed_kwargs)

                # Post-processing
                if postprocess:
                    return await ucall(
                        postprocess,
                        result,
                        *postprocess_args,
                        **postprocess_kwargs,
                    )
                return result

            return wrapper

        return decorator

    @staticmethod
    def map(function: Callable) -> Callable:
        """
        Decorator to map a function over async function results.

        Args:
            function: Mapping function to apply to each element.

        Returns:
            The decorated function.

        Example:
            >>> @CallDecorator.map(str.upper)
            ... async def get_names():
            ...     return ["alice", "bob"]
            >>> # Returns ["ALICE", "BOB"]
        """

        def decorator(func: F) -> F:
            if is_coroutine_func(func):

                @wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    values = await func(*args, **kwargs)
                    return [function(value) for value in values]

                return async_wrapper
            else:

                @wraps(func)
                def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                    values = func(*args, **kwargs)
                    return [function(value) for value in values]

                return sync_wrapper

        return decorator


__all__ = ["CallDecorator"]
