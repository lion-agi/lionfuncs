"""Input/Output operation utilities.

This module provides safe and efficient utilities for file operations, including
atomic writes, chunked reading, and resource management.
"""

import os
import json
import tempfile
import hashlib
import shutil
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    BinaryIO,
    Callable,
    Generator,
    Iterator,
    Optional,
    TextIO,
    Union,
    TypeVar,
    Generic,
)
from .base import UtilityGroup, PathLike
from .exceptions import IOError

T = TypeVar("T")


@dataclass
class FileInfo:
    """File information container."""

    path: Path
    size: int
    created: datetime
    modified: datetime
    checksum: Optional[str] = None

    @classmethod
    def from_path(
        cls, path: PathLike, calc_checksum: bool = False
    ) -> "FileInfo":
        """Create FileInfo from path."""
        path = Path(path)
        stats = path.stat()
        checksum = None
        if calc_checksum:
            checksum = cls.calculate_checksum(path)

        return cls(
            path=path,
            size=stats.st_size,
            created=datetime.fromtimestamp(stats.st_ctime),
            modified=datetime.fromtimestamp(stats.st_mtime),
            checksum=checksum,
        )

    @staticmethod
    def calculate_checksum(path: PathLike, chunk_size: int = 8192) -> str:
        """Calculate file SHA-256 checksum."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hasher.update(chunk)
        return hasher.hexdigest()


class SafeOpen(Generic[T]):
    """Safe file handle manager."""

    def __init__(
        self,
        path: PathLike,
        mode: str = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        **kwargs: Any,
    ):
        self.path = Path(path)
        self.mode = mode
        self.encoding = encoding
        self.errors = errors
        self.kwargs = kwargs
        self.file: Optional[Union[TextIO, BinaryIO]] = None

    def __enter__(self) -> Union[TextIO, BinaryIO]:
        try:
            self.file = open(
                self.path,
                mode=self.mode,
                encoding=self.encoding,
                errors=self.errors,
                **self.kwargs,
            )
            return self.file
        except Exception as e:
            raise IOError(f"Failed to open {self.path}: {e}") from e

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.file:
            self.file.close()


class IOUtils(UtilityGroup):
    """I/O utility functions."""

    @classmethod
    def get_name(cls) -> str:
        return "io_utils"

    @staticmethod
    @contextmanager
    def atomic_write(
        path: PathLike,
        mode: str = "w",
        encoding: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[Union[TextIO, BinaryIO], None, None]:
        """Atomically write to file using temporary file.

        Args:
            path: Target file path
            mode: File open mode
            encoding: File encoding
            **kwargs: Additional arguments for open()

        Yields:
            File object for writing

        Example:
            >>> with IOUtils.atomic_write('data.txt') as f:
            ...     f.write('content')
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        tmp = None
        try:
            # Create temp file in same directory
            fd, tmp = tempfile.mkstemp(
                dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
            )
            os.close(fd)
            tmp = Path(tmp)

            with open(tmp, mode=mode, encoding=encoding, **kwargs) as f:
                yield f

            # Ensure all data is written
            if hasattr(f, "flush"):
                f.flush()
                os.fsync(f.fileno())

            # Atomic rename
            tmp.replace(path)

        except Exception as e:
            raise IOError(f"Atomic write failed: {e}") from e
        finally:
            if tmp and tmp.exists():
                tmp.unlink()

    @staticmethod
    def safe_read(
        path: PathLike,
        encoding: str = "utf-8",
        chunk_size: Optional[int] = None,
        **kwargs: Any,
    ) -> Union[str, Iterator[str]]:
        """Safely read file content.

        Args:
            path: File path
            encoding: File encoding
            chunk_size: Optional chunk size for reading
            **kwargs: Additional arguments for open()

        Returns:
            File content or iterator of chunks
        """
        path = Path(path)
        if not path.exists():
            raise IOError(f"File not found: {path}")
        if not path.is_file():
            raise IOError(f"Not a file: {path}")

        try:
            if chunk_size:
                return IOUtils.chunk_reader(
                    path, chunk_size, encoding=encoding
                )
            return path.read_text(encoding=encoding, **kwargs)
        except Exception as e:
            raise IOError(f"Failed to read {path}: {e}") from e

    @staticmethod
    def safe_write(
        path: PathLike,
        content: Union[str, bytes],
        encoding: str = "utf-8",
        atomic: bool = True,
        mkdir: bool = True,
        **kwargs: Any,
    ) -> None:
        """Safely write content to file.

        Args:
            path: File path
            content: Content to write
            encoding: File encoding
            atomic: Use atomic write
            mkdir: Create parent directories
        """
        path = Path(path)
        if mkdir:
            path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if atomic:
                with IOUtils.atomic_write(
                    path,
                    "w" if isinstance(content, str) else "wb",
                    encoding=encoding,
                    **kwargs,
                ) as f:
                    f.write(content)
            else:
                if isinstance(content, str):
                    path.write_text(content, encoding=encoding)
                else:
                    path.write_bytes(content)
        except Exception as e:
            raise IOError(f"Failed to write to {path}: {e}") from e

    @staticmethod
    def read_json(
        path: PathLike, encoding: str = "utf-8", **kwargs: Any
    ) -> Any:
        """Read and parse JSON file.

        Args:
            path: JSON file path
            encoding: File encoding
            **kwargs: Additional arguments for json.loads
        """
        try:
            content = IOUtils.safe_read(path, encoding)
            return json.loads(content, **kwargs)
        except Exception as e:
            raise IOError(f"Failed to read JSON from {path}: {e}") from e

    @staticmethod
    def write_json(
        path: PathLike,
        data: Any,
        encoding: str = "utf-8",
        atomic: bool = True,
        indent: int = 2,
        **kwargs: Any,
    ) -> None:
        """Write data as JSON to file.

        Args:
            path: Output file path
            data: Data to write
            encoding: File encoding
            atomic: Use atomic write
            indent: JSON indentation
        """
        try:
            content = json.dumps(data, indent=indent, **kwargs)
            IOUtils.safe_write(path, content, encoding, atomic)
        except Exception as e:
            raise IOError(f"Failed to write JSON to {path}: {e}") from e

    @staticmethod
    @contextmanager
    def chunk_reader(
        path: PathLike,
        chunk_size: int = 8192,
        binary: bool = False,
        encoding: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[Union[str, bytes], None, None]:
        """Context manager for chunked file reading.

        Args:
            path: File path
            chunk_size: Size of chunks to read
            binary: Read in binary mode
            encoding: File encoding

        Yields:
            File chunks
        """
        path = Path(path)
        mode = "rb" if binary else "r"

        with open(path, mode=mode, encoding=encoding, **kwargs) as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    @staticmethod
    def get_file_info(path: PathLike, calc_checksum: bool = False) -> FileInfo:
        """Get file information.

        Args:
            path: File path
            calc_checksum: Calculate file checksum

        Returns:
            FileInfo object
        """
        return FileInfo.from_path(path, calc_checksum)

    @staticmethod
    def ensure_dir(
        path: PathLike, mode: int = 0o755, parents: bool = True
    ) -> Path:
        """Ensure directory exists.

        Args:
            path: Directory path
            mode: Directory permissions
            parents: Create parent directories

        Returns:
            Path object
        """
        path = Path(path)
        path.mkdir(mode=mode, parents=parents, exist_ok=True)
        return path

    @staticmethod
    def copy_file(
        src: PathLike, dst: PathLike, follow_symlinks: bool = True
    ) -> None:
        """Safely copy file.

        Args:
            src: Source path
            dst: Destination path
            follow_symlinks: Follow symbolic links
        """
        src = Path(src)
        dst = Path(dst)

        if not src.exists():
            raise IOError(f"Source file not found: {src}")
        if not src.is_file():
            raise IOError(f"Source is not a file: {src}")

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
        except Exception as e:
            raise IOError(f"Failed to copy {src} to {dst}: {e}") from e

    @staticmethod
    def remove_path(
        path: PathLike, recursive: bool = False, missing_ok: bool = True
    ) -> None:
        """Safely remove file or directory.

        Args:
            path: Path to remove
            recursive: Remove directories recursively
            missing_ok: Don't error if path doesn't exist
        """
        path = Path(path)
        try:
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=missing_ok)
            elif path.is_dir():
                if recursive:
                    shutil.rmtree(path)
                else:
                    path.rmdir()
        except Exception as e:
            raise IOError(f"Failed to remove {path}: {e}") from e

    @staticmethod
    def scan_dir(
        directory: PathLike,
        pattern: str = "*",
        recursive: bool = True,
        include_dirs: bool = False,
        follow_links: bool = False,
    ) -> Iterator[Path]:
        """Scan directory for files.

        Args:
            directory: Directory to scan
            pattern: File pattern to match
            recursive: Scan recursively
            include_dirs: Include directories in results
            follow_links: Follow symbolic links

        Yields:
            Matching Path objects
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise IOError(f"Not a directory: {directory}")

        for path in (
            directory.rglob(pattern) if recursive else directory.glob(pattern)
        ):
            if follow_links or not path.is_symlink():
                if include_dirs or path.is_file():
                    yield path
