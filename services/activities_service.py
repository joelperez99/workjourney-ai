"""Lógica de negocio del módulo Actividades (data entry + kanban)."""
from __future__ import annotations

import pandas as pd

from config.settings import ESTADOS_ACTIVIDAD, SHEET_ACTIVITIES
from database.repository import SheetRepository
from utils.formatters import now_str, parse_datetime
from utils.helpers import safe_float


class ActivitiesService:
    def __init__(self):
        self.repo = SheetRepository(SHEET_ACTIVITIES)

    def list_activities(self) -> pd.DataFrame:
        return self.repo.fetch_all()

    def create_activity(self, data: dict, created_by: str) -> str:
        start = parse_datetime(data.get("inicio")) or None
        end = parse_datetime(data.get("fin")) or None
        if start and end:
            data["duracion_horas"] = round((end - start).total_seconds() / 3600, 2)
        else:
            data.setdefault("duracion_horas", 0)
        data.setdefault("status", "Pendiente")
        data["created_by"] = created_by
        data["created_at"] = now_str()
        return self.repo.create(data)

    def update_activity(self, record_id: str, data: dict) -> bool:
        start = parse_datetime(data.get("inicio")) if "inicio" in data else None
        end = parse_datetime(data.get("fin")) if "fin" in data else None
        if start and end:
            data["duracion_horas"] = round((end - start).total_seconds() / 3600, 2)
        return self.repo.update(record_id, data)

    def update_status(self, record_id: str, status: str) -> bool:
        return self.repo.update(record_id, {"status": status})

    def delete_activity(self, record_id: str) -> bool:
        return self.repo.delete(record_id)

    def duplicate_activity(self, record_id: str) -> str | None:
        return self.repo.duplicate(record_id)

    def kanban_columns(self) -> dict[str, pd.DataFrame]:
        df = self.list_activities()
        return {
            status: (df[df["status"] == status] if not df.empty else df)
            for status in ESTADOS_ACTIVIDAD
        }

    def total_dinero(self, df: pd.DataFrame | None = None) -> float:
        df = df if df is not None else self.list_activities()
        if df.empty:
            return 0.0
        return df["dinero_relacionado"].apply(safe_float).sum()

    def total_hits(self, df: pd.DataFrame | None = None) -> int:
        df = df if df is not None else self.list_activities()
        if df.empty:
            return 0
        return int((df["hit_conseguido"].astype(str).str.lower() == "sí").sum() +
                    (df["hit_conseguido"].astype(str).str.lower() == "si").sum())
