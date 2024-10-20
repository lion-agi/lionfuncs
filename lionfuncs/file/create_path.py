from datetime import datetime
from pathlib import Path
from typing import Any

from lionfuncs.utils import unique_hash


def create_path(
    directory: Path | str,
    filename: str,
    extension: str = None,
    timestamp: bool = False,
    dir_exist_ok: bool = True,
    file_exist_ok: bool = False,
    time_prefix: bool = False,
    timestamp_format: str | None = None,
    random_hash_digits: int = 0,
) -> Path:
    """
    Generate a new file path with optional timestamp and random hash.

    Args:
        directory: The directory where the file will be created.
        filename: The base name of the file to create.
        timestamp: If True, adds a timestamp to the filename.
        dir_exist_ok: If True, doesn't raise an error if the directory
            exists.
        file_exist_ok: If True, allows overwriting of existing files.
        time_prefix: If True, adds the timestamp as a prefix instead of
            a suffix.
        timestamp_format: Custom format for the timestamp.
        random_hash_digits: Number of digits for the random hash.

    Returns:
        The full path to the new or existing file.

    Raises:
        ValueError: If the filename contains illegal characters.
        FileExistsError: If the file exists and file_exist_ok is False.
    """
    if "/" in filename or "\\" in filename:
        raise ValueError("Filename cannot contain directory separators.")
    directory = Path(directory)

    name, ext = None, None
    if "." in filename:
        name, ext = filename.rsplit(".", 1)
    else:
        name = filename
        ext = extension.strip(".").strip() if extension else None

    if not ext:
        raise ValueError("No extension provided for filename.")

    ext = f".{ext}" if ext else ""

    if timestamp:
        timestamp_str = datetime.now().strftime(
            timestamp_format or "%Y%m%d%H%M%S"
        )
        name = (
            f"{timestamp_str}_{name}"
            if time_prefix
            else f"{name}_{timestamp_str}"
        )

    if random_hash_digits > 0:
        random_hash = "-" + unique_hash(random_hash_digits)
        name = f"{name}{random_hash}"

    full_filename = f"{name}{ext}"
    full_path = directory / full_filename

    if full_path.exists():
        if file_exist_ok:
            return full_path
        raise FileExistsError(
            f"File {full_path} already exists and file_exist_ok is False."
        )
    full_path.parent.mkdir(parents=True, exist_ok=dir_exist_ok)
    return full_path


@staticmethod
def _get_path_kwargs(
    persist_path: str | Path, postfix: str, **path_kwargs: Any
) -> dict[str, Any]:
    """
    Generate keyword arguments for path creation.

    Args:
        persist_path: The base path to use.
        postfix: The file extension to use.
        **path_kwargs: Additional keyword arguments to override defaults.

    Returns:
        A dictionary of keyword arguments for path creation.
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
