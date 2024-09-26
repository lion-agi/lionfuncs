from pathlib import Path
from shutil import copy2


def copy_file(src: Path | str, dest: Path | str) -> None:
    """
    Copy a file from a source path to a destination path.

    Args:
        src: The source file path.
        dest: The destination file path.

    Raises:
        FileNotFoundError: If the source file does not exist or is not
            a file.
        PermissionError: If there are insufficient permissions to copy
            the file.
        OSError: If there's an OS-level error during the copy operation.
    """
    src_path, dest_path = Path(src), Path(dest)
    if not src_path.is_file():
        raise FileNotFoundError(f"{src_path} does not exist or is not a file.")

    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        copy2(src_path, dest_path)
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied when copying {src_path} to {dest_path}"
        ) from e
    except OSError as e:
        raise OSError(f"Failed to copy {src_path} to {dest_path}: {e}") from e
