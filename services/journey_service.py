"""Lógica de negocio del módulo Journey (diario profesional)."""
from __future__ import annotations

import pandas as pd

from config.settings import SHEET_JOURNEY
from database.repository import SheetRepository
from utils.formatters import duration_hours, now_str, today_str
from utils.helpers import safe_float


class JourneyService:
    def __init__(self):
        self.repo = SheetRepository(SHEET_JOURNEY)

    def list_entries(self) -> pd.DataFrame:
        df = self.repo.fetch_all()
        if df.empty:
            return df
        df = df.copy()
        df["_fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
        return df.sort_values(["_fecha_dt", "hora_inicio"], ascending=[False, False])

    def create_entry(self, data: dict, created_by: str) -> str:
        if data.get("hora_inicio") and data.get("hora_fin"):
            duration = duration_hours(data["hora_inicio"], data["hora_fin"])
        else:
            duration = 0.0
        data.setdefault("hits", "1" if str(data.get("resultado", "")).strip() else "0")
        data["created_by"] = created_by
        data["created_at"] = now_str()
        data.setdefault("fecha", today_str())
        record_id = self.repo.create(data)
        return record_id

    def update_entry(self, record_id: str, data: dict) -> bool:
        return self.repo.update(record_id, data)

    def delete_entry(self, record_id: str) -> bool:
        return self.repo.delete(record_id)

    def duplicate_entry(self, record_id: str) -> str | None:
        return self.repo.duplicate(record_id)

    def today_entries(self) -> pd.DataFrame:
        df = self.list_entries()
        if df.empty:
            return df
        return df[df["fecha"] == today_str()]

    def total_hits(self, df: pd.DataFrame | None = None) -> int:
        df = df if df is not None else self.list_entries()
        if df.empty:
            return 0
        return int(df["hits"].apply(safe_float).sum())

    def total_income(self, df: pd.DataFrame | None = None) -> float:
        df = df if df is not None else self.list_entries()
        if df.empty:
            return 0.0
        return df["dinero_generado"].apply(safe_float).sum()
