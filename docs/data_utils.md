# Data Structure Utilities Documentation

## Overview

The `DataUtils` module provides robust utilities for manipulating nested data structures in Python. It includes functionality for deep access, updates, and flattening/unflattening of nested dictionaries and lists.

## Key Features

### Deep Get/Set Operations
```python
from lionfuncs.utils import DataUtils

# Deep get with dot notation
data = {"user": {"profile": {"name": "Alice"}}}
name = DataUtils.deep_get(data, "user.profile.name")  # Returns "Alice"

# Deep set with automatic path creation
DataUtils.deep_set(data, "user.settings.theme", "dark")
```

### Deep Update
```python
base = {"settings": {"theme": "light", "font": "Arial"}}
update = {"settings": {"theme": "dark"}}

# Update while preserving existing values
result = DataUtils.deep_update(base, update)
# Result: {"settings": {"theme": "dark", "font": "Arial"}}
```

### Flatten/Unflatten
```python
# Flatten nested structure
nested = {
    "user": {
        "profile": {"name": "Alice"},
        "settings": ["dark", "compact"]
    }
}

flat = DataUtils.flatten(nested)
# Result: {
#     "user.profile.name": "Alice",
#     "user.settings.0": "dark",
#     "user.settings.1": "compact"
# }

# Unflatten back to nested structure
restored = DataUtils.unflatten(flat)
```

## Best Practices

### 1. Path Handling
- Use dot notation for paths: `"parent.child.key"`
- Handle missing paths with defaults: `deep_get(data, "path", default=None)`
- Use `create_missing=True` with `deep_set` for automatic path creation

### 2. Type Safety
- Consider type implications when flattening/unflattening
- Handle mixed structures (dicts and lists) appropriately
- Use type hints for better code safety

### 3. Performance
- Consider using `max_depth` for large structures
- Cache flattened results if used frequently
- Be mindful of memory usage with large structures

## Advanced Usage

### Custom Separators
```python
# Use custom separator for flattened keys
flat = DataUtils.flatten(data, separator="/")
# Result: {"user/profile/name": "Alice"}
```

### List Handling
```python
# Merging lists during updates
DataUtils.deep_update(
    base,
    update,
    merge_lists=True  # Concatenate lists instead of replacing
)
```

### Depth Control
```python
# Limit flattening depth
flat = DataUtils.flatten(data, max_depth=2)
```

## Error Handling

### Common Errors
1. `ValueError`: Empty or invalid paths
2. `TypeError`: Type conflicts during traversal
3. `IndexError`: Invalid list indices
4. `KeyError`: Missing dictionary keys

### Error Prevention
```python
# Safe deep get
value = DataUtils.deep_get(data, "risky.path", default="fallback")

# Safe deep set
try:
    DataUtils.deep_set(data, "path", value, create_missing=True)
except (ValueError, TypeError) as e:
    handle_error(e)
```

## Performance Considerations

### Optimization Tips
1. Minimize deep operations on large structures
2. Use appropriate data structures (dict vs list)
3. Consider caching for frequently accessed paths
4. Use `max_depth` for partial flattening

### Memory Usage
1. Be careful with large nested structures
2. Monitor memory when flattening deep structures
3. Clean up temporary structures

## Integration Patterns

### Configuration Management
```python
class Config:
    def __init__(self, data: dict):
        self._data = data

    def get(self, path: str, default: Any = None) -> Any:
        return DataUtils.deep_get(self._data, path, default)

    def set(self, path: str, value: Any) -> None:
        DataUtils.deep_set(self._data, path, value)
```

### Data Transformation
```python
def transform_data(data: dict) -> dict:
    # Flatten for processing
    flat = DataUtils.flatten(data)

    # Process flat structure
    processed = {k: process_value(v) for k, v in flat.items()}

    # Restore structure
    return DataUtils.unflatten(processed)
```

### Data Migration
```python
def migrate_data(old_data: dict, new_schema: dict) -> dict:
    # Flatten old data
    flat_data = DataUtils.flatten(old_data)

    # Map to new schema
    migrated = {}
    for old_path, new_path in new_schema.items():
        if old_path in flat_data:
            DataUtils.deep_set(
                migrated,
                new_path,
                flat_data[old_path]
            )

    return migrated
```

## Testing Strategies

### Unit Testing
1. Test basic operations
2. Test edge cases
3. Test error conditions
4. Test large structures
5. Test performance

### Integration Testing
1. Test with real data structures
2. Test with other modules
3. Test in typical use cases

## Additional Resources
- Type hints documentation
- Python data structures guide
- Performance optimization tips
