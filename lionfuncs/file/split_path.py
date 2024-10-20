from pathlib import Path


@staticmethod
def split_path(path: Path | str) -> tuple[Path, str]:
    """
    Split a path into its directory and filename components.

    Args:
        path: The path to split.

    Returns:
        A tuple containing the directory and filename.
    """
    path = Path(path)
    return path.parent, path.name
