"""Funciones de formateo compartidas por toda la app (fechas, dinero, horas)."""
from __future__ import annotations

import datetime as dt
from typing import Any

from config.settings import DEFAULT_CURRENCY


def format_currency(value: Any, currency: str = DEFAULT_CURRENCY) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0
    symbol = "$" if currency in ("USD", "MXN") else currency
    return f"{symbol}{value:,.2f}"


def format_hours(value: Any) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0
    hours = int(value)
    minutes = int(round((value - hours) * 60))
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def format_percent(value: Any, decimals: int = 1) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0
    return f"{value:.{decimals}f}%"


def format_date(value: Any, fmt: str = "%d %b %Y") -> str:
    parsed = parse_date(value)
    return parsed.strftime(fmt) if parsed else "-"


def parse_date(value: Any) -> dt.date | None:
    if value in (None, "", "nan"):
        return None
    if isinstance(value, dt.date):
        return value
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(str(value), fmt).date()
        except ValueError:
            continue
    return None


def parse_datetime(value: Any) -> dt.datetime | None:
    if value in (None, "", "nan"):
        return None
    if isinstance(value, dt.datetime):
        return value
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return dt.datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return None


def duration_hours(start: str, end: str) -> float:
    """Calcula la duración en horas entre dos horas 'HH:MM'."""
    try:
        h1, m1 = map(int, str(start).split(":")[:2])
        h2, m2 = map(int, str(end).split(":")[:2])
        minutes = (h2 * 60 + m2) - (h1 * 60 + m1)
        if minutes < 0:
            minutes += 24 * 60
        return round(minutes / 60, 2)
    except (ValueError, AttributeError):
        return 0.0


def new_id(prefix: str = "") -> str:
    import uuid

    suffix = uuid.uuid4().hex[:10]
    return f"{prefix}{suffix}" if prefix else suffix


def now_str() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return dt.date.today().strftime("%Y-%m-%d")
