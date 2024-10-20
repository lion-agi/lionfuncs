import re
import sys
from pathlib import Path


def is_valid_path(
    path: str | Path,
    *,
    max_length: int | None = None,
    allow_relative: bool = True,
    allow_symlinks: bool = True,
    custom_reserved_names: list[str] | None = None,
    strict_mode: bool = False,
) -> bool:
    """
    Validates whether the given path is syntactically valid for the current operating system.

    Args:
        path (Union[str, Path]): The filesystem path to validate.
        max_length (Optional[int]): Maximum allowed path length. If None, uses OS default.
        allow_relative (bool): Whether to allow relative paths. Default is True.
        allow_symlinks (bool): Whether to allow symlinks. Default is True.
        custom_reserved_names (Optional[List[str]]): Additional reserved names to check.
        strict_mode (bool): If True, applies stricter validation rules. Default is False.

    Returns:
        bool: True if the path is valid, False otherwise.

    Raises:
        ValueError: If the path is invalid, with a detailed explanation.
    """
    if isinstance(path, Path):
        path_str = str(path)
    elif isinstance(path, str):
        path_str = path
    else:
        raise TypeError("Path must be a string or Path object.")

    if not path_str:
        raise ValueError("Path cannot be an empty string.")

    issues = []
    is_windows = sys.platform.startswith("win")

    # Common checks for both Windows and Unix-like systems
    if "\0" in path_str:
        issues.append("Path contains null character.")

    if not max_length:
        max_length = 260 if is_windows else 4096
    if len(path_str) > max_length:
        issues.append(
            f"Path exceeds the maximum length of {max_length} characters."
        )

    if is_windows:
        # Windows-specific validation
        invalid_chars = r'<>:"/\\|?*'
        if re.search(f"[{re.escape(invalid_chars)}]", path_str):
            issues.append(f"Path contains invalid characters: {invalid_chars}")

        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }
        if custom_reserved_names:
            reserved_names.update(custom_reserved_names)

        path = Path(path_str)
        for part in path.parts:
            name = part.upper().rstrip(". ")
            if name in reserved_names:
                issues.append(f"Path contains a reserved name: '{part}'")

        if path_str.endswith(" ") or path_str.endswith("."):
            issues.append(
                "Path cannot end with a space or a period on Windows."
            )

        if strict_mode:
            if not path_str.startswith("\\\\?\\") and len(path_str) > 260:
                issues.append(
                    "Path exceeds 260 characters without long path prefix."
                )

    else:
        # Unix-like systems validation
        if strict_mode:
            if re.search(r"//+", path_str):
                issues.append("Path contains consecutive slashes.")

        if not allow_relative and not path_str.startswith("/"):
            issues.append("Relative paths are not allowed.")

    # Common additional checks
    if not allow_symlinks and Path(path_str).is_symlink():
        issues.append("Symlinks are not allowed.")

    if strict_mode:
        if re.search(r"\s", path_str):
            issues.append("Path contains whitespace characters.")

    if issues:
        raise ValueError("Invalid path: " + "; ".join(issues))

    return True
