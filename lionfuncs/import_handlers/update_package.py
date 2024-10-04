import logging
import subprocess

from lionfuncs.utils import run_pip_command


def update_package(package_name: str) -> None:
    """
    Update a specified package.

    Args:
        package_name: The name of the package to update.

    Raises:
        subprocess.CalledProcessError: If the update fails.
    """
    try:
        run_pip_command(["install", "--upgrade", package_name])
        logging.info(f"Successfully updated {package_name}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to update {package_name}. Error: {e}")
        raise
