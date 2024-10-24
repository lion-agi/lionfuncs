"""
Docstring parsing utilities for Python functions.

Features:
- Support for Google and reST docstring styles
- Function description extraction
- Parameter description parsing
- Robust parsing with edge case handling
- Clear type safety
"""

import inspect
from collections.abc import Callable
from typing import Dict, Optional, Tuple, Union


def extract_docstring(
    func: Callable,
    style: str = "google",
) -> Tuple[Optional[str], Dict[str, str]]:
    """
    Extract function description and parameter descriptions from docstring.

    Args:
        func: Function to parse docstring from.
        style: Docstring style ('google' or 'rest').

    Returns:
        Tuple of:
            - Function description (or None if no docstring)
            - Dict of parameter names to descriptions

    Raises:
        ValueError: If unsupported style is provided.

    Example:
        >>> def example(param1: int):
        ...     '''Example function.
        ...
        ...     Args:
        ...         param1: First parameter.
        ...     '''
        ...     pass
        >>> desc, params = extract_docstring(example)
        >>> desc
        'Example function.'
        >>> params
        {'param1': 'First parameter.'}
    """
    style = str(style).strip().lower()

    if style == "google":
        return _extract_docstring_details_google(func)
    elif style == "rest":
        return _extract_docstring_details_rest(func)
    else:
        raise ValueError(
            'Style must be "google" or "rest", got "{}"'.format(style)
        )


def _extract_docstring_details_google(
    func: Callable,
) -> Tuple[Optional[str], Dict[str, str]]:
    """
    Extract details from Google-style docstring.

    Args:
        func: Function to parse docstring from.

    Returns:
        Tuple of:
            - Function description (or None if no docstring)
            - Dict of parameter names to descriptions

    Example:
        >>> def example(param1: int):
        ...     '''Example function.
        ...
        ...     Args:
        ...         param1: First parameter.
        ...     '''
        ...     pass
        >>> desc, params = _extract_docstring_details_google(example)
        >>> desc
        'Example function.'
        >>> params
        {'param1': 'First parameter.'}
    """
    docstring = inspect.getdoc(func)
    if not docstring:
        return None, {}

    lines = docstring.split("\n")
    func_description = lines[0].strip()
    lines_len = len(lines)

    params_description: Dict[str, str] = {}

    # Find start of parameters section
    param_start_pos = 0
    for i in range(1, lines_len):
        line = str(lines[i]).strip().lower()
        if any(
            line.startswith(x)
            for x in ["args", "parameters", "params", "arguments"]
        ):
            param_start_pos = i + 1
            break

    # Parse parameters
    current_param = None
    for i in range(param_start_pos, lines_len):
        line = lines[i]
        if not line:
            continue
        elif line.startswith(" "):
            param_desc = line.split(":", 1)
            if len(param_desc) == 1:
                if current_param:
                    params_description[current_param] += " {}".format(
                        param_desc[0].strip()
                    )
                continue
            param, desc = param_desc
            param = param.split("(")[0].strip()
            params_description[param] = desc.strip()
            current_param = param
        else:
            break

    return func_description, params_description


def _extract_docstring_details_rest(
    func: Callable,
) -> Tuple[Optional[str], Dict[str, str]]:
    """
    Extract details from reStructuredText-style docstring.

    Args:
        func: Function to parse docstring from.

    Returns:
        Tuple of:
            - Function description (or None if no docstring)
            - Dict of parameter names to descriptions

    Example:
        >>> def example(param1: int):
        ...     '''Example function.
        ...
        ...     :param param1: First parameter
        ...     :type param1: int
        ...     '''
        ...     pass
        >>> desc, params = _extract_docstring_details_rest(example)
        >>> desc
        'Example function.'
        >>> params
        {'param1': 'First parameter'}
    """
    docstring = inspect.getdoc(func)
    if not docstring:
        return None, {}

    lines = docstring.split("\n")
    func_description = lines[0].strip()

    params_description: Dict[str, str] = {}
    current_param = None

    for line in lines[1:]:
        line = line.strip()
        if line.startswith(":param"):
            param_desc = line.split(":", 2)
            if len(param_desc) == 3:
                _, param, desc = param_desc
                param = param.split()[-1].strip()
                params_description[param] = desc.strip()
                current_param = param
        elif line.startswith(" ") and current_param:
            params_description[current_param] += " {}".format(line)

    return func_description, params_description


__all__ = ["extract_docstring"]
