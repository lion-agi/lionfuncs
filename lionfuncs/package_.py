"""
Comprehensive package management utilities for Python environments.

Features:
- Package installation and import handling
- Package version and status checking
- System architecture detection
- Safe import operations
- Installation management
"""

import importlib.metadata
import importlib.util
import logging
import platform
import subprocess
from typing import Any, List, Optional, Union

from lionfuncs.utils import run_pip_command


def import_module(
    package_name: str,
    module_name: Optional[str] = None,
    import_name: Optional[Union[str, List[str]]] = None,
) -> Any:
    """
    Import a module by its path.

    Args:
        package_name: Base package name.
        module_name: Specific module to import.
        import_name: Specific name(s) to import.

    Returns:
        The imported module or attribute(s).

    Example:
        >>> np = import_module('numpy', import_name='array')
        >>> isinstance(np, type)
        True
    """
    try:
        full_import_path = (
            f"{package_name}.{module_name}" if module_name else package_name
        )

        if import_name:
            import_name = (
                [import_name]
                if not isinstance(import_name, list)
                else import_name
            )
            module = __import__(
                full_import_path,
                fromlist=import_name,
            )
            if len(import_name) == 1:
                return getattr(module, import_name[0])
            return [getattr(module, name) for name in import_name]
        else:
            return __import__(full_import_path)

    except ImportError as e:
        raise ImportError(
            f"Failed to import module {full_import_path}: {e}"
        ) from e


def install_import(
    package_name: str,
    module_name: Optional[str] = None,
    import_name: Optional[str] = None,
    pip_name: Optional[str] = None,
) -> Any:
    """
    Attempt to import a package, installing if not found.

    Args:
        package_name: Package to import.
        module_name: Specific module to import.
        import_name: Specific name to import.
        pip_name: Alternative pip installation name.

    Returns:
        Imported module or attribute.

    Example:
        >>> module = install_import('pandas')
        >>> hasattr(module, 'DataFrame')
        True
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


def check_import(
    package_name: str,
    module_name: Optional[str] = None,
    import_name: Optional[str] = None,
    pip_name: Optional[str] = None,
    attempt_install: bool = True,
    error_message: str = "",
) -> Any:
    """
    Check if package is installed, attempt installation if not.

    Args:
        package_name: Package to check.
        module_name: Specific module to import.
        import_name: Specific name to import.
        pip_name: Alternative pip name.
        attempt_install: Whether to try installation.
        error_message: Custom error message.

    Returns:
        Imported module or attribute.

    Example:
        >>> module = check_import('numpy', import_name='array')
        >>> callable(module)
        True
    """
    if not is_import_installed(package_name):
        if attempt_install:
            logging.info(
                f"Package {package_name} not found. Attempting installation."
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
            msg = f"Package {package_name} not found. {error_message}"
            logging.info(msg)
            raise ImportError(msg)

    return import_module(
        package_name=package_name,
        module_name=module_name,
        import_name=import_name,
    )


def is_import_installed(package_name: str) -> bool:
    """
    Check if a package is installed.

    Args:
        package_name: Package to check.

    Returns:
        True if installed, False otherwise.
    """
    try:
        return importlib.util.find_spec(package_name) is not None
    except Exception as e:
        logging.error(f"Error checking package {package_name}: {e}")
        return False


def list_installed_packages() -> List[str]:
    """Get list of installed packages."""
    try:
        return [
            dist.metadata["Name"]
            for dist in importlib.metadata.distributions()
        ]
    except Exception as e:
        logging.error(f"Failed to list installed packages: {e}")
        return []


def update_package(package_name: str) -> None:
    """Update specified package."""
    try:
        run_pip_command(["install", "--upgrade", package_name])
        logging.info(f"Successfully updated {package_name}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to update {package_name}: {e}")
        raise


def uninstall_package(package_name: str) -> None:
    """Uninstall specified package."""
    try:
        run_pip_command(["uninstall", package_name, "-y"])
        logging.info(f"Successfully uninstalled {package_name}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to uninstall {package_name}: {e}")
        raise


def get_package_version(package_name: str) -> str:
    """Get installed version of package."""
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        logging.warning(f"Package {package_name} not found")
        return ""
    except Exception as e:
        logging.error(f"Error getting version for {package_name}: {e}")
        return ""


def get_cpu_architecture() -> str:
    """
    Get CPU architecture.

    Returns:
        'arm64' for ARM, 'x86_64' for Intel/AMD 64-bit, or actual architecture.
    """
    arch: str = platform.machine().lower()
    if "arm" in arch or "aarch64" in arch:
        return "arm64"
    elif "x86_64" in arch or "amd64" in arch:
        return "x86_64"
    return arch


__all__ = [
    "import_module",
    "install_import",
    "check_import",
    "is_import_installed",
    "list_installed_packages",
    "update_package",
    "uninstall_package",
    "get_package_version",
    "get_cpu_architecture",
]
