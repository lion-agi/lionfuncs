import importlib.metadata
import logging


def list_installed_packages() -> list[str]:
    """
    List all installed packages.

    Returns:
        List[str]: A list of names of installed packages.
    """
    try:
        return [
            dist.metadata["Name"]
            for dist in importlib.metadata.distributions()
        ]
    except Exception as e:
        logging.error(f"Failed to list installed packages: {e}")
        return []
