"""Utilidades genéricas compartidas por componentes, páginas y servicios."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st


def safe_float(value, default: float = 0.0) -> float:
    try:
        if value in (None, "", "nan"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default: int = 0) -> int:
    try:
        if value in (None, "", "nan"):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def inject_css(path: str | Path) -> None:
    """Inyecta un archivo CSS en la app de Streamlit."""
    css_path = Path(path)
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def filter_by_date_range(
    df: pd.DataFrame, date_col: str, start: dt.date, end: dt.date
) -> pd.DataFrame:
    if df.empty or date_col not in df.columns:
        return df
    dates = pd.to_datetime(df[date_col], errors="coerce").dt.date
    mask = (dates >= start) & (dates <= end)
    return df[mask]


def week_bounds(reference: dt.date | None = None) -> tuple[dt.date, dt.date]:
    reference = reference or dt.date.today()
    start = reference - dt.timedelta(days=reference.weekday())
    end = start + dt.timedelta(days=6)
    return start, end


def month_bounds(reference: dt.date | None = None) -> tuple[dt.date, dt.date]:
    reference = reference or dt.date.today()
    start = reference.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1) - dt.timedelta(days=1)
    else:
        end = start.replace(month=start.month + 1, day=1) - dt.timedelta(days=1)
    return start, end


def compute_streak(dates: list[dt.date]) -> int:
    """Calcula la racha de días consecutivos (hasta hoy) con actividad."""
    if not dates:
        return 0
    unique_dates = sorted(set(dates), reverse=True)
    today = dt.date.today()
    if unique_dates[0] not in (today, today - dt.timedelta(days=1)):
        return 0
    streak = 1
    for i in range(len(unique_dates) - 1):
        if (unique_dates[i] - unique_dates[i + 1]).days == 1:
            streak += 1
        else:
            break
    return streak


def badge_color_for_status(status: str) -> str:
    mapping = {
        "Pendiente": "warning",
        "En progreso": "info",
        "Completada": "success",
        "Cancelada": "danger",
        "Activo": "success",
        "Inactivo": "gray",
        "Pausado": "warning",
    }
    return mapping.get(status, "gray")
