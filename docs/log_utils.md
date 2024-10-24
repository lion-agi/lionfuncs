# Logging Utilities Documentation

## Overview

The `LogUtils` module provides comprehensive logging functionality with support for structured logging, contextual logging, log rotation, and various debugging utilities.

## Core Features

### Basic Logging Setup
```python
from lionfuncs.utils import LogUtils

# Setup basic logging
logger = LogUtils.setup_logging(
    level="INFO",
    log_file="app.log",
    json_format=True
)

# Basic logging
logger.info("Application started")
logger.error("An error occurred", exc_info=True)
```

### Contextual Logging
```python
# Add context to logs
with LogUtils.log_context(user_id="123", action="login"):
    logger.info("User logged in")

    # Nested context
    with LogUtils.log_context(session="abc"):
        logger.info("Session created")
```

### Structured Logging
```python
# Log structured data
logger.info(
    "Operation completed",
    extra={
        'structured_data': {
            'duration': 1.23,
            'status': 'success'
        }
    }
)
```

## Best Practices

### 1. Log Configuration
- Use appropriate log levels
- Configure log rotation
- Enable JSON formatting for parsing
- Set meaningful context

### 2. Error Handling
- Use exception_handler decorator
- Include stack traces
- Capture all relevant context
- Handle logging failures

### 3. Performance
- Use appropriate log levels
- Configure rotation sizes
- Handle high-volume logging
- Clean up resources

## Common Patterns

### Operation Logging
```python
@LogUtils.log_call(log_args=True, log_result=True)
def process_data(data: dict) -> dict:
    """Process data with full logging."""
    result = transform(data)
    return result
```

### Error Tracking
```python
@LogUtils.exception_handler(logger)
def risky_operation():
    """Operation with error tracking."""
    result = perform_risky_task()
    return result
```

### Output Capture
```python
def capture_output():
    """Capture stdout/stderr to logs."""
    with LogUtils.capture_output(logger):
        print("This goes to logs")
        subprocess.run(["some_command"])
```

## Error Handling

### Common Errors
1. FileNotFoundError for log files
2. PermissionError for log access
3. IOError for log operations
4. Thread context errors

### Error Prevention
```python
try:
    logger = LogUtils.setup_logging(log_file="app.log")
except Exception as e:
    # Fallback to console logging
    logger = LogUtils.setup_logging()
    logger.error(f"Failed to setup file logging: {e}")
```

## Performance Considerations

### Optimization Tips
1. Use appropriate log levels
2. Configure batch writing
3. Set rotation policies
4. Clean up old logs

### Resource Management
1. Monitor log file size
2. Configure retention policy
3. Handle disk space issues
4. Clean up resources

## Integration

### System Integration
```python
# Application logging
class App:
    def __init__(self):
        self.logger = LogUtils.setup_logging(
            log_file="app.log",
            json_format=True
        )

    def run(self):
        with LogUtils.log_context(app_id=self.id):
            self.logger.info("Application starting")
            try:
                self.process()
            except Exception:
                self.logger.exception("Application error")
```

### Service Integration
```python
class Service:
    def __init__(self, logger):
        self.logger = logger

    @LogUtils.log_call(log_args=True)
    def handle_request(self, request):
        with LogUtils.log_context(
            request_id=request.id,
            user=request.user
        ):
            return self.process_request(request)
```

## Testing

### Test Strategies
1. Verify log content
2. Test log rotation
3. Verify context handling
4. Test error scenarios

### Example Tests
```python
def test_logging():
    with tempfile.NamedTemporaryFile() as tmp:
        logger = LogUtils.setup_logging(
            log_file=tmp.name,
            json_format=True
        )

        logger.info("Test message")

        log_content = Path(tmp.name).read_text()
        assert "Test message" in log_content
```

## Additional Resources
- Python logging documentation
- JSON logging best practices
- Log rotation strategies
- Monitoring guidelines
