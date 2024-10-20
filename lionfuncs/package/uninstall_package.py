import logging
import subprocess

from lionfuncs.utils import run_pip_command


def uninstall_package(package_name: str) -> None:
    """
    Uninstall a specified package.

    Args:
        package_name: The name of the package to uninstall.

    Raises:
        subprocess.CalledProcessError: If the uninstallation fails.
    """
    try:
        run_pip_command(["uninstall", package_name, "-y"])
        logging.info(f"Successfully uninstalled {package_name}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to uninstall {package_name}. Error: {e}")
        raise
