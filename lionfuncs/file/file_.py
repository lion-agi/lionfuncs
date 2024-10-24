"""File operation utilities.

This module provides safe file operations including reading, writing, copying,
and size calculations. It ensures proper error handling and logging.
"""

from __future__ import annotations

import logging
import shutil
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Union


class SizeUnit(Enum):
    """Units for file size measurement."""

    BYTES = 1
    KB = 1024
    MB = 1024 * 1024
    GB = 1024 * 1024 * 1024
    TB = 1024 * 1024 * 1024 * 1024


def get_file_size(
    path: Union[Path, str],
    *,
    unit: SizeUnit = SizeUnit.BYTES,
    follow_links: bool = False,
) -> Union[int, float]:
    """Get size of file or directory.

    Args:
        path: File or directory path.
        unit: Size unit to return.
        follow_links: If True, follow symbolic links.

    Returns:
        Size in specified unit.

    Raises:
        FileNotFoundError: Path doesn't exist.
        PermissionError: Insufficient permissions.

    Examples:
        >>> get_file_size('file.txt')
        1024
        >>> get_file_size('file.txt', unit=SizeUnit.KB)
        1.0
    """
    path = Path(path)
    try:
        if path.is_file():
            size = path.stat().st_size
        elif path.is_dir():
            size = sum(
                f.stat().st_size
                for f in path.rglob("*")
                if f.is_file() and (follow_links or not f.is_symlink())
            )
        else:
            raise FileNotFoundError(f"{path} does not exist")

        return size if unit == SizeUnit.BYTES else size / unit.value
    except PermissionError as e:
        logging.error(f"Permission denied: {path}")
        raise


def get_file_size_info(
    path: Union[Path, str],
    follow_links: bool = False,
) -> Tuple[float, str]:
    """Get file size with appropriate unit.

    Args:
        path: File or directory path.
        follow_links: Follow symbolic links.

    Returns:
        Tuple of (size, unit_string).

    Examples:
        >>> get_file_size_info('file.txt')
        (1.0, 'KB')
    """
    size_bytes = get_file_size(path, follow_links=follow_links)

    for unit in reversed(list(SizeUnit)):
        if size_bytes >= unit.value:
            size = size_bytes / unit.value
            return size, unit.name

    return float(size_bytes), SizeUnit.BYTES.name


def read_file(path: Union[Path, str], /) -> str:
    """Read file contents safely.

    Args:
        path: Path to file.

    Returns:
        File contents as string.

    Raises:
        FileNotFoundError: File doesn't exist.
        PermissionError: Can't read file.

    Examples:
        >>> content = read_file('file.txt')
    """
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as e:
        logging.error(f"File not found: {path}")
        raise
    except PermissionError as e:
        logging.error(f"Permission denied: {path}")
        raise


def save_to_file(
    content: str,
    path: Union[Path, str],
    *,
    make_dirs: bool = True,
    overwrite: bool = False,
    verbose: bool = False,
) -> None:
    """Save content to file safely.

    Args:
        content: Content to write.
        path: Target file path.
        make_dirs: Create parent directories.
        overwrite: Allow overwriting existing file.
        verbose: Enable verbose logging.

    Raises:
        FileExistsError: File exists and overwrite=False.
        PermissionError: Can't write to path.

    Examples:
        >>> save_to_file("content", "file.txt")
    """
    path = Path(path)
    try:
        if path.exists() and not overwrite:
            raise FileExistsError(f"{path} exists")

        if make_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content, encoding="utf-8")

        if verbose:
            logging.info(f"Saved to {path}")
    except Exception as e:
        logging.error(f"Error saving to {path}: {e}")
        raise


def copy_file(
    src: Union[Path, str],
    dest: Union[Path, str],
    *,
    make_dirs: bool = True,
    overwrite: bool = False,
) -> None:
    """Copy file safely.

    Args:
        src: Source path.
        dest: Destination path.
        make_dirs: Create parent directories.
        overwrite: Allow overwriting existing file.

    Raises:
        FileNotFoundError: Source doesn't exist.
        FileExistsError: Destination exists and overwrite=False.

    Examples:
        >>> copy_file('src.txt', 'dest.txt')
    """
    src_path = Path(src)
    dest_path = Path(dest)

    if not src_path.is_file():
        raise FileNotFoundError(f"{src_path} not found")

    if dest_path.exists() and not overwrite:
        raise FileExistsError(f"{dest_path} exists")

    try:
        if make_dirs:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest_path)
    except Exception as e:
        logging.error(f"Error copying {src_path} to {dest_path}: {e}")
        raise


def clear_path(
    path: Union[Path, str],
    *,
    recursive: bool = False,
    exclude: Optional[List[str]] = None,
) -> None:
    """Clear files in directory.

    Args:
        path: Directory to clear.
        recursive: Clear subdirectories.
        exclude: Patterns to exclude.

    Raises:
        NotADirectoryError: Path not a directory.
        PermissionError: Can't delete files.

    Examples:
        >>> clear_path('/tmp/cache', recursive=True)
    """
    path = Path(path)
    if not path.is_dir():
        raise NotADirectoryError(f"{path} not a directory")

    exclude_pattern = None
    if exclude:
        import re

        exclude_pattern = re.compile("|".join(exclude))

    for item in path.iterdir():
        try:
            if exclude_pattern and exclude_pattern.search(str(item)):
                logging.info(f"Excluded: {item}")
                continue

            if item.is_file():
                item.unlink()
            elif item.is_dir() and recursive:
                clear_path(item, recursive=True, exclude=exclude)
                item.rmdir()

            logging.info(f"Removed: {item}")
        except Exception as e:
            logging.error(f"Error clearing {item}: {e}")
            raise


def list_files(
    directory: Union[Path, str],
    *,
    pattern: str = "*",
    recursive: bool = True,
) -> List[Path]:
    """List files in directory.

    Args:
        directory: Directory to scan.
        pattern: Glob pattern to match.
        recursive: Include subdirectories.

    Returns:
        List of file paths.

    Raises:
        NotADirectoryError: Path not a directory.

    Examples:
        >>> files = list_files('/data', pattern='*.txt')
    """
    path = Path(directory)
    if not path.is_dir():
        raise NotADirectoryError(f"{path} not a directory")

    glob_func = path.rglob if recursive else path.glob
    return [f for f in glob_func(pattern) if f.is_file()]


__all__ = [
    "SizeUnit",
    "get_file_size",
    "get_file_size_info",
    "read_file",
    "save_to_file",
    "copy_file",
    "clear_path",
    "list_files",
]
