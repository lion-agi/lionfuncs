"""Tests for path manipulation utilities."""

import os
import shutil
import stat
import time
from pathlib import Path
import pytest
from typing import Generator

from lionfuncs.utils.path_utils import PathUtils, PathValidator, PathInfo


class TestPathUtils:
    """Test suite for PathUtils."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create temporary directory for tests."""
        with pytest.TemporaryDirectory() as tmp:
            yield Path(tmp)

    def test_ensure_path(self, temp_dir: Path):
        """Test path creation and validation."""
        # Test directory creation
        test_dir = temp_dir / "test_dir"
        created = PathUtils.ensure_path(test_dir)
        assert created.exists()
        assert created.is_dir()

        # Test file creation
        test_file = test_dir / "test.txt"
        created = PathUtils.ensure_path(test_file)
        assert created.exists()
        assert created.is_file()

        # Test permissions
        if os.name != "nt":  # Skip on Windows
            test_dir = temp_dir / "mode_dir"
            created = PathUtils.ensure_path(test_dir, mode=0o700)
            assert stat.S_IMODE(created.stat().st_mode) == 0o700

    def test_unique_path(self, temp_dir: Path):
        """Test unique path generation."""
        # Create some existing files
        (temp_dir / "test.txt").touch()
        (temp_dir / "test_1.txt").touch()

        # Get unique path
        unique = PathUtils.get_unique_path(
            temp_dir, prefix="test", suffix=".txt"
        )
        assert not unique.exists()
        assert unique.name.startswith("test")
        assert unique.suffix == ".txt"

        # Test max attempts
        with pytest.raises(IOError):
            PathUtils.get_unique_path(
                temp_dir, prefix="test", suffix=".txt", max_attempts=1
            )

    def test_scan_directory(self, temp_dir: Path):
        """Test directory scanning."""
        # Create test files
        (temp_dir / "file1.txt").touch()
        (temp_dir / "file2.txt").touch()
        nested = temp_dir / "nested"
        nested.mkdir()
        (nested / "file3.txt").touch()

        # Test recursive scan
        files = list(PathUtils.scan_directory(temp_dir))
        assert len(files) == 3
        assert all(f.suffix == ".txt" for f in files)

        # Test non-recursive
        files = list(PathUtils.scan_directory(temp_dir, recursive=False))
        assert len(files) == 2

        # Test pattern matching
        files = list(
            PathUtils.scan_directory(temp_dir, pattern="file[12].txt")
        )
        assert len(files) == 2

        # Test exclusion
        files = list(
            PathUtils.scan_directory(temp_dir, exclude_patterns={"file1.txt"})
        )
        assert len(files) == 2
        assert all(f.name != "file1.txt" for f in files)

    def test_move_copy_remove(self, temp_dir: Path):
        """Test path operations."""
        # Create test file
        source = temp_dir / "source.txt"
        source.write_text("test")

        # Test copy
        dest = temp_dir / "dest.txt"
        copied = PathUtils.copy_path(source, dest)
        assert copied.exists()
        assert copied.read_text() == "test"

        # Test move
        moved = temp_dir / "moved.txt"
        result = PathUtils.move_path(dest, moved)
        assert result.exists()
        assert not dest.exists()
        assert result.read_text() == "test"

        # Test remove
        PathUtils.remove_path(moved)
        assert not moved.exists()

    def test_path_info(self, temp_dir: Path):
        """Test path information retrieval."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        info = PathUtils.get_path_info(test_file)
        assert info.path == test_file
        assert info.size == len("test content")
        assert info.is_file
        assert not info.is_dir
        assert not info.is_symlink

    def test_tree_size(self, temp_dir: Path):
        """Test directory tree size calculation."""
        # Create test files
        file1 = temp_dir / "file1.txt"
        file1.write_text("a" * 100)

        nested = temp_dir / "nested"
        nested.mkdir()
        file2 = nested / "file2.txt"
        file2.write_text("b" * 150)

        # Calculate total size
        total_size, file_count = PathUtils.get_tree_size(temp_dir)
        assert total_size == 250  # 100 + 150
        assert file_count == 2

    def test_find_duplicates(self, temp_dir: Path):
        """Test duplicate file detection."""
        # Create duplicate files
        content1 = "content1"
        content2 = "content2"

        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file3 = temp_dir / "sub" / "file3.txt"

        file1.write_text(content1)
        file2.write_text(content1)  # Duplicate of file1
        file3.parent.mkdir()
        file3.write_text(content2)

        # Find duplicates by content
        duplicates = PathUtils.find_duplicates(temp_dir)
        assert len(duplicates) == 1  # One group of duplicates
        assert len(duplicates[0]) == 2  # Two files in group
        assert {file1, file2} == set(duplicates[0])

    def test_path_accessibility(self, temp_dir: Path):
        """Test path access checks."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        # Test read access
        assert PathUtils.is_path_accessible(test_file, "r")

        if os.name != "nt":  # Skip permission tests on Windows
            # Remove write permission
            test_file.chmod(0o444)
            assert not PathUtils.is_path_accessible(test_file, "w")

            # Remove read permission
            test_file.chmod(0o000)
            assert not PathUtils.is_path_accessible(test_file, "r")

            # Restore permissions for cleanup
            test_file.chmod(0o644)

    def test_relative_paths(self, temp_dir: Path):
        """Test relative path operations."""
        nested = temp_dir / "a" / "b" / "c"
        nested.mkdir(parents=True)
        test_file = nested / "test.txt"
        test_file.touch()

        # Make single path relative
        rel_path = PathUtils.make_path_relative(test_file, temp_dir)
        assert str(rel_path) == os.path.join("a", "b", "c", "test.txt")

        # Make multiple paths relative
        paths = [nested, test_file]
        rel_paths = PathUtils.make_path_relative(paths, temp_dir)
        assert len(rel_paths) == 2
        assert all(not p.is_absolute() for p in rel_paths)

    def test_subpath_detection(self, temp_dir: Path):
        """Test subpath detection."""
        parent = temp_dir / "parent"
        child = parent / "child"
        sibling = temp_dir / "sibling"

        parent.mkdir()
        child.mkdir()
        sibling.mkdir()

        # Test valid subpath
        assert PathUtils.is_subpath(child, parent)

        # Test non-subpath
        assert not PathUtils.is_subpath(sibling, parent)

        # Test with strict mode
        assert not PathUtils.is_subpath(parent, parent, strict=True)
        assert PathUtils.is_subpath(parent, parent, strict=False)

    def test_filter_paths(self, temp_dir: Path):
        """Test path filtering."""
        # Create test paths
        file1 = temp_dir / "test1.txt"
        file2 = temp_dir / "test2.txt"
        dir1 = temp_dir / "dir1"

        file1.write_text("small")
        file2.write_text("larger content")
        dir1.mkdir()

        paths = [file1, file2, dir1]

        # Filter by type
        files = PathUtils.filter_paths(paths, files_only=True)
        assert len(files) == 2
        assert all(p.is_file() for p in files)

        dirs = PathUtils.filter_paths(paths, dirs_only=True)
        assert len(dirs) == 1
        assert all(p.is_dir() for p in dirs)

        # Filter by size
        large_files = PathUtils.filter_paths(
            paths, files_only=True, min_size=10
        )
        assert len(large_files) == 1
        assert file2 in large_files

    def test_path_permissions(self, temp_dir: Path):
        """Test permission management."""
        if os.name == "nt":  # Skip on Windows
            return

        test_dir = temp_dir / "permissions"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.touch()

        # Set permissions recursively
        PathUtils.set_path_permissions(test_dir, 0o700, recursive=True)

        # Verify permissions
        assert stat.S_IMODE(test_dir.stat().st_mode) == 0o700
        assert stat.S_IMODE(test_file.stat().st_mode) == 0o700

    def test_path_compression(self, temp_dir: Path):
        """Test path compression and extraction."""
        # Create test files
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        file1 = source_dir / "file1.txt"
        file2 = source_dir / "file2.txt"

        file1.write_text("content1")
        file2.write_text("content2")

        # Test zip compression
        zip_path = temp_dir / "archive.zip"
        PathUtils.compress_paths([source_dir], zip_path, format="zip")
        assert zip_path.exists()

        # Test extraction
        extract_dir = temp_dir / "extracted"
        PathUtils.extract_archive(zip_path, extract_dir)

        # Verify contents
        extracted_files = list(extract_dir.rglob("*.txt"))
        assert len(extracted_files) == 2
        assert any(f.read_text() == "content1" for f in extracted_files)
        assert any(f.read_text() == "content2" for f in extracted_files)

    def test_path_validation(self):
        """Test path validation."""
        # Test safe paths
        assert PathValidator.is_safe_path("/normal/path")
        assert PathValidator.is_safe_path("relative/path", allow_relative=True)

        # Test unsafe paths
        assert not PathValidator.is_safe_path("../traversal")
        assert not PathValidator.is_safe_path("COM1")  # Windows device
        assert not PathValidator.is_safe_path("/path/with/\0/null")

    def test_error_handling(self, temp_dir: Path):
        """Test error handling."""
        non_existent = temp_dir / "non_existent"

        # Test operation on non-existent path
        with pytest.raises(IOError):
            PathUtils.ensure_path(non_existent / "file", create=False)

        # Test invalid moves
        source = temp_dir / "source.txt"
        source.touch()

        with pytest.raises(IOError):
            PathUtils.move_path(source, temp_dir / "non_existent" / "dest.txt")

    def test_cross_platform(self, temp_dir: Path):
        """Test cross-platform path handling."""
        # Test path normalization
        if os.name == "nt":
            path = temp_dir / "folder\\subfolder\\file.txt"
        else:
            path = temp_dir / "folder/subfolder/file.txt"

        normalized = PathValidator.normalize_path(path)
        assert str(normalized).replace("\\", "/") == str(path).replace(
            "\\", "/"
        )

        # Test path comparison
        path1 = temp_dir / "folder" / "file.txt"
        path2 = temp_dir / "folder" / ".." / "folder" / "file.txt"

        resolved1 = PathValidator.normalize_path(path1)
        resolved2 = PathValidator.normalize_path(path2)
        assert resolved1 == resolved2

    def test_performance(self, benchmark, temp_dir: Path):
        """Test path operations performance."""
        # Create test directory structure
        for i in range(100):
            path = temp_dir / f"dir_{i}"
            path.mkdir()
            for j in range(10):
                (path / f"file_{j}.txt").touch()

        def bench_operation():
            # Scan directory
            files = list(PathUtils.scan_directory(temp_dir))
            # Get path info
            for file in files[:10]:
                PathUtils.get_path_info(file)
            # Calculate tree size
            PathUtils.get_tree_size(temp_dir)

        benchmark(bench_operation)

    def test_concurrent_access(self, temp_dir: Path):
        """Test concurrent path operations."""
        import threading

        file_path = temp_dir / "concurrent.txt"
        error_occurred = False

        def worker():
            nonlocal error_occurred
            try:
                PathUtils.ensure_path(file_path)
                time.sleep(0.1)
                if file_path.exists():
                    PathUtils.remove_path(file_path)
            except Exception:
                error_occurred = True

        # Run multiple threads
        threads = [threading.Thread(target=worker) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not error_occurred
