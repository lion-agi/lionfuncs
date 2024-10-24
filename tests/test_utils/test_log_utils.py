"""Tests for logging utilities."""

import io
import json
import logging
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
import pytest
from typing import Generator

from lionfuncs.utils.log_utils import LogUtils, StructuredLogger


class TestLogUtils:
    """Test suite for LogUtils."""

    @pytest.fixture
    def temp_log_file(self) -> Generator[Path, None, None]:
        """Create temporary log file."""
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp) / "test.log"

    def test_basic_logging(self, temp_log_file: Path):
        """Test basic logging setup and functionality."""
        logger = LogUtils.setup_logging(level="INFO", log_file=temp_log_file)

        test_message = "Test log message"
        logger.info(test_message)

        # Verify log file
        log_content = temp_log_file.read_text()
        assert test_message in log_content

        # Verify log level
        logger.debug("Debug message")  # Should not appear
        log_content = temp_log_file.read_text()
        assert "Debug message" not in log_content

    def test_json_logging(self, temp_log_file: Path):
        """Test JSON formatted logging."""
        logger = LogUtils.setup_logging(
            level="INFO", log_file=temp_log_file, json_format=True
        )

        test_message = "Test JSON log"
        logger.info(test_message)

        # Verify JSON format
        log_content = temp_log_file.read_text()
        log_entry = json.loads(log_content.strip())
        assert log_entry["message"] == test_message
        assert "timestamp" in log_entry
        assert log_entry["level"] == "INFO"

    def test_log_rotation(self, temp_log_file: Path):
        """Test log file rotation."""
        rotation_size = 1000  # 1KB
        logger = LogUtils.setup_logging(
            level="INFO",
            log_file=temp_log_file,
            rotation_size=rotation_size,
            backup_count=3,
        )

        # Write enough data to trigger multiple rotations
        for i in range(100):
            logger.info("X" * 100)  # 100 bytes per message

        # Verify rotation
        log_files = list(temp_log_file.parent.glob("test.log*"))
        assert 1 < len(log_files) <= 4  # Original + backups
        assert all(f.stat().st_size <= rotation_size for f in log_files)

    def test_context_logging(self, temp_log_file: Path):
        """Test contextual logging."""
        logger = LogUtils.setup_logging(
            level="INFO", log_file=temp_log_file, json_format=True
        )

        with LogUtils.log_context(user_id="123", action="test"):
            logger.info("Action performed")

            # Nested context
            with LogUtils.log_context(sub_action="detail"):
                logger.info("Sub-action performed")

        # Verify context in logs
        log_entries = [
            json.loads(line)
            for line in temp_log_file.read_text().strip().split("\n")
        ]

        assert log_entries[0]["context"]["user_id"] == "123"
        assert log_entries[1]["context"]["user_id"] == "123"
        assert log_entries[1]["context"]["sub_action"] == "detail"

    def test_multi_threaded_context(self):
        """Test context isolation between threads."""
        results = []

        def worker(user_id: str) -> None:
            with LogUtils.log_context(user_id=user_id):
                # Simulate some work
                time.sleep(0.1)
                # Get context
                context = LogUtils.get_context()
                results.append(context["user_id"])

        # Run multiple threads
        threads = [
            threading.Thread(target=worker, args=(f"user_{i}",))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify contexts were isolated
        assert sorted(results) == [f"user_{i}" for i in range(5)]

    def test_output_capture(self, temp_log_file: Path):
        """Test stdout/stderr capture."""
        logger = LogUtils.setup_logging(
            level="INFO", log_file=temp_log_file, json_format=True
        )

        with LogUtils.capture_output(logger):
            print("Stdout message")
            print("Error message", file=sys.stderr)

        # Verify captured output
        log_entries = [
            json.loads(line)
            for line in temp_log_file.read_text().strip().split("\n")
        ]

        assert any(
            e["message"] == "Stdout message" and e["level"] == "INFO"
            for e in log_entries
        )
        assert any(
            e["message"] == "Error message" and e["level"] == "ERROR"
            for e in log_entries
        )

    def test_decorated_logging(self, temp_log_file: Path):
        """Test logging decorator."""
        logger = LogUtils.setup_logging(
            level="DEBUG", log_file=temp_log_file, json_format=True
        )

        @LogUtils.log_call(logger=logger, log_args=True, log_result=True)
        def test_function(x: int, y: str) -> str:
            return f"{x}-{y}"

        result = test_function(42, "test")
        assert result == "42-test"

        # Verify logs
        log_entries = [
            json.loads(line)
            for line in temp_log_file.read_text().strip().split("\n")
        ]

        assert any(
            e["structured_data"]["function"] == "test_function"
            and "42" in e["structured_data"]["args"]
            and "test" in e["structured_data"]["result"]
            for e in log_entries
        )

    def test_error_handling(self, temp_log_file: Path):
        """Test error logging and handling."""
        logger = LogUtils.setup_logging(
            level="INFO", log_file=temp_log_file, json_format=True
        )

        @LogUtils.exception_handler(logger, reraise=False)
        def error_function():
            raise ValueError("Test error")

        # Execute function that raises error
        error_function()

        # Verify error logs
        log_entries = [
            json.loads(line)
            for line in temp_log_file.read_text().strip().split("\n")
        ]

        error_log = next(e for e in log_entries if e["level"] == "ERROR")
        assert "Test error" in error_log["message"]
        assert error_log["context"]["error_type"] == "ValueError"

    def test_structured_logging(self, temp_log_file: Path):
        """Test structured logging capabilities."""
        logger = LogUtils.setup_logging(
            level="INFO", log_file=temp_log_file, json_format=True
        )

        structured_data = {
            "user": {"id": 123, "name": "test"},
            "metrics": {"duration": 0.5, "status": "success"},
        }

        logger.info(
            "Structured log test", extra={"structured_data": structured_data}
        )

        # Verify structured data in logs
        log_entries = [
            json.loads(line)
            for line in temp_log_file.read_text().strip().split("\n")
        ]

        assert log_entries[0]["data"] == structured_data

    def test_stack_trace(self):
        """Test stack trace formatting."""

        def nested_function():
            return LogUtils.stack_trace()

        def outer_function():
            return nested_function()

        trace = outer_function()

        assert "nested_function" in trace
        assert "outer_function" in trace
        assert ".py:" in trace  # Contains file and line info

    def test_error_conditions(self, temp_log_file: Path):
        """Test logging under error conditions."""
        # Test with invalid log file path
        invalid_path = Path("/nonexistent/path/log.txt")
        logger = LogUtils.setup_logging(level="INFO", log_file=invalid_path)

        # Should still log to console
        stream = io.StringIO()
        sys.stdout = stream
        logger.info("Test message")
        sys.stdout = sys.__stdout__

        assert "Test message" in stream.getvalue()

    def test_performance(self, benchmark, temp_log_file: Path):
        """Test logging performance."""

        def bench_logging():
            logger = LogUtils.setup_logging(
                level="INFO", log_file=temp_log_file, json_format=True
            )

            with LogUtils.log_context(bench="test"):
                for _ in range(100):
                    logger.info("Benchmark log message")

        benchmark(bench_logging)

    def test_cleanup(self, temp_log_file: Path):
        """Test resource cleanup."""
        logger = LogUtils.setup_logging(level="INFO", log_file=temp_log_file)

        # Test context cleanup
        with LogUtils.log_context(test="value"):
            pass
        assert "test" not in LogUtils.get_context()

        # Test output capture cleanup
        original_stdout = sys.stdout
        with LogUtils.capture_output(logger):
            pass
        assert sys.stdout is original_stdout
