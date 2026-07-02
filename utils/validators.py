"""Validaciones simples usadas en formularios."""
from __future__ import annotations

import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(value: str) -> bool:
    return bool(value) and bool(EMAIL_RE.match(value.strip()))


def is_non_empty(value: str) -> bool:
    return bool(value) and bool(str(value).strip())


def is_positive_number(value) -> bool:
    try:
        return float(value) >= 0
    except (TypeError, ValueError):
        return False


def validate_required_fields(data: dict, required: list[str]) -> list[str]:
    """Devuelve la lista de campos faltantes/vacíos."""
    missing = []
    for field in required:
        val = data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(field)
    return missing
