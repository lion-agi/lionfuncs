"""Core asynchronous operation utilities.

This module provides fundamental utilities for handling asynchronous operations,
focusing on core functionality like throttling, concurrency control, and
event loop management.

Typical usage:
    >>> @Throttle(period=1.0)
    ... async def rate_limited():
    ...     pass

    >>> @AsyncUtils.max_concurrent(limit=5)
    ... async def concurrent_op():
    ...     pass
"""

import asyncio
import logging
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, contextmanager
from functools import lru_cache, wraps
from typing import Any, AsyncIterator, Callable, Optional, TypeVar, Dict

from lionfuncs.utils.global_utils import time

T = TypeVar("T")
AsyncCallable = Callable[..., T]
ErrorHandler = Callable[[Exception], Any]


class Throttle:
    """Advanced rate limiting implementation.

    Features:
    - Per-instance and global rate limiting
    - Burst allowance
    - Fair queuing
    - Async and sync support

    Args:
        period: Minimum time between operations in seconds.
        max_burst: Maximum operations allowed in burst.
        global_limit: Use global rate limiting across instances.

    Attributes:
        period: Time between operations.
        max_burst: Maximum burst size.
        global_limit: Global limiting flag.
        last_called: Last operation timestamp.
        timestamps: Operation timestamp queue.
        _lock: Instance rate limit lock.

    Raises:
        ValueError: If period or max_burst are invalid.
    """

    # Class-level state for global limiting
    _global_lock: Optional[asyncio.Lock] = None
    _global_timestamps: Optional[deque] = None

    def __init__(
        self, period: float, *, max_burst: int = 1, global_limit: bool = False
    ) -> None:
        if period <= 0:
            raise ValueError("Period must be positive")
        if max_burst < 1:
            raise ValueError("Max burst must be at least 1")

        self.period = period
        self.max_burst = max_burst
        self.global_limit = global_limit

        # Instance-specific state
        self.last_called = 0
        self.timestamps: deque = deque(maxlen=max_burst)
        self._lock = asyncio.Lock()

        # Initialize global state if needed
        if global_limit:
            if not Throttle._global_lock:
                Throttle._global_lock = asyncio.Lock()
            if not Throttle._global_timestamps:
                Throttle._global_timestamps = deque(maxlen=max_burst)

    async def _acquire(self) -> None:
        """Acquire rate limit slot.

        Raises:
            asyncio.TimeoutError: If slot cannot be acquired in time.
        """
        async with Throttle._global_lock if self.global_limit else self._lock:
            now = time()
            timestamps = (
                Throttle._global_timestamps
                if self.global_limit
                else self.timestamps
            )

            # Clean old timestamps
            while timestamps and now - timestamps[0] > self.period:
                timestamps.popleft()

            # Calculate delay if needed
            if len(timestamps) >= self.max_burst:
                delay = self.period - (now - timestamps[0])
                if delay > 0:
                    await asyncio.sleep(delay)
                    now = time()

            timestamps.append(now)
            self.last_called = now

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Apply throttling to function.

        Args:
            func: Function to throttle.

        Returns:
            Throttled function wrapper.

        Raises:
            AsyncError: If throttling fails.
        """
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                await self._acquire()
                return await func(*args, **kwargs)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            async def _throttled():
                await self._acquire()
                return func(*args, **kwargs)

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(_throttled())

        return sync_wrapper


class AsyncUtils:
    """Core async operation utilities.

    This class provides static methods for common async operations:
    - Function type checking and conversion
    - Event loop management
    - Error handling
    - Concurrency control
    - Timeout management
    """

    _executor = ThreadPoolExecutor()

    @staticmethod
    def time() -> float:
        """Get current time in loop or system time."""
        try:
            return asyncio.get_event_loop().time()
        except RuntimeError:
            return time()

    @staticmethod
    @lru_cache(maxsize=128)
    def is_coroutine_func(func: Callable[..., Any]) -> bool:
        """Check if a function is a coroutine function.

        Args:
            func: Function to check.

        Returns:
            True if function is a coroutine function.
        """
        return asyncio.iscoroutinefunction(func)

    @staticmethod
    def force_async(func: Callable[..., T]) -> Callable[..., Callable[..., T]]:
        """Convert synchronous function to asynchronous.

        Args:
            func: Function to convert.

        Returns:
            Async wrapper for function.
        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            future = AsyncUtils._executor.submit(func, *args, **kwargs)
            return asyncio.wrap_future(future)

        return wrapper

    @staticmethod
    @contextmanager
    def event_loop():
        """Event loop context manager.

        Yields:
            asyncio.AbstractEventLoop: New event loop.

        Example:
            >>> with AsyncUtils.event_loop() as loop:
            ...     loop.run_until_complete(async_func())
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            yield loop
        finally:
            if not loop.is_closed():
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()

    @staticmethod
    async def custom_error_handler(
        error: Exception, error_map: Dict[type, ErrorHandler]
    ) -> None:
        """Handle errors using custom error map.

        Args:
            error: Exception to handle.
            error_map: Mapping of error types to handlers.
        """
        for error_type, handler in error_map.items():
            if isinstance(error, error_type):
                if AsyncUtils.is_coroutine_func(handler):
                    return await handler(error)
                return handler(error)
        logging.error(f"Unhandled error: {error}")

    @staticmethod
    def max_concurrent(
        limit: int,
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Limit maximum concurrent executions.

        Args:
            limit: Maximum concurrent executions.

        Returns:
            Decorator limiting concurrency.

        Raises:
            ValueError: If limit is less than 1.
        """
        if limit < 1:
            raise ValueError("Concurrency limit must be positive")

        semaphore = asyncio.Semaphore(limit)

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            if not AsyncUtils.is_coroutine_func(func):
                func = AsyncUtils.force_async(func)

            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any):
                async with semaphore:
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    @asynccontextmanager
    async def timeout_context(
        timeout: float, cleanup: Optional[Callable[[], Any]] = None
    ) -> AsyncIterator[None]:
        """Timeout context manager with cleanup.

        Args:
            timeout: Timeout in seconds.
            cleanup: Optional cleanup function.

        Yields:
            None

        Raises:
            asyncio.TimeoutError: If operation times out.
        """
        try:
            async with asyncio.timeout(timeout):
                yield
        except (asyncio.TimeoutError, Exception) as e:
            if cleanup:
                if AsyncUtils.is_coroutine_func(cleanup):
                    await cleanup()
                else:
                    cleanup()
            raise
