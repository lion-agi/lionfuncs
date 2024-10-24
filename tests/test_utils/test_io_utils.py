"""Tests for I/O operation utilities."""

import os
import json
import tempfile
from pathlib import Path
import pytest
from lionfuncs.utils.io_utils import IOUtils, FileInfo


class TestIOUtils:
    """Test suite for IOUtils."""

    @pytest.fixture
    def temp_dir(self) -> Path:  # type: ignore
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    def test_atomic_write(self, temp_dir):
        """Test atomic write operation."""
        test_file = temp_dir / "test.txt"
        content = "test content"

        # Test successful write
        with IOUtils.atomic_write(test_file) as f:
            f.write(content)
        assert test_file.read_text() == content

        # Test failed write doesn't corrupt file
        with pytest.raises(IOError):
            with IOUtils.atomic_write(test_file) as f:
                f.write("new content")
                raise Exception("Simulated failure")
        assert test_file.read_text() == content

    def test_safe_read(self, temp_dir):
        """Test safe read operation."""
        test_file = temp_dir / "test.txt"
        content = "test content"
        test_file.write_text(content)

        # Test basic read
        assert IOUtils.safe_read(test_file) == content

        # Test chunked read
        chunks = list(IOUtils.safe_read(test_file, chunk_size=5))
        assert "".join(chunks) == content

        # Test non-existent file
        with pytest.raises(IOError):
            IOUtils.safe_read(temp_dir / "nonexistent.txt")

    def test_safe_write(self, temp_dir):
        """Test safe write operation."""
        test_file = temp_dir / "test.txt"
        content = "test content"

        # Test basic write
        IOUtils.safe_write(test_file, content)
        assert test_file.read_text() == content

        # Test atomic write
        IOUtils.safe_write(test_file, content, atomic=True)
        assert test_file.read_text() == content

        # Test directory creation
        nested_file = temp_dir / "nested" / "test.txt"
        IOUtils.safe_write(nested_file, content, mkdir=True)
        assert nested_file.read_text() == content

    def test_json_operations(self, temp_dir):
        """Test JSON read/write operations."""
        test_file = temp_dir / "test.json"
        data = {
            "string": "value",
            "number": 42,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }

        # Test write
        IOUtils.write_json(test_file, data)

        # Test read
        loaded = IOUtils.read_json(test_file)
        assert loaded == data

        # Test pretty printing
        content = test_file.read_text()
        assert "\n" in content  # Verify indentation

        # Test invalid JSON
        with pytest.raises(IOError):
            IOUtils.read_json(temp_dir / "invalid.json")

    def test_chunk_reader(self, temp_dir):
        """Test chunked reading."""
        test_file = temp_dir / "test.txt"
        content = "a" * 1000  # 1KB content
        test_file.write_text(content)

        # Test text mode
        chunks = list(IOUtils.chunk_reader(test_file, chunk_size=100))
        assert "".join(chunks) == content
        assert all(len(chunk) <= 100 for chunk in chunks)

        # Test binary mode
        binary_chunks = list(
            IOUtils.chunk_reader(test_file, chunk_size=100, binary=True)
        )
        assert b"".join(binary_chunks) == content.encode()

    def test_file_info(self, temp_dir):
        """Test file information retrieval."""
        test_file = temp_dir / "test.txt"
        content = "test content"
        test_file.write_text(content)

        # Test basic info
        info = IOUtils.get_file_info(test_file)
        assert info.size == len(content)
        assert info.path == test_file
        assert info.checksum is None

        # Test with checksum
        info = IOUtils.get_file_info(test_file, calc_checksum=True)
        assert info.checksum is not None
        assert len(info.checksum) == 64  # SHA-256 length

    def test_directory_operations(self, temp_dir):
        """Test directory operations."""
        test_dir = temp_dir / "test_dir"

        # Test directory creation
        created_dir = IOUtils.ensure_dir(test_dir)
        assert created_dir.exists()
        assert created_dir.is_dir()

        # Test nested directory
        nested_dir = test_dir / "nested" / "dir"
        IOUtils.ensure_dir(nested_dir, parents=True)
        assert nested_dir.exists()

        # Test directory removal
        IOUtils.remove_path(test_dir, recursive=True)
        assert not test_dir.exists()

    def test_file_copy(self, temp_dir):
        """Test file copy operations."""
        source = temp_dir / "source.txt"
        dest = temp_dir / "dest.txt"
        content = "test content"
        source.write_text(content)

        # Test basic copy
        IOUtils.copy_file(source, dest)
        assert dest.exists()
        assert dest.read_text() == content

        # Test nested copy
        nested_dest = temp_dir / "nested" / "dest.txt"
        IOUtils.copy_file(source, nested_dest)
        assert nested_dest.exists()
        assert nested_dest.read_text() == content

        # Test copy errors
        with pytest.raises(IOError):
            IOUtils.copy_file(temp_dir / "nonexistent.txt", dest)

    def test_directory_scan(self, temp_dir):
        """Test directory scanning."""
        # Create test files
        (temp_dir / "file1.txt").write_text("content")
        (temp_dir / "file2.txt").write_text("content")
        nested_dir = temp_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "file3.txt").write_text("content")

        # Test non-recursive scan
        files = list(IOUtils.scan_dir(temp_dir, recursive=False))
        assert len(files) == 2

        # Test recursive scan
        files = list(IOUtils.scan_dir(temp_dir, recursive=True))
        assert len(files) == 3

        # Test pattern matching
        files = list(IOUtils.scan_dir(temp_dir, pattern="*.txt"))
        assert all(f.suffix == ".txt" for f in files)

    def test_symlink_handling(self, temp_dir):
        """Test symbolic link handling."""
        original = temp_dir / "original.txt"
        link = temp_dir / "link.txt"
        content = "test content"
        original.write_text(content)
        link.symlink_to(original)

        # Test symlink read
        assert IOUtils.safe_read(link) == content

        # Test directory scan with links
        files = list(IOUtils.scan_dir(temp_dir, follow_links=False))
        assert len(files) == 1  # Only original file

        files = list(IOUtils.scan_dir(temp_dir, follow_links=True))
        assert len(files) == 2  # Original and link

    def test_error_handling(self, temp_dir):
        """Test error handling scenarios."""
        test_file = temp_dir / "test.txt"

        # Test permission error
        test_file.write_text("content")
        test_file.chmod(0o000)  # Remove all permissions

        with pytest.raises(IOError):
            IOUtils.safe_read(test_file)

        # Restore permissions for cleanup
        test_file.chmod(0o666)

        # Test write to read-only directory
        if os.name != "nt":  # Skip on Windows
            read_only_dir = temp_dir / "readonly"
            read_only_dir.mkdir()
            read_only_dir.chmod(0o555)  # Read-only

            with pytest.raises(IOError):
                IOUtils.safe_write(read_only_dir / "file.txt", "content")

            read_only_dir.chmod(0o755)  # Restore for cleanup

    def test_large_file_handling(self, temp_dir):
        """Test handling of large files."""
        large_file = temp_dir / "large.txt"
        size_mb = 10
        chunk_size = 1024 * 1024  # 1MB

        # Create large file
        with IOUtils.atomic_write(large_file, "wb") as f:
            for _ in range(size_mb):
                f.write(b"0" * chunk_size)

        # Test chunked reading
        total_size = 0
        for chunk in IOUtils.chunk_reader(large_file, binary=True):
            total_size += len(chunk)

        assert total_size == size_mb * chunk_size

        # Test memory efficient copy
        copy_file = temp_dir / "large_copy.txt"
        IOUtils.copy_file(large_file, copy_file)
        assert copy_file.stat().st_size == large_file.stat().st_size

    def test_concurrent_access(self, temp_dir):
        """Test concurrent file access."""
        import threading

        test_file = temp_dir / "concurrent.txt"
        thread_count = 10
        iterations = 100

        def worker():
            for i in range(iterations):
                with IOUtils.atomic_write(test_file) as f:
                    f.write(f"Thread write {i}\n")

        threads = [
            threading.Thread(target=worker) for _ in range(thread_count)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify file integrity
        content = test_file.read_text()
        assert len(content.splitlines()) == thread_count * iterations

    def test_cleanup(self, temp_dir):
        """Test cleanup after operations."""
        test_file = temp_dir / "test.txt"

        # Test temporary file cleanup after atomic write
        with IOUtils.atomic_write(test_file) as f:
            f.write("content")

        # Verify no temporary files remain
        temp_files = [f for f in temp_dir.iterdir() if f.name.startswith(".")]
        assert not temp_files

        # Test cleanup after failed operations
        try:
            with IOUtils.atomic_write(test_file) as f:
                f.write("content")
                raise Exception("Simulated failure")
        except Exception:
            pass

        # Verify no temporary files remain
        temp_files = [f for f in temp_dir.iterdir() if f.name.startswith(".")]
        assert not temp_files

    def test_performance(self, benchmark):
        """Test IO operation performance."""

        def bench_operation(tmp_path):
            file_path = tmp_path / "bench.txt"
            data = "x" * 1000000  # 1MB

            # Write
            IOUtils.safe_write(file_path, data)

            # Read
            content = IOUtils.safe_read(file_path)
            assert len(content) == len(data)

            # Cleanup
            IOUtils.remove_path(file_path)

        with tempfile.TemporaryDirectory() as tmp:
            benchmark(bench_operation, Path(tmp))
