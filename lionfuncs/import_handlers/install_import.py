import logging
import subprocess

from lionfuncs.import_handlers.import_module import import_module
from lionfuncs.utils import run_pip_command


def install_import(
    package_name: str,
    module_name: str | None = None,
    import_name: str | None = None,
    pip_name: str | None = None,
):
    """
    Attempt to import a package, installing it if not found.

    Args:
        package_name: The name of the package to import.
        module_name: The specific module to import (if any).
        import_name: The specific name to import from the module (if any).
        pip_name: The name to use for pip installation (if different).

    Raises:
        ImportError: If the package cannot be imported or installed.
        subprocess.CalledProcessError: If pip installation fails.
    """
    pip_name = pip_name or package_name

    try:
        return import_module(
            package_name=package_name,
            module_name=module_name,
            import_name=import_name,
        )
    except ImportError:
        logging.info(f"Installing {pip_name}...")
        try:
            run_pip_command(["install", pip_name])
            return import_module(
                package_name=package_name,
                module_name=module_name,
                import_name=import_name,
            )
        except subprocess.CalledProcessError as e:
            raise ImportError(f"Failed to install {pip_name}: {e}") from e
        except ImportError as e:
            raise ImportError(
                f"Failed to import {pip_name} after installation: {e}"
            ) from e
