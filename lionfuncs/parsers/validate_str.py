from typing import Any

from lionfuncs.ln_undefined import LN_UNDEFINED
from lionfuncs.parsers.validate_mapping import validate_mapping


def validate_str(value: Any, field_name: str) -> str:

    value = value.strip() if isinstance(value, str) else str(value)
    if "{" in value or "}" in value:
        out = validate_mapping(
            value, field_name, handle_unmatched="ignore"
        ).get(field_name, LN_UNDEFINED)
        if out is LN_UNDEFINED:
            return ""
        else:
            return out.strip() if isinstance(out, str) else str(out).strip()

    return value
