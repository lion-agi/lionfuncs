import logging
import re
from pathlib import Path


def clear_path(
    path: Path | str,
    /,
    recursive: bool = False,
    exclude: list[str] | None = None,
) -> None:
    """
    Clear all files and directories in the specified path.

    Args:
        path: The path to the directory to clear.
        recursive: If True, clears directories recursively.
        exclude: A list of string patterns to exclude from deletion.

    Raises:
        FileNotFoundError: If the specified directory does not exist.
        PermissionError: If there are insufficient permissions to delete
            files.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"The specified directory {path} does not exist."
        )

    exclude = exclude or []
    exclude_pattern = re.compile("|".join(exclude)) if exclude else None

    for file_path in path.iterdir():
        if exclude_pattern and exclude_pattern.search(file_path.name):
            logging.info(f"Excluded from deletion: {file_path}")
            continue

        try:
            if file_path.is_dir():
                if recursive:
                    clear_path(file_path, recursive=True, exclude=exclude)
                    file_path.rmdir()
                else:
                    continue
            else:
                file_path.unlink()
            logging.info(f"Successfully deleted {file_path}")
        except PermissionError as e:
            logging.error(f"Permission denied when deleting {file_path}: {e}")
        except Exception as e:
            logging.error(f"Failed to delete {file_path}: {e}")
