"""Cache utilities for storing and managing cached data.

This module provides utilities for caching with features like TTL,
memory limits, thread safety, and automatic cleanup.
"""

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Generic, Optional, TypeVar, Union
from functools import wraps

T = TypeVar("T")
TimeDelta = Union[int, float, timedelta]


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with value and metadata."""

    value: T
    expires_at: Optional[float] = None
    last_accessed: float = time.time()
    access_count: int = 0

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return self.expires_at is not None and time.time() > self.expires_at

    def access(self) -> None:
        """Update entry access metadata."""
        self.last_accessed = time.time()
        self.access_count += 1


class Cache(Generic[T]):
    """Thread-safe cache implementation with TTL and size limits."""

    def __init__(
        self,
        maxsize: int = 128,
        ttl: Optional[TimeDelta] = None,
        cleanup_interval: Optional[TimeDelta] = None,
    ):
        """Initialize cache."""
        if maxsize < 0:
            raise ValueError("maxsize must be non-negative")
        if ttl is not None and ttl < 0:
            raise ValueError("ttl must be non-negative")
        if cleanup_interval is not None and cleanup_interval < 0:
            raise ValueError("cleanup_interval must be non-negative")

        self.maxsize = maxsize
        self.ttl = self._parse_timedelta(ttl)
        self.cleanup_interval = self._parse_timedelta(cleanup_interval)

        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = threading.RLock()
        self._last_cleanup = time.time()

    def get(self, key: str, default: Any = None) -> Optional[T]:
        """Get value from cache."""
        with self._lock:
            self._maybe_cleanup()

            entry = self._cache.get(key)
            if entry is None:
                return default

            if entry.is_expired():
                del self._cache[key]
                return default

            entry.access()
            return entry.value

    def set(self, key: str, value: T, ttl: Optional[TimeDelta] = None) -> None:
        """Set cache value."""
        with self._lock:
            self._maybe_cleanup()

            expires_at = None
            if ttl is not None:
                ttl_seconds = self._parse_timedelta(ttl)
                if ttl_seconds == 0:
                    return  # Don't cache items with zero TTL
                expires_at = time.time() + ttl_seconds
            elif self.ttl is not None:
                expires_at = time.time() + self.ttl

            entry = CacheEntry(
                value=value, expires_at=expires_at, last_accessed=time.time()
            )

            if key in self._cache:
                del self._cache[key]

            self._cache[key] = entry

            while len(self._cache) > self.maxsize:
                self._cache.popitem(last=False)

    def delete(self, key: str) -> None:
        """Delete cache entry.

        Args:
            key: Cache key
        """
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._last_cleanup = time.time()

    def cleanup(self) -> None:
        """Remove expired entries."""
        with self._lock:
            now = time.time()
            expired = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]
            for key in expired:
                del self._cache[key]
            self._last_cleanup = now

    @property
    def size(self) -> int:
        """Current cache size."""
        return len(self._cache)

    def _maybe_cleanup(self) -> None:
        """Run cleanup if needed."""
        now = time.time()
        if (
            self.cleanup_interval
            and now - self._last_cleanup > self.cleanup_interval
        ):
            expired = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]
            for key in expired:
                del self._cache[key]
            self._last_cleanup = now

    @staticmethod
    def _parse_timedelta(value: Optional[TimeDelta]) -> Optional[float]:
        """Convert time delta to seconds."""
        if value is None:
            return None
        if isinstance(value, timedelta):
            return value.total_seconds()
        return float(value)


class CacheUtils:
    """Cache utility functions."""

    @staticmethod
    def memoize(
        maxsize: int = 128,
        ttl: Optional[TimeDelta] = None,
        key_maker: Optional[Callable[..., str]] = None,
    ):
        """Memoization decorator with TTL."""
        # Create cache with lock for thread safety
        cache: Cache[Any] = Cache(maxsize=maxsize, ttl=ttl)
        lock = threading.Lock()

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_maker:
                    key = key_maker(*args, **kwargs)
                else:
                    # Make key from arguments
                    key = f"{args}:{sorted(kwargs.items())}"

                # Thread-safe cache access
                with lock:
                    result = cache.get(key)
                    if result is None:
                        result = func(*args, **kwargs)
                        cache.set(key, result)
                    return result

            # Add cache management methods
            wrapper.cache_clear = cache.clear
            wrapper.cache_info = lambda: {
                "size": len(cache._cache),
                "maxsize": cache.maxsize,
            }
            return wrapper

        return decorator

    @staticmethod
    def timed_cache(
        seconds: int, maxsize: Optional[int] = None, typed: bool = False
    ):
        """Time-based cache decorator."""
        if seconds <= 0:
            raise ValueError("seconds must be positive")
        if maxsize is not None and maxsize < 0:
            raise ValueError("maxsize must be non-negative")

        maxsize = maxsize if maxsize is not None else float("inf")

        def make_key(*args, **kwargs):
            key = str(hash((args, *sorted(kwargs.items()))))
            if typed:
                key += str(hash(tuple(type(arg) for arg in args)))
            return key

        return CacheUtils.memoize(
            maxsize=maxsize, ttl=seconds, key_maker=make_key
        )

    @staticmethod
    def create_cache(
        name: str,
        maxsize: int = 128,
        ttl: Optional[TimeDelta] = None,
        cleanup_interval: Optional[TimeDelta] = None,
    ) -> Cache:
        """Create a new cache instance."""
        return Cache(
            maxsize=maxsize, ttl=ttl, cleanup_interval=cleanup_interval
        )
