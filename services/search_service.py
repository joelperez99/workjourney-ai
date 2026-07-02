"""Búsqueda global sobre todas las hojas de Google Sheets (Command Palette)."""
from __future__ import annotations

from config.settings import (
    SHEET_ACTIVITIES, SHEET_CLIENTS, SHEET_FINANCE, SHEET_GOALS,
    SHEET_JOURNEY, SHEET_PROJECTS,
)
from database.repository import SheetRepository

SEARCHABLE = {
    SHEET_JOURNEY: ("Journey", ["actividad", "descripcion", "resultado", "proyecto", "cliente"]),
    SHEET_ACTIVITIES: ("Actividades", ["titulo", "descripcion", "proyecto", "cliente"]),
    SHEET_CLIENTS: ("Clientes", ["nombre", "empresa", "correo"]),
    SHEET_PROJECTS: ("Proyectos", ["nombre", "cliente"]),
    SHEET_GOALS: ("Objetivos", ["objetivo", "descripcion"]),
    SHEET_FINANCE: ("Finanzas", ["cliente", "proyecto", "categoria", "referencia"]),
}


def global_search(query: str, limit_per_sheet: int = 5) -> list[dict]:
    """Busca `query` (case-insensitive) en las columnas de texto de cada hoja."""
    if not query or len(query.strip()) < 2:
        return []
    query = query.lower().strip()
    results: list[dict] = []

    for sheet_name, (label, columns) in SEARCHABLE.items():
        repo = SheetRepository(sheet_name)
        df = repo.fetch_all()
        if df.empty:
            continue
        mask = False
        for col in columns:
            if col in df.columns:
                col_mask = df[col].astype(str).str.lower().str.contains(query, na=False)
                mask = col_mask if mask is False else (mask | col_mask)
        if mask is False:
            continue
        matches = df[mask].head(limit_per_sheet)
        for _, row in matches.iterrows():
            preview_field = next((row[c] for c in columns if c in row and row[c]), "")
            results.append(
                {
                    "module": label,
                    "sheet": sheet_name,
                    "id": row.get("id", ""),
                    "preview": str(preview_field)[:80],
                }
            )
    return results
