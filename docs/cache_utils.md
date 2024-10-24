# Cache Utilities Documentation

The cache utilities module provides a robust, thread-safe caching system with features like TTL (Time-To-Live), size limits, and automatic cleanup.

## Core Features

### Basic Cache

The `Cache` class provides the core caching functionality:

```python
from lionfuncs.utils import Cache

# Create cache instance
cache = Cache[str](maxsize=100, ttl=3600)  # 1 hour TTL

# Basic operations
cache.set("key", "value")
value = cache.get("key")
cache.delete("key")
cache.clear()
```

### Memoization

The `@memoize` decorator provides function result caching:

```python
from lionfuncs.utils import CacheUtils

@CacheUtils.memoize(ttl=3600, maxsize=100)
def expensive_function(x, y):
    # Expensive computation
    return result
```

### Timed Cache

The `@timed_cache` decorator provides simpler time-based caching:

```python
@CacheUtils.timed_cache(seconds=60)
def get_data():
    # Fetch data
    return data
```

## Configuration

### Cache Parameters

- `maxsize`: Maximum number of entries (default: 128)
- `ttl`: Time-to-live in seconds (default: None)
- `cleanup_interval`: Automatic cleanup interval (default: None)

### Memoization Parameters

- `maxsize`: Maximum cache size
- `ttl`: Cache TTL in seconds
- `key_maker`: Custom cache key function

## Advanced Usage

### Type-Safe Caching

The Cache class is generic and supports type hints:

```python
cache = Cache[int](maxsize=100)  # Only integers
cache.set("key", 42)  # OK
cache.set("key", "value")  # Type error
```

### Custom Cache Keys

```python
def make_key(*args, **kwargs):
    return f"{args}:{sorted(kwargs.items())}"

@CacheUtils.memoize(key_maker=make_key)
def function(x, y, **kwargs):
    return result
```

### Cache Management

```python
@CacheUtils.memoize()
def function(x):
    return x * 2

# Clear cache
function.cache_clear()

# Get cache info
info = function.cache_info()
print(f"Cache size: {info['size']}")
```

## Best Practices

### 1. Cache Size Management

- Set appropriate `maxsize` based on memory constraints
- Monitor cache size using `cache_info()`
- Use cleanup intervals for automatic maintenance

```python
cache = Cache[str](
    maxsize=1000,
    cleanup_interval=300  # 5 minute cleanup
)
```

### 2. TTL Strategy

- Use TTL for time-sensitive data
- Set per-item TTL for varying freshness requirements
- Consider cleanup_interval for automatic expiration

```python
# Default TTL
cache = Cache[str](ttl=3600)  # 1 hour

# Per-item TTL
cache.set("quick", value, ttl=60)  # 1 minute
cache.set("slow", value, ttl=86400)  # 1 day
```

### 3. Thread Safety

All cache operations are thread-safe by default:

```python
# Safe for concurrent access
cache = Cache[str]()

def worker():
    cache.set(key, value)
    return cache.get(key)

# Create multiple threads
threads = [Thread(target=worker) for _ in range(10)]
```

### 4. Error Handling

```python
try:
    value = cache.get("key")
    if value is None:
        value = compute_value()
        cache.set("key", value)
except Exception as e:
    logger.error(f"Cache error: {e}")
```

## Performance Considerations

### 1. Cache Size

- Larger cache sizes increase memory usage
- Smaller sizes may increase cache misses
- Monitor hit/miss ratios

### 2. TTL Values

- Shorter TTLs increase freshness
- Longer TTLs improve cache hits
- Balance based on data volatility

### 3. Cleanup Interval

- Shorter intervals reduce memory usage
- Longer intervals improve performance
- Default: cleanup on access

## Common Patterns

### 1. Computed Values Cache

```python
@CacheUtils.memoize(ttl=3600)
def compute_expensive_value(x):
    # Expensive computation
    return result
```

### 2. API Response Cache

```python
@CacheUtils.memoize(ttl=300)  # 5 minutes
async def fetch_api_data(endpoint):
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint) as response:
            return await response.json()
```

### 3. Multi-Level Cache

```python
local_cache = Cache[str](maxsize=100, ttl=60)  # 1 minute
shared_cache = Cache[str](maxsize=1000, ttl=3600)  # 1 hour

def get_value(key):
    # Try local cache
    value = local_cache.get(key)
    if value is not None:
        return value

    # Try shared cache
    value = shared_cache.get(key)
    if value is not None:
        local_cache.set(key, value)
        return value

    # Compute value
    value = compute_value(key)
    shared_cache.set(key, value)
    local_cache.set(key, value)
    return value
```

## Error Cases

Handle common error scenarios:

1. Cache full
2. TTL expired
3. Invalid keys
4. Serialization errors
5. Concurrent modifications

## Memory Management

Tips for managing memory usage:

1. Set appropriate maxsize
2. Use TTL for all entries
3. Run regular cleanup
4. Monitor cache size
5. Clear unused entries

## Monitoring

Key metrics to track:

1. Cache size
2. Hit/miss ratio
3. Eviction rate
4. Average TTL
5. Cleanup frequency

## Debugging Tips

1. Enable verbose logging
2. Monitor memory usage
3. Track cache statistics
4. Check thread contention
5. Validate TTL behavior
