# I/O Utilities Documentation

## Overview

The `IOUtils` module provides a robust set of utilities for file system operations with emphasis on safety, atomicity, and proper resource management.

## Core Features

### Atomic File Operations
```python
from lionfuncs.utils import IOUtils

# Atomic write
with IOUtils.atomic_write("data.txt") as f:
    f.write("content")

# Safe read/write
content = IOUtils.safe_read("input.txt")
IOUtils.safe_write("output.txt", content, atomic=True)
```

### JSON Operations
```python
# Write JSON
data = {"key": "value"}
IOUtils.write_json("config.json", data, indent=2)

# Read JSON
config = IOUtils.read_json("config.json")
```

### Chunked Reading
```python
# Read large file in chunks
for chunk in IOUtils.chunk_reader("large.txt", chunk_size=8192):
    process_chunk(chunk)
```

## Best Practices

### 1. File Safety
- Use atomic operations for critical writes
- Always handle exceptions
- Use proper encoding parameters
- Clean up resources properly

### 2. Performance
- Use chunked reading for large files
- Buffer writes appropriately
- Consider memory constraints
- Monitor file sizes

### 3. Error Handling
- Check file existence
- Handle permission errors
- Validate paths
- Clean up on errors

## Common Patterns

### Safe File Updates
```python
def safe_update(file_path, updater):
    # Read current content
    try:
        content = IOUtils.safe_read(file_path)
    except IOError:
        content = ""

    # Update content
    new_content = updater(content)

    # Write atomically
    IOUtils.safe_write(file_path, new_content, atomic=True)
```

### Configuration Management
```python
class Config:
    def __init__(self, path):
        self.path = path

    def load(self):
        try:
            return IOUtils.read_json(self.path)
        except IOError:
            return {}

    def save(self, data):
        IOUtils.write_json(self.path, data, atomic=True)
```

### File Processing Pipeline
```python
def process_files(directory):
    for file_path in IOUtils.scan_dir(directory, pattern="*.txt"):
        info = IOUtils.get_file_info(file_path)
        if info.size > 0:
            with IOUtils.chunk_reader(file_path) as chunks:
                for chunk in chunks:
                    process_chunk(chunk)
```

## Error Handling

### Common Errors
1. FileNotFoundError
2. PermissionError
3. IOError
4. OSError

### Error Prevention
```python
try:
    content = IOUtils.safe_read("file.txt")
except IOError as e:
    handle_error(e)
```

## Performance Considerations

### Optimization Tips
1. Use appropriate chunk sizes
2. Buffer large writes
3. Avoid unnecessary reads
4. Clean up resources promptly

### Memory Management
1. Use chunked reading
2. Monitor file sizes
3. Clean up temporary files
4. Use context managers

## Security

### Best Practices
1. Validate file paths
2. Check permissions
3. Use secure file operations
4. Clean up sensitive data

### Secure File Handling
```python
def secure_write(path, content):
    # Validate path
    path = Path(path).resolve()
    if not path.parent.exists():
        raise IOError("Invalid path")

    # Write securely
    try:
        IOUtils.safe_write(path, content, atomic=True)
    finally:
        # Cleanup
        if isinstance(content, bytes):
            content = bytearray(len(content))
```

## Testing

### Test Strategies
1. Test file operations
2. Test error conditions
3. Test concurrent access
4. Test resource cleanup

### Example Tests
```python
def test_file_operations():
    # Create test file
    IOUtils.safe_write("test.txt", "content")

    # Verify content
    assert IOUtils.safe_read("test.txt") == "content"

    # Clean up
    IOUtils.remove_path("test.txt")
```

## Integration

### System Integration
1. Use consistent paths
2. Handle system differences
3. Manage resources properly
4. Monitor system state

### Error Recovery
1. Implement retries
2. Handle cleanup
3. Log errors
4. Maintain consistency

## Additional Resources
- Python pathlib documentation
- File system best practices
- IO performance optimization
- Security guidelines
