import logging

from lionfuncs.import_handlers.import_module import import_module
from lionfuncs.import_handlers.install_import import install_import
from lionfuncs.import_handlers.is_import_installed import is_import_installed


def check_import(
    package_name: str,
    module_name: str | None = None,
    import_name: str | None = None,
    pip_name: str | None = None,
    attempt_install: bool = True,
    error_message: str = "",
):
    """
    Check if a package is installed, attempt to install if not.

    Args:
        package_name: The name of the package to check.
        module_name: The specific module to import (if any).
        import_name: The specific name to import from the module (if any).
        pip_name: The name to use for pip installation (if different).
        attempt_install: Whether to attempt installation if not found.
        error_message: Custom error message to use if package not found.

    Raises:
        ImportError: If the package is not found and not installed.
        ValueError: If the import fails after installation attempt.
    """
    if not is_import_installed(package_name):
        if attempt_install:
            logging.info(
                f"Package {package_name} not found. Attempting " "to install.",
            )
            try:
                return install_import(
                    package_name=package_name,
                    module_name=module_name,
                    import_name=import_name,
                    pip_name=pip_name,
                )
            except ImportError as e:
                raise ValueError(
                    f"Failed to install {package_name}: {e}"
                ) from e
        else:
            logging.info(
                f"Package {package_name} not found. {error_message}",
            )
            raise ImportError(
                f"Package {package_name} not found. {error_message}",
            )

    return import_module(
        package_name=package_name,
        module_name=module_name,
        import_name=import_name,
    )
