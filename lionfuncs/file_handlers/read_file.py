import logging
from pathlib import Path


def read_file(path: Path | str, /) -> str:
    """
    Read the contents of a file.

    Args:
        path: The path to the file to read.

    Returns:
        str: The contents of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If there are insufficient permissions to read
            the file.
    """
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as e:
        logging.error(f"File not found: {path}: {e}")
        raise
    except PermissionError as e:
        logging.error(f"Permission denied when reading file: {path}: {e}")
        raise
