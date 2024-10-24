# Async Utilities Documentation

The `AsyncUtils` class provides a collection of utilities for handling asynchronous operations in Python. These utilities help manage common async patterns like rate limiting, batch processing, retries, and concurrency control.

## Core Features

### Rate Limiting

The `throttle` decorator implements rate limiting for async functions:

```python
from lionfuncs.utils import AsyncUtils

@AsyncUtils.throttle(rate_limit=10)  # 10 calls per second
async def api_call():
    # ... make API call
```

Parameters:
- `rate_limit`: Maximum calls per second
- `max_burst`: Maximum number of concurrent calls allowed

### Batch Processing

Process sequences of items in batches with concurrency control:

```python
items = list(range(100))

async def process_item(x):
    return x * 2

results = await AsyncUtils.batch_process(
    items,
    process_item,
    batch_size=10,
    max_concurrent=5
)
```

Parameters:
- `items`: Sequence of items to process
- `processor`: Async function to process each item
- `batch_size`: Number of items per batch
- `max_concurrent`: Maximum concurrent batches
- `on_batch_complete`: Optional callback for batch completion
- `retry_count`: Number of retries for failed items
- `retry_delay`: Delay between retries

### Retry Logic

Retry async functions with exponential backoff:

```python
async def flaky_operation():
    # ... may fail

result = await AsyncUtils.retry(
    flaky_operation,
    retries=3,
    delay=1.0,
    backoff_factor=2.0
)
```

Parameters:
- `func`: Function to retry
- `retries`: Maximum retry attempts
- `delay`: Initial delay between retries
- `backoff_factor`: Factor to increase delay
- `exceptions`: Tuple of exceptions to catch

### Timeout Management

Context manager for operations with timeout:

```python
async with AsyncUtils.timeout_context(5.0, cleanup=cleanup_func):
    await long_running_operation()
```

Parameters:
- `timeout`: Timeout in seconds
- `cleanup`: Optional cleanup function

### Concurrency Control

Run tasks with concurrency limits:

```python
tasks = [create_task(i) for i in range(100)]
results = await AsyncUtils.gather_with_concurrency(10, *tasks)
```

Parameters:
- `n`: Maximum concurrent tasks
- `tasks`: Tasks to run
- `return_exceptions`: Whether to return exceptions

### Event Loop Management

Context manager for event loop handling:

```python
with AsyncUtils.event_loop() as loop:
    loop.run_until_complete(async_function())
```

## Best Practices

1. Rate Limiting:
   - Set appropriate rate limits based on resource constraints
   - Use max_burst to prevent overwhelming resources

2. Batch Processing:
   - Choose batch_size based on memory constraints
   - Set max_concurrent based on available CPU/IO capacity

3. Retries:
   - Use exponential backoff for external services
   - Set appropriate timeout values

4. Error Handling:
   - Always handle exceptions in async code
   - Use cleanup functions with timeout contexts

## Common Patterns

### API Rate Limiting

```python
@AsyncUtils.throttle(rate_limit=2)  # 2 calls per second
async def api_call(endpoint):
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint) as response:
            return await response.json()

# Multiple calls will be rate-limited
results = await asyncio.gather(*[api_call(endpoint) for _ in range(10)])
```

### Batch Data Processing

```python
async def process_data(items):
    async def process_item(item):
        # Process single item
        return transformed_item

    return await AsyncUtils.batch_process(
        items,
        process_item,
        batch_size=100,
        max_concurrent=5,
        retry_count=3
    )
```

### Resilient Operations

```python
async def resilient_operation():
    async with AsyncUtils.timeout_context(10.0, cleanup=cleanup_resources):
        result = await AsyncUtils.retry(
            operation,
            retries=3,
            delay=1.0,
            backoff_factor=2.0
        )
    return result
```

## Performance Considerations

1. Batch Size:
   - Larger batches reduce overhead but increase memory usage
   - Consider available memory when setting batch_size

2. Concurrency:
   - Too many concurrent operations can overwhelm resources
   - Monitor system resources to find optimal concurrency levels

3. Rate Limiting:
   - Set rate limits based on actual resource capabilities
   - Consider burst patterns in workload

4. Timeouts:
   - Set timeouts based on expected operation duration
   - Include buffer for network/system variations

## Error Handling

1. Always handle exceptions in async code
2. Use cleanup functions with timeout contexts
3. Set appropriate retry policies
4. Monitor and log errors

## Resource Management

1. Use context managers for cleanup
2. Implement proper error recovery
3. Monitor resource usage
4. Clean up resources in error cases

## Debugging Tips

1. Enable debug logging
2. Monitor task execution times
3. Track resource usage
4. Use asyncio debug mode

## Additional Resources

- [asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [Python async patterns](https://docs.python.org/3/library/asyncio-task.html)
