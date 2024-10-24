# Path Utilities Documentation

## Overview

The `PathUtils` module provides comprehensive path manipulation utilities with emphasis on security, cross-platform compatibility, and robust error handling.

## Core Features

### Path Operations
```python
from lionfuncs.utils import PathUtils

# Ensure path exists
path = PathUtils.ensure_path("data/output.txt", create=True)

# Get unique path
unique = PathUtils.get_unique_path("output", suffix=".txt")

# Scan directory
for file in PathUtils.scan_directory("data", pattern="*.txt"):
    process_file(file)
```

### File Management
```python
# Move file safely
PathUtils.move_path("source.txt", "dest.txt")

# Copy with verification
PathUtils.copy_path("source.txt", "backup.txt")

# Remove with safety checks
PathUtils.remove_path("old.txt")
```

### Path Information
```python
# Get path info
info = PathUtils.get_path_info("data.txt")
print(f"Size: {info.size}, Modified: {info.modified}")

# Calculate directory size
total_size, file_count = PathUtils.get_tree_size("data")
```

## Best Practices

### 1. Path Safety
```python
# Validate paths
if PathValidator.is_safe_path(user_input):
    process_path(user_input)

# Normalize paths
safe_path = PathValidator.normalize_path(path)
```

### 2. Cross-Platform
```python
# Use platform-independent paths
path = PathUtils.ensure_path("data/file.txt")

# Handle path separators
relative = PathUtils.make_path_relative(path)
```

### 3. Error Handling
```python
try:
    PathUtils.move_path(src, dst)
except IOError as e:
    handle_error(e)
```

## Common Patterns

### Safe File Processing
```python
def safe_process_file(path):
    # Validate path
    if not PathValidator.is_safe_path(path):
        raise ValueError("Invalid path")

    # Get unique output path
    output = PathUtils.get_unique_path(
        "output",
        suffix=".txt"
    )

    # Process safely
    try:
        with path.open() as f:
            data = process(f.read())

        PathUtils.atomic_write(output, data)
        return output
    except Exception as e:
        PathUtils.remove_path(output)
        raise
```

### Directory Scanning
```python
def scan_files(directory):
    """Scan directory with filtering."""
    paths = PathUtils.scan_directory(
        directory,
        pattern="*.txt",
        recursive=True
    )

    return PathUtils.filter_paths(
        paths,
        files_only=True,
        min_size=1024,  # 1KB
        exclude_patterns={"temp_*"}
    )
```

### Archive Management
```python
def archive_files(paths, archive_name):
    """Create and verify archive."""
    # Compress files
    archive = PathUtils.compress_paths(
        paths,
        archive_name,
        format='zip'
    )

    # Verify
    extract_dir = PathUtils.get_unique_path("verify")
    try:
        PathUtils.extract_archive(archive, extract_dir)
        # Verify contents
        return verify_contents(extract_dir, paths)
    finally:
        PathUtils.remove_path(extract_dir, recursive=True)
```

## Error Handling

### Common Errors
1. FileNotFoundError
2. PermissionError
3. IOError
4. ValueError for invalid paths

### Error Prevention
```python
def safe_operation(path):
    # Validate path
    if not PathValidator.is_safe_path(path):
        raise ValueError("Invalid path")

    # Check accessibility
    if not PathUtils.is_path_accessible(path, 'w'):
        raise PermissionError("Path not writable")

    # Perform operation
    try:
        perform_operation(path)
    except Exception as e:
        handle_error(e)
```

## Performance Considerations

### Optimization Tips
1. Use appropriate scanning patterns
2. Minimize path operations
3. Batch file operations
4. Cache path information

### Resource Management
1. Clean up temporary files
2. Handle large directories
3. Manage memory usage
4. Use context managers

## Security

### Best Practices
1. Validate all paths
2. Check permissions
3. Use absolute paths
4. Handle symbolic links
5. Prevent path traversal

### Secure Path Handling
```python
def secure_operation(user_path):
    # Normalize and validate
    path = PathValidator.normalize_path(user_path)
    if not PathValidator.is_safe_path(path):
        raise ValueError("Invalid path")

    # Check if path is under allowed directory
    if not PathUtils.is_subpath(path, ALLOWED_DIR):
        raise ValueError("Path not allowed")

# Perform operation
    return process_secure_operation(path)

## Testing

### Test Strategies
1. Test cross-platform behavior
2. Test error conditions
3. Test concurrent access
4. Test resource cleanup

### Example Tests
```python
def test_path_operations():
    # Create test directory
    path = PathUtils.ensure_path("test_dir")

    # Create test files
    test_file = path / "test.txt"
    PathUtils.atomic_write(test_file, "content")

    # Verify
    assert test_file.exists()
    assert PathUtils.get_path_info(test_file).size > 0

    # Cleanup
    PathUtils.remove_path(path, recursive=True)
```

## Cross-Platform Considerations

### Windows Specifics
1. Path length limitations
2. Reserved names (CON, PRN, etc.)
3. Drive letters
4. Backslash separators

### Unix Specifics
1. Case sensitivity
2. File permissions
3. Symbolic links
4. Forward slash separators

### Compatibility Code
```python
def cross_platform_path(path):
    """Handle path across platforms."""
    # Normalize separators
    path = PathValidator.normalize_path(path)

    # Handle long paths on Windows
    if os.name == 'nt' and len(str(path)) > 260:
        path = f"\\\\?\\{path}"

    return path
```

## Integration Patterns

### File System Operations
```python
class FileManager:
    def __init__(self, root_dir):
        self.root = PathUtils.ensure_path(root_dir)

    def safe_write(self, filename, content):
        """Safely write file in root directory."""
        path = self.root / filename
        if not PathUtils.is_subpath(path, self.root):
            raise ValueError("Path traversal detected")

        PathUtils.atomic_write(path, content)

    def list_files(self, pattern="*"):
        """List files with safety checks."""
        return PathUtils.filter_paths(
            PathUtils.scan_directory(self.root, pattern),
            files_only=True
        )
```

### Archive Management
```python
class ArchiveManager:
    def __init__(self, archive_dir):
        self.archive_dir = PathUtils.ensure_path(archive_dir)

    def create_archive(self, files, name):
        """Create verified archive."""
        archive_path = PathUtils.get_unique_path(
            self.archive_dir / name,
            suffix=".zip"
        )

        return PathUtils.compress_paths(
            files,
            archive_path,
            format='zip'
        )

    def extract_safe(self, archive, extract_dir):
        """Safely extract archive."""
        # Verify archive path
        if not PathValidator.is_safe_path(archive):
            raise ValueError("Invalid archive path")

        # Create safe extraction directory
        extract_path = PathUtils.ensure_path(extract_dir)

        return PathUtils.extract_archive(archive, extract_path)
```

## Advanced Usage

### Watching File System Changes
```python
async def watch_directory(path):
    """Watch directory for changes."""
    async for event, path in PathUtils.watch_path(path):
        if event == 'created':
            handle_new_file(path)
        elif event == 'modified':
            handle_modified_file(path)
        elif event == 'deleted':
            handle_deleted_file(path)
```

### Finding Duplicate Files
```python
def cleanup_duplicates(directory):
    """Find and handle duplicate files."""
    duplicates = PathUtils.find_duplicates(directory)

    for group in duplicates:
        # Keep first file, remove others
        original, *copies = group
        for copy in copies:
            PathUtils.remove_path(copy)
```

## Resources
- Python pathlib documentation
- File system security guidelines
- Cross-platform path handling
- Performance optimization tips

## Next Steps

### Learning More
1. Study platform-specific path handling
2. Review security best practices
3. Learn about file system limitations
4. Understand performance implications

### Getting Help
1. Check documentation examples
2. Review test cases
3. Consult platform guides
4. Seek community support
