"""Tests for cache utilities."""

import threading
import time
from datetime import timedelta
from unittest.mock import patch

import pytest

from lionfuncs.utils.cache_utils import Cache, CacheUtils, CacheEntry


class TestCache:
    """Test suite for Cache class."""

    def test_basic_operations(self):
        """Test basic cache operations."""
        cache = Cache[str](maxsize=2)

        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Test default value
        assert cache.get("nonexistent") is None
        assert cache.get("nonexistent", "default") == "default"

        # Test delete
        cache.delete("key1")
        assert cache.get("key1") is None

        # Test clear
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.size == 0

    def test_maxsize(self):
        """Test cache size limits."""
        cache = Cache[int](maxsize=2)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # Should evict "a"

        assert cache.size == 2
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_ttl(self):
        """Test TTL functionality."""
        cache = Cache[str](ttl=0.1)  # 100ms TTL

        cache.set("key", "value")
        assert cache.get("key") == "value"

        time.sleep(0.2)  # Wait for expiration
        assert cache.get("key") is None

    def test_per_item_ttl(self):
        """Test per-item TTL override."""
        cache = Cache[str](ttl=10)  # 10s default TTL

        cache.set("long", "value1")  # Default TTL
        cache.set("short", "value2", ttl=0.1)  # 100ms TTL

        assert cache.get("long") == "value1"
        assert cache.get("short") == "value2"

        time.sleep(0.2)
        assert cache.get("long") == "value1"
        assert cache.get("short") is None

    def test_cleanup(self):
        """Test automatic cleanup."""
        cache = Cache[str](ttl=0.1, cleanup_interval=0.2)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.size == 2

        time.sleep(0.3)  # Wait for cleanup
        # Access triggers cleanup
        cache.get("key1")
        assert cache.size == 0

    def test_thread_safety(self):
        """Test thread-safe operations."""
        cache = Cache[int](maxsize=100)
        results = []

        def worker():
            for i in range(100):
                cache.set(f"key{i}", i)
                results.append(cache.get(f"key{i}"))

        threads = [threading.Thread(target=worker) for _ in range(4)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert None not in results
        assert cache.size <= 100


class TestCacheUtils:
    """Test suite for CacheUtils."""

    def test_memoize_basic(self):
        """Test basic memoization."""
        calls = 0

        @CacheUtils.memoize()
        def func(x, y):
            nonlocal calls
            calls += 1
            return x + y

        assert func(1, 2) == 3
        assert func(1, 2) == 3
        assert calls == 1

    def test_memoize_different_args(self):
        """Test memoization with different arguments."""
        calls = 0

        @CacheUtils.memoize()
        def func(x, y):
            nonlocal calls
            calls += 1
            return x + y

        assert func(1, 2) == 3
        assert func(2, 3) == 5
        assert calls == 2

    def test_memoize_ttl(self):
        """Test memoization with TTL."""
        calls = 0

        @CacheUtils.memoize(ttl=0.1)
        def func(x):
            nonlocal calls
            calls += 1
            return x * 2

        assert func(5) == 10
        assert func(5) == 10
        assert calls == 1

        time.sleep(0.2)
        assert func(5) == 10
        assert calls == 2

    def test_memoize_maxsize(self):
        """Test memoization size limit."""
        calls = 0

        @CacheUtils.memoize(maxsize=2)
        def func(x):
            nonlocal calls
            calls += 1
            return x * 2

        func(1)
        func(2)
        func(3)  # Should evict cache for func(1)
        func(1)  # Should call again

        assert calls == 4

    def test_memoize_key_maker(self):
        """Test custom cache key function."""
        calls = 0

        def make_key(x, y, **kwargs):
            return f"{x}:{y}:{sorted(kwargs.items())}"

        @CacheUtils.memoize(key_maker=make_key)
        def func(x, y, **kwargs):
            nonlocal calls
            calls += 1
            return x + y + sum(kwargs.values())

        assert func(1, 2, z=3) == 6
        assert func(1, 2, z=3) == 6
        assert calls == 1

    def test_timed_cache(self):
        """Test timed cache decorator."""
        calls = 0

        @CacheUtils.timed_cache(seconds=0.1, typed=True)
        def func(x):
            nonlocal calls
            calls += 1
            return x * 2

        # Test basic caching
        assert func(5) == 10
        assert func(5) == 10
        assert calls == 1

        # Test type differentiation
        assert func(5) == 10  # int
        assert func(5.0) == 10.0  # float
        assert calls == 2

        # Test expiration
        time.sleep(0.2)
        assert func(5) == 10
        assert calls == 3

    def test_cache_clear(self):
        """Test cache clearing through decorator."""
        calls = 0

        @CacheUtils.memoize()
        def func(x):
            nonlocal calls
            calls += 1
            return x * 2

        func(5)
        func(5)
        assert calls == 1

        func.cache_clear()
        func(5)
        assert calls == 2

    def test_cache_info(self):
        """Test cache info access."""

        @CacheUtils.memoize(maxsize=100)
        def func(x):
            return x * 2

        func(5)
        func(10)

        info = func.cache_info()
        assert info["size"] == 2
        assert info["maxsize"] == 100

    def test_error_handling(self):
        """Test error handling in cached functions."""

        @CacheUtils.memoize()
        def func(x):
            if x < 0:
                raise ValueError("Negative value")
            return x * 2

        # Test successful case
        assert func(5) == 10

        # Test error case
        with pytest.raises(ValueError):
            func(-1)

        # Ensure error wasn't cached
        with pytest.raises(ValueError):
            func(-1)

    def test_cache_creation(self):
        """Test cache instance creation."""
        cache = CacheUtils.create_cache(
            "test_cache", maxsize=100, ttl=3600, cleanup_interval=300
        )

        assert isinstance(cache, Cache)
        assert cache.maxsize == 100
        assert cache.ttl == 3600
        assert cache.cleanup_interval == 300

    def test_access_tracking(self):
        """Test access tracking metadata."""
        cache = Cache[str](ttl=1.0)  # 1 second TTL

        # Set value and verify access tracking
        cache.set("key", "value")
        first_access = cache.get("key")
        time.sleep(0.1)
        second_access = cache.get("key")

        entry = cache._cache["key"]
        assert entry.access_count == 2
        # Verify last_accessed is after creation (expires_at - TTL)
        assert entry.last_accessed > (entry.expires_at - 1.0)

    def test_concurrent_memoization(self):
        """Test memoization under concurrent access."""
        calls = 0
        lock = threading.Lock()

        @CacheUtils.memoize()
        def slow_func(x):
            nonlocal calls
            # Thread-safe increment
            with lock:
                calls += 1
            time.sleep(0.1)  # Simulate slow operation
            return x * 2

        # Run concurrent access
        threads = [
            threading.Thread(target=lambda: slow_func(5)) for _ in range(4)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert calls == 1  # Should only compute once

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test negative values
        with pytest.raises(ValueError):
            Cache[str](maxsize=-1)

        with pytest.raises(ValueError):
            Cache[str](ttl=-1)

        with pytest.raises(ValueError):
            Cache[str](cleanup_interval=-1)

        # Test zero cases
        cache = Cache[str](ttl=0)
        cache.set("key", "value")
        assert cache.get("key") is None

        cache = Cache[str](maxsize=0)
        cache.set("key", "value")
        assert cache.get("key") is None
