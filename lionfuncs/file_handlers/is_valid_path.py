import re
import sys
from pathlib import Path


def is_valid_path(path_str):
    """
    Validates whether the given path string is syntactically
    valid for the current operating system.

    Args:
        path_str (str): The filesystem path to validate.

    Returns:
        bool: True if the path is valid, False otherwise.

    Raises:
        ValueError: If the path is invalid, with an explanation.
    """
    if isinstance(path_str, Path):
        path_str = str(path_str)

    if not isinstance(path_str, str):
        raise TypeError("Path must be a string.")

    if not path_str:
        raise ValueError("Path cannot be an empty string.")

    # Determine the current operating system
    is_windows = sys.platform.startswith("win")
    if is_windows:
        # Windows-specific validation

        # 1. Check for invalid characters
        # Invalid characters: < > : " / \ | ? *
        invalid_chars = r'<>:"/\\|?*'
        if re.search(f"[{re.escape(invalid_chars)}]", path_str):
            raise ValueError(
                f"Path contains invalid characters: {invalid_chars}"
            )

        # 2. Check for reserved names in each path component
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

        path = Path(path_str)
        for part in path.parts:
            # Remove trailing dots and spaces (Windows ignores them)
            name = part.upper().rstrip(". ")
            if name in reserved_names:
                raise ValueError(
                    f"Path contains a reserved name in component: '{part}'"
                )

        # 3. Check for path length
        # Traditional MAX_PATH is 260 characters.
        # Modern Windows can handle longer paths with Unicode prefix.
        # Here, we'll enforce the traditional limit.
        if len(path_str) > 260:
            raise ValueError(
                "Path exceeds the maximum length of 260 characters on Windows."
            )

        # 4. Additional checks (optional)
        # For example, checking if the path ends with
        # a space or dot, which is invalid in Windows
        if path_str.endswith(" ") or path_str.endswith("."):
            raise ValueError(
                "Path cannot end with a space or a dot on Windows."
            )

    else:
        # Unix-like systems validation

        # 1. Check for null character
        if "\0" in path_str:
            raise ValueError(
                "Path contains a null character, "
                "which is invalid on Unix-like systems."
            )

        # 2. Check for path length
        # Common maximum path length on Unix is 4096 characters
        if len(path_str) > 4096:
            raise ValueError(
                "Path exceeds the maximum length of 4096"
                " characters on Unix-like systems."
            )

        # 3. Check for empty components (e.g., consecutive slashes)
        # Although Unix can handle multiple slashes,
        # you might want to enforce single separators
        if re.search(r"//+", path_str):
            raise ValueError(
                "Path contains consecutive slashes ('//'), "
                "which may be invalid in some contexts."
            )

        # 4. Optional: Check if path starts with a valid character
        # Typically, Unix paths start with '/', '~', or a
        # valid character for relative paths
        # This can be adjusted based on specific requirements
        if not re.match(r"^(/|~|\.|[^/])", path_str):
            raise ValueError("Path does not start with a valid character.")

    # If all checks pass
    return True
