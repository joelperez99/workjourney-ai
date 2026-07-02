"""Decoradores de cache reutilizados por los servicios."""
from __future__ import annotations

import streamlit as st

# TTL corto: los datos viven en Google Sheets y pueden cambiar por otros
# usuarios, pero no queremos golpear la API en cada rerender de Streamlit.
DEFAULT_TTL = 30


def cache_dataframe(ttl: int = DEFAULT_TTL):
    """Cachea funciones que devuelven DataFrames leídos de Google Sheets."""
    return st.cache_data(ttl=ttl, show_spinner=False)


def cache_resource():
    """Cachea recursos singleton (p.ej. el cliente de gspread)."""
    return st.cache_resource(show_spinner=False)
