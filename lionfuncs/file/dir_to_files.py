"""File processing utilities for bulk operations.

This module provides utilities for processing multiple files and chunking
file contents, with support for concurrent operations and progress tracking.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Union


def dir_to_files(
    directory: Union[str, Path],
    file_types: Optional[List[str]] = None,
    max_workers: Optional[int] = None,
    ignore_errors: bool = False,
    verbose: bool = False,
) -> List[Path]:
    """Process directory and return matching files.

    Recursively processes a directory to find files matching specified types.
    Supports concurrent processing for large directories.

    Args:
        directory: Directory to process.
        file_types: List of file extensions (e.g., ['.txt', '.pdf']).
        max_workers: Maximum number of concurrent workers.
        ignore_errors: Continue on errors if True.
        verbose: Enable detailed logging.

    Returns:
        List of matching file paths.

    Raises:
        ValueError: Invalid directory or processing error.

    Examples:
        >>> files = dir_to_files('/data', ['.txt'], verbose=True)
        >>> print(len(files), 'text files found')
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"Invalid directory: {directory}")

    if file_types:
        file_types = [t if t.startswith(".") else f".{t}" for t in file_types]

    def process_file(path: Path) -> Optional[Path]:
        """Process single file with error handling."""
        try:
            if file_types is None or path.suffix in file_types:
                if verbose:
                    logging.info(f"Found matching file: {path}")
                return path
        except Exception as e:
            if ignore_errors:
                if verbose:
                    logging.warning(f"Error processing {path}: {e}")
            else:
                raise ValueError(f"Error processing {path}: {e}") from e
        return None

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(process_file, f)
                for f in directory.rglob("*")
                if f.is_file()
            ]

            files = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        files.append(result)
                except Exception as e:
                    if not ignore_errors:
                        raise
                    if verbose:
                        logging.warning(f"Error in file processing: {e}")

        if verbose:
            logging.info(f"Found {len(files)} matching files in {directory}")
        return files

    except Exception as e:
        raise ValueError(f"Error processing directory {directory}: {e}")


__all__ = [
    "dir_to_files",
    "file_to_chunks",
]
