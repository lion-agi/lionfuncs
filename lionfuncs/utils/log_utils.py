"""Logging utilities.

This module provides comprehensive logging utilities with support for structured
logging, log rotation, log aggregation, and contextual logging.
"""

import inspect
import json
import logging
import logging.handlers
import os
import sys
import threading
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Callable,
    ContextManager,
    Dict,
    Generator,
    Optional,
    TypeVar,
    Union,
    cast,
)

from .base import UtilityGroup, PathLike
from .exceptions import IOError

T = TypeVar("T")


@dataclass
class LogContext:
    """Thread-safe logging context."""

    data: Dict[str, Any] = field(default_factory=dict)
    _local: threading.local = field(default_factory=threading.local)

    def get(self) -> Dict[str, Any]:
        """Get current context data."""
        if not hasattr(self._local, "stack"):
            self._local.stack = [self.data.copy()]
        return self._local.stack[-1]

    def push(self, data: Dict[str, Any]) -> None:
        """Push new context data."""
        if not hasattr(self._local, "stack"):
            self._local.stack = [self.data.copy()]
        current = self._local.stack[-1].copy()
        current.update(data)
        self._local.stack.append(current)

    def pop(self) -> None:
        """Pop context data."""
        if hasattr(self._local, "stack"):
            if len(self._local.stack) > 1:
                self._local.stack.pop()


class StructuredLogRecord(logging.LogRecord):
    """Enhanced log record with structured data support."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.context_data: Dict[str, Any] = {}
        self.structured_data: Dict[str, Any] = {}


class StructuredLogger(logging.Logger):
    """Logger with structured logging support."""

    def makeRecord(
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: Any,
        args: Any,
        exc_info: Any,
        func: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        sinfo: Optional[str] = None,
    ) -> StructuredLogRecord:
        """Create a LogRecord with structured data support."""
        record = StructuredLogRecord(
            name, level, fn, lno, msg, args, exc_info, func, sinfo
        )
        if extra:
            for key, value in extra.items():
                setattr(record, key, value)
        return record


class JsonFormatter(logging.Formatter):
    """JSON log formatter with context support."""

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = "%",
        validate: bool = True,
        defaults: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(fmt, datefmt, style, validate, defaults)

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        record = cast(StructuredLogRecord, record)
        data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context data
        if hasattr(record, "context_data"):
            data["context"] = record.context_data

        # Add structured data
        if hasattr(record, "structured_data"):
            data["data"] = record.structured_data

        # Add exception info
        if record.exc_info:
            data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "stack_trace": self.formatException(record.exc_info),
            }

        return json.dumps(data)


class LogUtils(UtilityGroup):
    """Logging utility functions."""

    _context = LogContext()

    @classmethod
    def get_name(cls) -> str:
        return "log_utils"

    @classmethod
    def setup_logging(
        cls,
        level: Union[str, int] = logging.INFO,
        log_file: Optional[PathLike] = None,
        format_string: Optional[str] = None,
        json_format: bool = False,
        rotation_size: int = 10_000_000,  # 10MB
        backup_count: int = 5,
        capture_warnings: bool = True,
        propagate: bool = True,
    ) -> logging.Logger:
        """Setup logging configuration.

        Args:
            level: Logging level
            log_file: Optional log file path
            format_string: Log format string
            json_format: Use JSON formatter
            rotation_size: Max size for log rotation
            backup_count: Number of backup logs to keep
            capture_warnings: Capture Python warnings
            propagate: Propagate logs to parent handlers

        Returns:
            Configured logger

        Example:
            >>> logger = LogUtils.setup_logging(
            ...     level="INFO",
            ...     log_file="app.log",
            ...     json_format=True
            ... )
        """
        # Register custom logger class
        logging.setLoggerClass(StructuredLogger)

        # Get or create logger
        logger = logging.getLogger()
        logger.setLevel(
            level
            if isinstance(level, int)
            else getattr(logging, level.upper())
        )
        logger.propagate = propagate

        # Clear existing handlers
        logger.handlers.clear()

        # Create formatter
        if json_format:
            formatter = JsonFormatter()
        else:
            format_string = format_string or (
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            formatter = logging.Formatter(format_string)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler with rotation
        if log_file:
            try:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)

                file_handler = logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=rotation_size, backupCount=backup_count
                )
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.error(f"Failed to setup file logging: {e}")

        # Capture warnings
        if capture_warnings:
            logging.captureWarnings(True)

        return logger

    @classmethod
    @contextmanager
    def log_context(cls, **kwargs: Any) -> Generator[None, None, None]:
        """Context manager for temporary logging context.

        Args:
            **kwargs: Context variables to add to logs

        Example:
            >>> with LogUtils.log_context(user_id="123"):
            ...     logger.info("Processing user data")  # Includes user_id
        """
        cls._context.push(kwargs)
        try:
            yield
        finally:
            cls._context.pop()

    @classmethod
    def get_context(cls) -> Dict[str, Any]:
        """Get current logging context."""
        return cls._context.get()

    @classmethod
    def log_call(
        cls,
        logger: Optional[logging.Logger] = None,
        level: int = logging.DEBUG,
        log_args: bool = True,
        log_result: bool = True,
        log_time: bool = True,
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Decorator to log function calls.

        Args:
            logger: Logger to use
            level: Logging level
            log_args: Log function arguments
            log_result: Log function result
            log_time: Log execution time

        Example:
            >>> @LogUtils.log_call(level=logging.INFO)
            ... def process_data(data):
            ...     return data * 2
        """

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            nonlocal logger
            # Get logger from module if not provided
            if logger is None:
                logger = logging.getLogger(func.__module__)

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                func_name = func.__name__
                start_time = datetime.now()

                # Build call context
                context = {
                    "function": func_name,
                    "module": func.__module__,
                }
                if log_args:
                    context["args"] = str(args)
                    context["kwargs"] = str(kwargs)

                with cls.log_context(**context):
                    try:
                        result = func(*args, **kwargs)
                        duration = datetime.now() - start_time

                        # Log success
                        if log_time:
                            context["duration"] = str(duration)
                        if log_result:
                            context["result"] = str(result)

                        logger.log(
                            level,
                            f"{func_name} completed successfully",
                            extra={"structured_data": context},
                        )
                        return result
                    except Exception as e:
                        # Log error
                        context["error"] = str(e)
                        context["stack_trace"] = traceback.format_exc()
                        logger.exception(
                            f"Error in {func_name}",
                            extra={"structured_data": context},
                        )
                        raise

            return wrapper

        return decorator

    @staticmethod
    def capture_output(
        logger: logging.Logger, level: int = logging.INFO
    ) -> ContextManager[None]:
        """Capture stdout/stderr and redirect to logger.

        Args:
            logger: Logger to use
            level: Logging level for captured output
        """

        class LoggerWriter:
            def __init__(self, logger: logging.Logger, level: int):
                self.logger = logger
                self.level = level
                self.buffer = []

            def write(self, msg: str) -> None:
                if msg.strip():
                    self.buffer.append(msg)
                    if msg.endswith("\n"):
                        self.flush()

            def flush(self) -> None:
                if self.buffer:
                    message = "".join(self.buffer).strip()
                    if message:
                        self.logger.log(self.level, message)
                    self.buffer.clear()

        @contextmanager
        def _capture() -> Generator[None, None, None]:
            stdout_writer = LoggerWriter(logger, level)
            stderr_writer = LoggerWriter(logger, logging.ERROR)

            old_stdout = sys.stdout
            old_stderr = sys.stderr

            try:
                sys.stdout = stdout_writer  # type: ignore
                sys.stderr = stderr_writer  # type: ignore
                yield
            finally:
                stdout_writer.flush()
                stderr_writer.flush()
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        return _capture()

    @staticmethod
    def stack_trace(skip_frames: int = 0) -> str:
        """Get formatted stack trace.

        Args:
            skip_frames: Number of frames to skip from top

        Returns:
            Formatted stack trace string
        """
        stack = inspect.stack()[1 + skip_frames :]
        formatted = []

        for frame_info in stack:
            formatted.append(
                f"{frame_info.filename}:{frame_info.lineno} "
                f"in {frame_info.function}"
            )

        return "\n".join(formatted)

    @classmethod
    def exception_handler(
        cls,
        logger: logging.Logger,
        reraise: bool = True,
        level: int = logging.ERROR,
        **context: Any,
    ) -> Callable[[T], T]:
        """Decorator for exception handling and logging.

        Args:
            logger: Logger to use
            reraise: Whether to re-raise caught exceptions
            level: Logging level for errors
            **context: Additional context data

        Example:
            >>> @LogUtils.exception_handler(logger)
            ... def risky_operation():
            ...     raise ValueError("Something went wrong")
        """

        def decorator(func: T) -> T:
            if not callable(func):
                raise TypeError("Decorator must be applied to callable")

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    log_context = {
                        "function": func.__name__,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        **context,
                    }

                    with cls.log_context(**log_context):
                        logger.log(
                            level,
                            f"Error in {func.__name__}: {e}",
                            exc_info=True,
                        )

                    if reraise:
                        raise

            return cast(T, wrapper)

        return decorator
