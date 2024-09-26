from pathlib import Path


def get_file_size(path: Path | str) -> int:
    """
    Get the size of a file or total size of files in a directory.

    Args:
        path: The file or directory path.

    Returns:
        The size in bytes.

    Raises:
        FileNotFoundError: If the path does not exist.
        PermissionError: If there are insufficient permissions
            to access the path.
    """
    path = Path(path)
    try:
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(
                f.stat().st_size for f in path.rglob("*") if f.is_file()
            )
        else:
            raise FileNotFoundError(f"{path} does not exist.")
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied when accessing {path}"
        ) from e
