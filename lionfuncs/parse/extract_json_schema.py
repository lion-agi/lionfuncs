"""
JSON schema extraction and manipulation utilities.

Features:
- Extract JSON schema from data
- Convert schema to CFG
- Convert schema to regex
- Handle nested structures
- Support custom configurations
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from lionfuncs.data.flatten import flatten


def extract_json_schema(
    data: Any,
    *,
    sep: str = "|",
    coerce_keys: bool = True,
    dynamic: bool = True,
    coerce_sequence: Optional[str] = None,
    max_depth: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Extract a JSON schema from data.

    Args:
        data: JSON data to extract schema from.
        sep: Separator for flattened keys.
        coerce_keys: Whether to coerce keys to strings.
        dynamic: Whether to use dynamic flattening.
        coerce_sequence: How to coerce sequences ("dict"/"list"/None).
        max_depth: Maximum flatten depth.

    Returns:
        Dictionary representing JSON schema.

    Example:
        >>> data = {"name": "test", "values": [1, 2, 3]}
        >>> schema = extract_json_schema(data)
        >>> schema["type"] == "object"
        True
    """
    flattened = flatten(
        data,
        sep=sep,
        coerce_keys=coerce_keys,
        dynamic=dynamic,
        coerce_sequence=coerce_sequence,
        max_depth=max_depth,
    )

    schema = {}
    for key, value in flattened.items():
        key_parts = key.split(sep) if isinstance(key, str) else key
        current = schema
        for part in key_parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[key_parts[-1]] = _get_type(value)

    return {"type": "object", "properties": _consolidate_schema(schema)}


def _get_type(value: Any) -> Dict[str, Any]:
    """Determine JSON schema type for a value."""
    if isinstance(value, str):
        return {"type": "string"}
    elif isinstance(value, bool):
        return {"type": "boolean"}
    elif isinstance(value, int):
        return {"type": "integer"}
    elif isinstance(value, float):
        return {"type": "number"}
    elif isinstance(value, list):
        if not value:
            return {"type": "array", "items": {}}
        item_types = [_get_type(item) for item in value]
        if all(item_type == item_types[0] for item_type in item_types):
            return {"type": "array", "items": item_types[0]}
        return {"type": "array", "items": {"oneOf": item_types}}
    elif isinstance(value, dict):
        return {
            "type": "object",
            "properties": _consolidate_schema(
                {k: _get_type(v) for k, v in value.items()}
            ),
        }
    elif value is None:
        return {"type": "null"}
    return {"type": "any"}


def _consolidate_schema(schema: Dict) -> Dict:
    """
    Consolidate schema handling lists and nested structures.

    Args:
        schema: Schema to consolidate.

    Returns:
        Consolidated schema.
    """
    consolidated = {}
    for key, value in schema.items():
        if isinstance(value, dict) and all(k.isdigit() for k in value.keys()):
            # Handle list structures
            item_types = list(value.values())
            if all(item_type == item_types[0] for item_type in item_types):
                consolidated[key] = {"type": "array", "items": item_types[0]}
            else:
                consolidated[key] = {
                    "type": "array",
                    "items": {"oneOf": item_types},
                }
        elif isinstance(value, dict) and "type" in value:
            consolidated[key] = value
        else:
            consolidated[key] = _consolidate_schema(value)
    return consolidated


def json_schema_to_cfg(
    schema: Dict[str, Any], start_symbol: str = "S"
) -> List[Tuple[str, List[str]]]:
    """
    Convert JSON schema to Context-Free Grammar.

    Args:
        schema: JSON schema to convert.
        start_symbol: Starting symbol for grammar.

    Returns:
        List of production rules.

    Example:
        >>> schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        >>> rules = json_schema_to_cfg(schema)
        >>> len(rules) > 0
        True
    """
    productions = []
    visited = set()
    symbol_counter = 0

    def generate_symbol(base: str) -> str:
        nonlocal symbol_counter
        symbol = "{}@{}".format(base, symbol_counter)
        symbol_counter += 1
        return symbol

    def generate_rules(s: Dict[str, Any], symbol: str) -> None:
        if symbol in visited:
            return
        visited.add(symbol)

        if s.get("type") == "object":
            _handle_object_rules(
                s, symbol, productions, generate_symbol, generate_rules
            )
        elif s.get("type") == "array":
            _handle_array_rules(
                s, symbol, productions, generate_symbol, generate_rules
            )
        else:
            _handle_primitive_rules(s, symbol, productions)

    generate_rules(schema, start_symbol)
    return productions


def _handle_object_rules(
    schema: Dict[str, Any],
    symbol: str,
    productions: List[Tuple[str, List[str]]],
    generate_symbol: Callable[[str], str],
    generate_rules: Callable[[Dict[str, Any], str], None],
) -> None:
    """Handle object type rules for CFG generation."""
    properties = schema.get("properties", {})
    if properties:
        props_symbol = generate_symbol("PROPS")
        productions.append((symbol, ["{", props_symbol, "}"]))
        productions.append((props_symbol, []))

        for i, prop in enumerate(properties):
            prop_symbol = generate_symbol(prop)
            if i == 0:
                productions.append((props_symbol, [prop_symbol]))
            else:
                productions.append(
                    (props_symbol, [props_symbol, ",", prop_symbol])
                )

        for prop, prop_schema in properties.items():
            prop_symbol = generate_symbol(prop)
            value_symbol = generate_symbol("VALUE")
            productions.append(
                (prop_symbol, ['"{}"'.format(prop), ":", value_symbol])
            )
            generate_rules(prop_schema, value_symbol)
    else:
        productions.append((symbol, ["{", "}"]))


def _handle_array_rules(
    schema: Dict[str, Any],
    symbol: str,
    productions: List[Tuple[str, List[str]]],
    generate_symbol: Callable[[str], str],
    generate_rules: Callable[[Dict[str, Any], str], None],
) -> None:
    """Handle array type rules for CFG generation."""
    items = schema.get("items", {})
    items_symbol = generate_symbol("ITEMS")
    value_symbol = generate_symbol("VALUE")
    productions.extend(
        [
            (symbol, ["[", "]"]),
            (symbol, ["[", items_symbol, "]"]),
            (items_symbol, [value_symbol]),
            (items_symbol, [value_symbol, ",", items_symbol]),
        ]
    )
    generate_rules(items, value_symbol)


def _handle_primitive_rules(
    schema: Dict[str, Any],
    symbol: str,
    productions: List[Tuple[str, List[str]]],
) -> None:
    """Handle primitive type rules for CFG generation."""
    type_map = {
        "string": "STRING",
        "number": "NUMBER",
        "integer": "INTEGER",
        "boolean": "BOOLEAN",
        "null": "NULL",
    }
    schema_type = schema.get("type")
    if schema_type in type_map:
        productions.append((symbol, [type_map[schema_type]]))


def json_schema_to_regex(schema: Dict[str, Any]) -> str:
    """
    Convert JSON schema to regular expression.

    Args:
        schema: JSON schema to convert.

    Returns:
        Regular expression pattern.

    Example:
        >>> schema = {"type": "object", "properties": {"age": {"type": "integer"}}}
        >>> pattern = json_schema_to_regex(schema)
        >>> len(pattern) > 0
        True
    """

    def schema_to_regex(s: Dict[str, Any]) -> str:
        schema_type = s.get("type")

        if schema_type == "object":
            return _handle_object_regex(s, schema_to_regex)
        elif schema_type == "array":
            return _handle_array_regex(s, schema_to_regex)
        else:
            return _handle_primitive_regex(schema_type)

    return "^" + schema_to_regex(schema) + "$"


def _handle_object_regex(
    schema: Dict[str, Any],
    schema_to_regex: Callable[[Dict[str, Any]], str],
) -> str:
    """Handle object type conversion to regex."""
    properties = schema.get("properties", {})
    prop_patterns = [
        r'"{}"\s*:\s*{}'.format(prop, schema_to_regex(prop_schema))
        for prop, prop_schema in properties.items()
    ]
    return (
        r"\{"
        + r"\s*("
        + r"|".join(prop_patterns)
        + r")"
        + r"(\s*,\s*("
        + r"|".join(prop_patterns)
        + r"))*\s*\}"
    )


def _handle_array_regex(
    schema: Dict[str, Any],
    schema_to_regex: Callable[[Dict[str, Any]], str],
) -> str:
    """Handle array type conversion to regex."""
    items = schema.get("items", {})
    items_pattern = schema_to_regex(items)
    return (
        r"\[\s*(" + items_pattern + r"(\s*,\s*" + items_pattern + r")*)?\s*\]"
    )


def _handle_primitive_regex(schema_type: str) -> str:
    """Handle primitive type conversion to regex."""
    type_patterns = {
        "string": r'"[^"]*"',
        "integer": r"-?\d+",
        "number": r"-?\d+(\.\d+)?",
        "boolean": r"(true|false)",
        "null": r"null",
    }
    return type_patterns.get(schema_type, r".*")


def print_cfg(productions: List[Tuple[str, List[str]]]) -> None:
    """Print CFG productions in readable format."""
    for lhs, rhs in productions:
        print("{} -> {}".format(lhs, " ".join(rhs)))


__all__ = [
    "extract_json_schema",
    "json_schema_to_cfg",
    "json_schema_to_regex",
    "print_cfg",
]
