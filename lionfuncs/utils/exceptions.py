"""Exception classes for the utility system."""


class UtilityError(Exception):
    """Base exception for utility errors."""

    pass


class ValidationError(UtilityError):
    """Validation related errors."""

    pass


class ConfigError(UtilityError):
    """Configuration related errors."""

    pass


class IOError(UtilityError):
    """IO operation related errors."""

    pass


class CacheError(UtilityError):
    """Cache operation related errors."""

    pass


class AsyncError(UtilityError):
    """Async operation related errors."""

    pass
