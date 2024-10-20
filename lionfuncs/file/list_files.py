from pathlib import Path


def list_files(
    dir_path: Path | str, extension: str | None = None
) -> list[Path]:
    """
    List all files in a specified directory with an optional extension
    filter, including files in subdirectories.

    Args:
        dir_path: The directory path where files are listed.
        extension: Filter files by extension.

    Returns:
        A list of Path objects representing files in the directory.

    Raises:
        NotADirectoryError: If the provided dir_path is not a directory.
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"{dir_path} is not a directory.")

    pattern = f"*.{extension}" if extension else "*"
    return [f for f in dir_path.rglob(pattern) if f.is_file()]
