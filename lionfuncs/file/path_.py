"""Path manipulation and validation utilities.

This module provides utilities for path operations including validation,
creation, and manipulation. It handles cross-platform compatibility and
provides consistent behavior across operating systems.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from lionfuncs.utils import unique_hash


def is_valid_path(
    path: Union[str, Path],
    *,
    max_length: Optional[int] = None,
    allow_relative: bool = True,
    allow_symlinks: bool = True,
    custom_reserved_names: Optional[List[str]] = None,
    strict_mode: bool = False,
) -> bool:
    """Validates whether a given path is syntactically valid.

    Args:
        path: The filesystem path to validate.
        max_length: Maximum allowed path length.
        allow_relative: Whether to allow relative paths.
        allow_symlinks: Whether to allow symbolic links.
        custom_reserved_names: Additional reserved names to check.
        strict_mode: If True, applies stricter validation.

    Returns:
        True if path is valid.

    Raises:
        TypeError: If path is neither string nor Path object.
        ValueError: If path is invalid, with explanation.

    Examples:
        >>> is_valid_path("/home/user/file.txt")
        True
        >>> is_valid_path("COM1.txt", strict_mode=True)
        ValueError: Invalid path: Path contains reserved name
    """
    if isinstance(path, Path):
        path_str = str(path)
    elif isinstance(path, str):
        path_str = path
    else:
        raise TypeError("Path must be string or Path object")

    if not path_str:
        raise ValueError("Path cannot be empty")

    issues = []
    is_windows = sys.platform.startswith("win")

    if "\0" in path_str:
        issues.append("Path contains null character")

    if not max_length:
        max_length = 260 if is_windows else 4096
    if len(path_str) > max_length:
        issues.append(f"Path exceeds {max_length} characters")

    if is_windows:
        invalid_chars = r'<>:"/\\|?*'
        if re.search(f"[{re.escape(invalid_chars)}]", path_str):
            issues.append(f"Invalid characters: {invalid_chars}")

        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *[f"COM{i}" for i in range(1, 10)],
            *[f"LPT{i}" for i in range(1, 10)],
        }
        if custom_reserved_names:
            reserved_names.update(custom_reserved_names)

        path = Path(path_str)
        for part in path.parts:
            name = part.upper().rstrip(". ")
            if name in reserved_names:
                issues.append(f"Reserved name: '{part}'")

        if path_str.endswith((" ", ".")):
            issues.append("Cannot end with space/period")

        if (
            strict_mode
            and not path_str.startswith("\\\\?\\")
            and len(path_str) > 260
        ):
            issues.append("Exceeds 260 chars without long path prefix")

    else:
        if strict_mode and re.search(r"//+", path_str):
            issues.append("Contains consecutive slashes")

        if not allow_relative and not path_str.startswith("/"):
            issues.append("Relative paths not allowed")

    if not allow_symlinks and Path(path_str).is_symlink():
        issues.append("Symlinks not allowed")

    if strict_mode and re.search(r"\s", path_str):
        issues.append("Contains whitespace")

    if issues:
        raise ValueError("Invalid path: " + "; ".join(issues))

    return True


def create_path(
    directory: Union[Path, str],
    filename: str,
    extension: Optional[str] = None,
    timestamp: bool = False,
    dir_exist_ok: bool = True,
    file_exist_ok: bool = False,
    time_prefix: bool = False,
    timestamp_format: Optional[str] = None,
    random_hash_digits: int = 0,
) -> Path:
    """Generate a new file path with optional features.

    Args:
        directory: Base directory for file.
        filename: Base filename.
        extension: File extension if not in filename.
        timestamp: Add timestamp to filename.
        dir_exist_ok: Allow existing directory.
        file_exist_ok: Allow existing file.
        time_prefix: Add timestamp as prefix.
        timestamp_format: Custom timestamp format.
        random_hash_digits: Add random hash digits.

    Returns:
        Path: Complete path for new file.

    Raises:
        ValueError: Invalid filename or missing extension.
        FileExistsError: File exists and not allowed.

    Examples:
        >>> create_path("/tmp", "test", "txt")
        PosixPath('/tmp/test.txt')
        >>> create_path("/tmp", "test.txt", timestamp=True)
        PosixPath('/tmp/test_20241024123456.txt')
    """
    if "/" in filename or "\\" in filename:
        raise ValueError("Filename cannot contain separators")

    directory = Path(directory)
    name, ext = None, None

    if "." in filename:
        name, ext = filename.rsplit(".", 1)
    else:
        name = filename
        ext = extension.strip(".") if extension else None

    if not ext:
        raise ValueError("No extension provided")

    ext = f".{ext}"

    if timestamp:
        ts = datetime.now().strftime(timestamp_format or "%Y%m%d%H%M%S")
        name = f"{ts}_{name}" if time_prefix else f"{name}_{ts}"

    if random_hash_digits:
        name = f"{name}-{unique_hash(random_hash_digits)}"

    path = directory / f"{name}{ext}"

    if path.exists() and not file_exist_ok:
        raise FileExistsError(f"{path} exists")

    path.parent.mkdir(parents=True, exist_ok=dir_exist_ok)
    return path


def split_path(path: Union[Path, str]) -> Tuple[Path, str]:
    """Split path into directory and filename.

    Args:
        path: Path to split.

    Returns:
        Tuple of (directory_path, filename).

    Examples:
        >>> split_path("/home/user/file.txt")
        (PosixPath('/home/user'), 'file.txt')
    """
    path = Path(path)
    return path.parent, path.name


def _get_path_kwargs(
    persist_path: Union[str, Path], postfix: str, **path_kwargs: Any
) -> Dict[str, Any]:
    """Generate keyword arguments for path creation.

    Internal helper function to process path creation arguments.

    Args:
        persist_path: Base path to use.
        postfix: File extension.
        **path_kwargs: Additional keyword arguments.

    Returns:
        Dictionary of keyword arguments.
    """
    persist_path = Path(persist_path)
    postfix = f".{postfix.strip('.')}"

    if persist_path.suffix != postfix:
        dirname = persist_path
        filename = f"new_file{postfix}"
    else:
        dirname, filename = persist_path.parent, persist_path.name

    return {
        "timestamp": path_kwargs.get("timestamp", False),
        "file_exist_ok": path_kwargs.get("file_exist_ok", True),
        "directory": path_kwargs.get("directory", dirname),
        "filename": path_kwargs.get("filename", filename),
    }


__all__ = [
    "is_valid_path",
    "create_path",
    "split_path",
]
