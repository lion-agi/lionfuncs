"""Tests for async utilities."""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, Mock

from lionfuncs.utils.async_utils import AsyncUtils


@pytest.mark.asyncio
class TestAsyncUtils:
    """Test suite for AsyncUtils."""

    async def test_throttle_basic(self):
        """Test basic throttling functionality."""
        calls = 0

        @AsyncUtils.throttle(rate_limit=10)
        async def test_func():
            nonlocal calls
            calls += 1

        tasks = [test_func() for _ in range(5)]
        await asyncio.gather(*tasks)
        assert calls == 5

        """Test throttle respects rate limit."""
        start_time = time.time()
        calls = []

        @AsyncUtils.throttle(rate_limit=2)  # 2 calls per second
        async def test_func():
            calls.append(time.time())
            await asyncio.sleep(0.01)  # Small work simulation
            return len(calls)

        # Make 4 calls - should take ~2 seconds at 2 calls/sec
        results = await asyncio.gather(*[test_func() for _ in range(4)])

        # Verify timing
        duration = calls[-1] - start_time
        assert duration >= 1.5, f"Duration {duration} < 1.5s"

        # Verify call spacing
        intervals = [calls[i] - calls[i - 1] for i in range(1, len(calls))]
        avg_interval = sum(intervals) / len(intervals)
        assert avg_interval >= 0.45, f"Average interval {avg_interval} < 0.45s"

    async def test_batch_process_basic(self):
        """Test basic batch processing."""
        items = list(range(10))

        async def processor(x):
            await asyncio.sleep(0.01)  # Simulate work
            return x * 2

        results = await AsyncUtils.batch_process(
            items, processor, batch_size=3
        )
        assert results == [x * 2 for x in items]

    async def test_batch_process_callbacks(self):
        """Test batch completion callbacks."""
        items = list(range(6))
        completed_batches = []

        async def processor(x):
            await asyncio.sleep(0.01)
            return x * 2

        def on_complete(batch_results):
            completed_batches.append(batch_results)

        await AsyncUtils.batch_process(
            items, processor, batch_size=2, on_batch_complete=on_complete
        )

        assert len(completed_batches) == 3
        assert all(len(batch) == 2 for batch in completed_batches[:-1])

    async def test_batch_process_exceptions(self):
        """Test batch processing with exceptions."""
        items = list(range(5))

        async def failing_processor(x):
            if x % 2 == 0:
                raise ValueError(f"Failed on {x}")
            return x

        results = await AsyncUtils.batch_process(
            items, failing_processor, return_exceptions=True
        )

        assert len(results) == 5
        assert all(
            isinstance(r, ValueError) if i % 2 == 0 else r == i
            for i, r in enumerate(results)
        )

    async def test_timeout_context(self):
        """Test timeout context manager."""
        cleanup_called = False

        async def cleanup():
            nonlocal cleanup_called
            cleanup_called = True

        with pytest.raises(asyncio.TimeoutError):
            async with AsyncUtils.timeout_context(0.1, cleanup):
                await asyncio.sleep(1.0)

        assert cleanup_called

    async def test_retry_success(self):
        """Test successful retry."""
        mock_func = AsyncMock(side_effect=[ValueError, ValueError, "success"])

        result = await AsyncUtils.retry(mock_func, retries=2, delay=0.1)

        assert result == "success"
        assert mock_func.call_count == 3

    async def test_retry_failure(self):
        """Test retry exhaustion."""
        mock_func = AsyncMock(side_effect=ValueError("error"))

        with pytest.raises(ValueError):
            await AsyncUtils.retry(mock_func, retries=2, delay=0.1)

        assert mock_func.call_count == 3

    async def test_gather_with_concurrency(self):
        """Test concurrent task gathering."""
        running = 0
        max_running = 0
        results = []

        async def task(i):
            nonlocal running, max_running
            running += 1
            max_running = max(max_running, running)
            await asyncio.sleep(0.1)
            running -= 1
            results.append(i)
            return i

        tasks = [task(i) for i in range(10)]
        await AsyncUtils.gather_with_concurrency(3, *tasks)

        assert max_running <= 3
        assert len(results) == 10
        assert sorted(results) == list(range(10))

    def test_event_loop_context(self):
        """Test event loop context manager."""
        with AsyncUtils.event_loop() as loop:
            assert isinstance(loop, asyncio.AbstractEventLoop)
            assert not loop.is_running()
        assert loop.is_closed()

    def test_event_loop_new(self):
        """Test event loop creation."""
        with AsyncUtils.event_loop() as loop:
            assert isinstance(loop, asyncio.AbstractEventLoop)
            assert asyncio.get_event_loop() is loop

    async def test_throttle_invalid_params(self):
        """Test throttle with invalid parameters."""
        with pytest.raises(ValueError):

            @AsyncUtils.throttle(rate_limit=0)
            async def test_func():
                pass

        with pytest.raises(ValueError):

            @AsyncUtils.throttle(rate_limit=1, max_burst=0)
            async def test_func2():
                pass
