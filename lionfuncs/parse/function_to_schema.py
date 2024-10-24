"""
Function schema generation utilities for OpenAI API compatibility.

Features:
- Generate OpenAI-compatible function schemas
- Parse function signatures and docstrings
- Extract parameter types and descriptions
- Support multiple docstring formats
"""

import inspect
from typing import Any, Dict, Optional, Union

from lionfuncs.parse.extract_docstring import extract_docstring
from lionfuncs.parse.utils import py_json_msp


def function_to_schema(
    f_: Any,
    style: str = "google",
    *,
    f_description: Optional[str] = None,
    p_description: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Generate OpenAI-compatible schema for a function.

    Generates schema using typing hints and docstrings, including function
    name, description, and parameter details in OpenAI function calling format.

    Args:
        f_: Function to generate schema for.
        style: Docstring format ('google' or 'reST').
        f_description: Custom function description.
        p_description: Custom parameter descriptions.

    Returns:
        Schema describing the function in OpenAI format.

    Example:
        >>> def example(param1: int) -> bool:
        ...     '''Example function.
        ...
        ...     Args:
        ...         param1: First parameter.
        ...     '''
        ...     return True
        >>> schema = function_to_schema(example)
        >>> schema['function']['name'] == 'example'
        True
    """
    # Extract function name
    func_name = f_.__name__

    # Extract descriptions if not provided
    if not f_description or not p_description:
        try:
            func_desc, params_desc = extract_docstring(f_, style)
            f_description = f_description or func_desc
            p_description = p_description or params_desc
        except Exception as e:
            raise ValueError(
                "Failed to extract docstring: {}".format(str(e))
            ) from e

    # Ensure p_description is a dict
    if p_description is None:
        p_description = {}

    # Extract parameter details
    parameters = _extract_parameters(f_, p_description)

    # Build schema in OpenAI format
    return {
        "type": "function",
        "function": {
            "name": func_name,
            "description": f_description,
            "parameters": parameters,
        },
    }


def _extract_parameters(
    func: Any, param_descriptions: Dict[str, str]
) -> Dict[str, Any]:
    """
    Extract parameter details from function signature.

    Args:
        func: Function to extract parameters from.
        param_descriptions: Dictionary of parameter descriptions.

    Returns:
        Parameter schema in OpenAI format.
    """
    try:
        sig = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            "Failed to extract function signature: {}".format(str(e))
        ) from e

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    for name, param in sig.parameters.items():
        # Get parameter type
        param_type = "string"  # default
        if param.annotation is not inspect.Parameter.empty:
            try:
                param_type = py_json_msp[param.annotation.__name__]
            except (KeyError, AttributeError):
                param_type = "string"  # fallback

        # Get parameter description
        param_description = param_descriptions.get(name, "")

        # Add to required parameters if no default value
        if param.default is inspect.Parameter.empty:
            parameters["required"].append(name)

        # Add parameter details
        parameters["properties"][name] = {
            "type": param_type,
            "description": param_description,
        }

    return parameters


__all__ = ["function_to_schema"]
