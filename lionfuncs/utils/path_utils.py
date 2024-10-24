"""Path manipulation utilities.

This module provides secure and cross-platform path manipulation utilities with
validation, normalization, and convenience functions.
"""

import asyncio
import os
import re
import shutil
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import (
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    Pattern,
    TypeVar,
)

from .base import UtilityGroup, PathLike
from .exceptions import IOError

T = TypeVar("T")


@dataclass
class PathInfo:
    """Path information container."""

    path: Path
    size: int
    created: datetime
    modified: datetime
    accessed: datetime
    is_file: bool
    is_dir: bool
    is_symlink: bool
    owner: str
    permissions: int

    @classmethod
    def from_path(cls, path: PathLike) -> "PathInfo":
        """Create PathInfo from path."""
        path = Path(path)
        stats = path.stat()
        return cls(
            path=path,
            size=stats.st_size,
            created=datetime.fromtimestamp(stats.st_ctime),
            modified=datetime.fromtimestamp(stats.st_mtime),
            accessed=datetime.fromtimestamp(stats.st_atime),
            is_file=path.is_file(),
            is_dir=path.is_dir(),
            is_symlink=path.is_symlink(),
            owner=path.owner(),
            permissions=stats.st_mode,
        )


class PathValidator:
    """Path validation utilities."""

    # Common unsafe patterns
    UNSAFE_PATTERNS = {
        "win_device": re.compile(
            r"^(CON|PRN|AUX|NUL|COM\d|LPT\d)($|\.|\\|/)", re.I
        ),
        "control_chars": re.compile(r"[\x00-\x1f\x7f]"),
        "relative_traversal": re.compile(r"\.{2}[/\\]"),
    }

    # Maximum path lengths
    MAX_PATH_LENGTH = {"windows": 260, "unix": 4096}

    @classmethod
    def is_safe_path(
        cls,
        path: PathLike,
        allow_relative: bool = False,
        allow_symlinks: bool = False,
        check_existence: bool = True,
    ) -> bool:
        """Check if path is safe to use.

        Args:
            path: Path to validate
            allow_relative: Allow relative paths
            allow_symlinks: Allow symbolic links
            check_existence: Check if path exists
        """
        try:
            path = Path(path)

            # Check basic path validity
            str_path = str(path)
            if not str_path:
                return False

            # Check path length
            max_length = cls.MAX_PATH_LENGTH[
                "windows" if os.name == "nt" else "unix"
            ]
            if len(str_path) > max_length:
                return False

            # Check unsafe patterns
            if any(p.search(str_path) for p in cls.UNSAFE_PATTERNS.values()):
                return False

            # Check relative paths
            if not allow_relative and not path.is_absolute():
                return False

            # Check symlinks
            if not allow_symlinks and path.is_symlink():
                return False

            # Check existence if required
            if check_existence and not path.exists():
                return False

            return True
        except Exception:
            return False

    @classmethod
    def normalize_path(
        cls,
        path: PathLike,
        make_absolute: bool = True,
        resolve_symlinks: bool = True,
        collapse_user: bool = True,
    ) -> Path:
        """Normalize path representation.

        Args:
            path: Path to normalize
            make_absolute: Convert to absolute path
            resolve_symlinks: Resolve symbolic links
            collapse_user: Collapse user home directory
        """
        path = Path(path)
        if collapse_user:
            try:
                path = path.expanduser()
            except RuntimeError:
                pass

        if resolve_symlinks:
            path = path.resolve()
        elif make_absolute:
            path = path.absolute()

        return path


class PathUtils(UtilityGroup):
    """Path utility functions."""

    @classmethod
    def get_name(cls) -> str:
        return "path_utils"

    @staticmethod
    def ensure_path(
        path: PathLike,
        create: bool = True,
        mode: int = 0o755,
        parents: bool = True,
        exist_ok: bool = True,
    ) -> Path:
        """Ensure path exists.

        Args:
            path: Path to ensure
            create: Create path if it doesn't exist
            mode: Directory permissions
            parents: Create parent directories
            exist_ok: Don't error if path exists

        Returns:
            Path object

        Raises:
            IOError: If path creation fails
        """
        path = Path(path)

        if create and not path.exists():
            try:
                if path.suffix:  # File path
                    path.parent.mkdir(
                        mode=mode, parents=parents, exist_ok=exist_ok
                    )
                    path.touch(mode=mode, exist_ok=exist_ok)
                else:  # Directory path
                    path.mkdir(mode=mode, parents=parents, exist_ok=exist_ok)
            except Exception as e:
                raise IOError(f"Failed to create path {path}: {e}")

        return path

    @staticmethod
    def get_unique_path(
        directory: PathLike,
        prefix: str = "",
        suffix: str = "",
        separator: str = "_",
        max_attempts: int = 1000,
    ) -> Path:
        """Get unique path in directory.

        Args:
            directory: Target directory
            prefix: Path prefix
            suffix: Path suffix
            separator: Number separator
            max_attempts: Maximum attempts

        Returns:
            Unique Path object

        Raises:
            IOError: If unique path cannot be found
        """
        directory = Path(directory)
        counter = 0

        while counter < max_attempts:
            if counter == 0:
                path = directory / f"{prefix}{suffix}"
            else:
                path = directory / f"{prefix}{separator}{counter}{suffix}"

            if not path.exists():
                return path
            counter += 1

        raise IOError(
            f"Could not find unique path after {max_attempts} attempts"
        )

    @staticmethod
    def scan_directory(
        directory: PathLike,
        pattern: Union[str, Pattern] = "*",
        recursive: bool = True,
        include_dirs: bool = False,
        exclude_patterns: Optional[Set[str]] = None,
        follow_links: bool = False,
    ) -> Iterator[Path]:
        """Scan directory for matching paths.

        Args:
            directory: Directory to scan
            pattern: Match pattern
            recursive: Scan recursively
            include_dirs: Include directories
            exclude_patterns: Patterns to exclude
            follow_links: Follow symbolic links
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise IOError(f"Not a directory: {directory}")

        exclude_patterns = exclude_patterns or set()

        def match_path(path: Path) -> bool:
            """Check if path matches criteria."""
            if exclude_patterns:
                str_path = str(path)
                if any(re.search(p, str_path) for p in exclude_patterns):
                    return False

            if isinstance(pattern, str):
                return path.match(pattern)
            return bool(pattern.search(str(path)))

        for path in directory.rglob("*") if recursive else directory.glob("*"):
            if not follow_links and path.is_symlink():
                continue

            if path.is_file() or (include_dirs and path.is_dir()):
                if match_path(path):
                    yield path

    @staticmethod
    def relative_path(
        path: PathLike, start: Optional[PathLike] = None, strict: bool = True
    ) -> Path:
        """Get relative path.

        Args:
            path: Path to make relative
            start: Start path (default: current directory)
            strict: Enforce path is under start
        """
        path = Path(path)
        if start is None:
            start = Path.cwd()
        else:
            start = Path(start)

        try:
            rel_path = path.relative_to(start)
            return rel_path
        except ValueError as e:
            if strict:
                raise ValueError(f"Path {path} is not under {start}") from e
            return path

    @staticmethod
    def move_path(
        src: PathLike, dst: PathLike, overwrite: bool = False
    ) -> Path:
        """Safely move path.

        Args:
            src: Source path
            dst: Destination path
            overwrite: Overwrite existing destination
        """
        src = Path(src)
        dst = Path(dst)

        if not src.exists():
            raise IOError(f"Source does not exist: {src}")

        if dst.exists() and not overwrite:
            raise IOError(f"Destination exists: {dst}")

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return dst
        except Exception as e:
            raise IOError(f"Failed to move {src} to {dst}: {e}")

    @staticmethod
    def copy_path(
        src: PathLike,
        dst: PathLike,
        overwrite: bool = False,
        follow_links: bool = True,
    ) -> Path:
        """Safely copy path.

        Args:
            src: Source path
            dst: Destination path
            overwrite: Overwrite existing destination
            follow_links: Follow symbolic links
        """
        src = Path(src)
        dst = Path(dst)

        if not src.exists():
            raise IOError(f"Source does not exist: {src}")

        if dst.exists() and not overwrite:
            raise IOError(f"Destination exists: {dst}")

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(
                    src,
                    dst,
                    symlinks=not follow_links,
                    dirs_exist_ok=overwrite,
                )
            else:
                shutil.copy2(src, dst, follow_symlinks=follow_links)
            return dst
        except Exception as e:
            raise IOError(f"Failed to copy {src} to {dst}: {e}")

    @staticmethod
    def remove_path(
        path: PathLike, recursive: bool = False, ignore_errors: bool = False
    ) -> None:
        """Safely remove path.

        Args:
            path: Path to remove
            recursive: Remove directories recursively
            ignore_errors: Ignore removal errors
        """
        path = Path(path)
        try:
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=ignore_errors)
            elif path.is_dir():
                if recursive:
                    shutil.rmtree(path, ignore_errors=ignore_errors)
                else:
                    path.rmdir()
        except Exception as e:
            if not ignore_errors:
                raise IOError(f"Failed to remove {path}: {e}")

    @staticmethod
    def get_path_info(path: PathLike) -> PathInfo:
        """Get path information.

        Args:
            path: Path to inspect

        Returns:
            PathInfo object
        """
        return PathInfo.from_path(path)

    @staticmethod
    def get_tree_size(path: PathLike) -> Tuple[int, int]:
        """Get total size of directory tree.

        Args:
            path: Root path

        Returns:
            Tuple of (total_size, file_count)
        """
        path = Path(path)
        if path.is_file():
            return path.stat().st_size, 1

        total_size = 0
        file_count = 0

        for entry in path.rglob("*"):
            if entry.is_file():
                stat = entry.stat()
                total_size += stat.st_size
                file_count += 1

        return total_size, file_count

    @staticmethod
    def find_duplicates(
        directory: PathLike, by_content: bool = True, chunk_size: int = 8192
    ) -> List[List[Path]]:
        """Find duplicate files.

        Args:
            directory: Directory to scan
            by_content: Compare file contents
            chunk_size: Content comparison chunk size

        Returns:
            List of duplicate file groups
        """
        from hashlib import sha256

        def get_file_hash(path: Path) -> str:
            """Calculate file hash."""
            hasher = sha256()
            with path.open("rb") as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()

        # Group files by size first
        size_groups = {}
        for path in Path(directory).rglob("*"):
            if path.is_file():
                size = path.stat().st_size
                size_groups.setdefault(size, []).append(path)

        # Find duplicates
        duplicates = []
        for paths in size_groups.values():
            if len(paths) > 1:
                if by_content:
                    # Group by content hash
                    hash_groups = {}
                    for path in paths:
                        file_hash = get_file_hash(path)
                        hash_groups.setdefault(file_hash, []).append(path)

                    # Add groups with duplicates
                    duplicates.extend(
                        group
                        for group in hash_groups.values()
                        if len(group) > 1
                    )
                else:
                    duplicates.append(paths)

        return duplicates

    @staticmethod
    def is_path_accessible(path: PathLike, mode: str = "r") -> bool:
        """Check if path is accessible.

        Args:
            path: Path to check
            mode: Access mode ('r', 'w', or 'x')

        Returns:
            True if path is accessible
        """
        path = Path(path)
        try:
            if mode == "r":
                return os.access(path, os.R_OK)
            elif mode == "w":
                return os.access(path, os.W_OK)
            elif mode == "x":
                return os.access(path, os.X_OK)
            else:
                raise ValueError(f"Invalid access mode: {mode}")
        except Exception:
            return False

    @staticmethod
    def make_path_relative(
        paths: Union[PathLike, List[PathLike]],
        root: Optional[PathLike] = None,
        strict: bool = True,
    ) -> Union[Path, List[Path]]:
        """Make paths relative to root.

        Args:
            paths: Path(s) to convert
            root: Root path (default: current directory)
            strict: Enforce paths are under root

        Returns:
            Relative path(s)
        """
        if isinstance(paths, (str, Path)):
            return PathUtils.relative_path(paths, root, strict)

        return [PathUtils.relative_path(p, root, strict) for p in paths]

    @staticmethod
    def is_subpath(
        child: PathLike, parent: PathLike, strict: bool = True
    ) -> bool:
        """Check if path is subpath of parent.

        Args:
            child: Path to check
            parent: Parent path
            strict: Disallow same path
        """
        try:
            child = Path(child).resolve()
            parent = Path(parent).resolve()

            if strict and child == parent:
                return False

            return str(parent) in str(child)
        except Exception:
            return False

    @staticmethod
    def get_common_prefix(paths: List[PathLike]) -> Optional[Path]:
        """Get common prefix path.

        Args:
            paths: Paths to compare

        Returns:
            Common prefix path or None
        """
        if not paths:
            return None

        paths = [Path(p).resolve() for p in paths]
        prefix = str(paths[0])

        for path in paths[1:]:
            while prefix and not str(path).startswith(prefix):
                prefix = str(Path(prefix).parent)
                if not prefix:
                    return None

        return Path(prefix) if prefix else None

    @staticmethod
    def filter_paths(
        paths: List[PathLike],
        *,
        files_only: bool = False,
        dirs_only: bool = False,
        links_only: bool = False,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        exclude_patterns: Optional[Set[str]] = None,
        include_patterns: Optional[Set[str]] = None,
    ) -> List[Path]:
        """Filter paths based on criteria.

        Args:
            paths: Paths to filter
            files_only: Only include files
            dirs_only: Only include directories
            links_only: Only include symbolic links
            min_size: Minimum size in bytes
            max_size: Maximum size in bytes
            exclude_patterns: Patterns to exclude
            include_patterns: Patterns to include

        Returns:
            Filtered paths
        """
        result = []
        exclude_patterns = exclude_patterns or set()
        include_patterns = include_patterns or {"*"}

        for path in paths:
            path = Path(path)

            # Check type
            if files_only and not path.is_file():
                continue
            if dirs_only and not path.is_dir():
                continue
            if links_only and not path.is_symlink():
                continue

            # Check size
            if path.is_file():
                size = path.stat().st_size
                if min_size is not None and size < min_size:
                    continue
                if max_size is not None and size > max_size:
                    continue

            # Check patterns
            str_path = str(path)
            if any(re.search(p, str_path) for p in exclude_patterns):
                continue

            if not any(re.search(p, str_path) for p in include_patterns):
                continue

            result.append(path)

        return result

    @staticmethod
    def set_path_permissions(
        path: PathLike, mode: int, recursive: bool = False
    ) -> None:
        """Set path permissions.

        Args:
            path: Path to modify
            mode: Permission mode (octal)
            recursive: Apply recursively
        """
        path = Path(path)
        try:
            if recursive and path.is_dir():
                for item in path.rglob("*"):
                    item.chmod(mode)
            path.chmod(mode)
        except Exception as e:
            raise IOError(f"Failed to set permissions on {path}: {e}")

    @staticmethod
    def watch_path(
        path: PathLike,
        patterns: Optional[Set[str]] = None,
        recursive: bool = False,
    ) -> Iterator[Tuple[str, Path]]:
        """Watch path for changes.

        Args:
            path: Path to watch
            patterns: Patterns to match
            recursive: Watch recursively

        Yields:
            Tuples of (event_type, path)

        Note:
            Requires watchdog package
        """
        try:
            from watchdog.observers import Observer  # type: ignore
            from watchdog.events import (  # type: ignore
                FileSystemEventHandler,
                FileSystemEvent,
            )
        except ImportError:
            raise ImportError("watchdog package required for path watching")

        class Handler(FileSystemEventHandler):
            def __init__(
                self, patterns: Optional[Set[str]], queue: asyncio.Queue
            ):
                self.patterns = patterns
                self.queue = queue

            def on_any_event(self, event: FileSystemEvent) -> None:
                if not event.is_directory:
                    path = Path(event.src_path)
                    if not self.patterns or any(
                        path.match(p) for p in self.patterns
                    ):
                        self.queue.put_nowait((event.event_type, path))

        path = Path(path)
        if not path.exists():
            raise IOError(f"Path does not exist: {path}")

        queue: asyncio.Queue = asyncio.Queue()
        observer = Observer()
        handler = Handler(patterns, queue)

        observer.schedule(handler, str(path), recursive=recursive)
        observer.start()

        try:
            while True:
                event = yield queue.get()
                queue.task_done()
        finally:
            observer.stop()
            observer.join()

    @staticmethod
    def compress_paths(
        paths: List[PathLike],
        archive_path: PathLike,
        format: str = "zip",
        compression: int = 9,
    ) -> Path:
        """Compress paths into archive.

        Args:
            paths: Paths to compress
            archive_path: Output archive path
            format: Archive format ('zip' or 'tar')
            compression: Compression level (0-9)
        """
        archive_path = Path(archive_path)
        paths = [Path(p) for p in paths]

        try:
            if format == "zip":
                import zipfile

                with zipfile.ZipFile(
                    archive_path,
                    "w",
                    compression=zipfile.ZIP_DEFLATED,
                    compresslevel=compression,
                ) as zf:
                    for path in paths:
                        if path.is_file():
                            zf.write(path)
                        elif path.is_dir():
                            for file in path.rglob("*"):
                                if file.is_file():
                                    zf.write(file)
            elif format == "tar":
                import tarfile

                with tarfile.open(
                    archive_path, f"w:gz", compresslevel=compression
                ) as tf:
                    for path in paths:
                        tf.add(path)
            else:
                raise ValueError(f"Invalid archive format: {format}")

            return archive_path
        except Exception as e:
            raise IOError(f"Failed to create archive: {e}")

    @staticmethod
    def extract_archive(
        archive_path: PathLike,
        extract_path: PathLike,
        format: Optional[str] = None,
    ) -> Path:
        """Extract archive contents.

        Args:
            archive_path: Archive path
            extract_path: Extraction path
            format: Archive format (autodetect if None)
        """
        archive_path = Path(archive_path)
        extract_path = Path(extract_path)

        if not archive_path.exists():
            raise IOError(f"Archive not found: {archive_path}")

        # Autodetect format
        if format is None:
            suffix = archive_path.suffix.lower()
            if suffix in {".zip", ".jar", ".war"}:
                format = "zip"
            elif suffix in {".tar", ".gz", ".bz2", ".xz"}:
                format = "tar"
            else:
                raise ValueError(f"Cannot detect archive format: {suffix}")

        try:
            extract_path.mkdir(parents=True, exist_ok=True)

            if format == "zip":
                import zipfile

                with zipfile.ZipFile(archive_path) as zf:
                    zf.extractall(extract_path)
            elif format == "tar":
                import tarfile

                with tarfile.open(archive_path) as tf:
                    tf.extractall(extract_path)
            else:
                raise ValueError(f"Invalid archive format: {format}")

            return extract_path
        except Exception as e:
            raise IOError(f"Failed to extract archive: {e}")
