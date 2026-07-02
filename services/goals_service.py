"""Lógica de negocio del módulo Objetivos."""
from __future__ import annotations

import datetime as dt

import pandas as pd

from config.settings import SHEET_GOALS
from database.repository import SheetRepository
from utils.formatters import now_str, parse_date
from utils.helpers import safe_float


class GoalsService:
    def __init__(self):
        self.repo = SheetRepository(SHEET_GOALS)

    def list_goals(self) -> pd.DataFrame:
        df = self.repo.fetch_all()
        if df.empty:
            return df
        df = df.copy()
        df["meta_num"] = df["meta"].apply(safe_float)
        df["valor_num"] = df["valor_actual"].apply(safe_float)
        df["progreso"] = df.apply(
            lambda r: min(round((r["valor_num"] / r["meta_num"]) * 100, 1), 100)
            if r["meta_num"]
            else 0.0,
            axis=1,
        )
        return df

    def create_goal(self, data: dict, created_by: str) -> str:
        data.setdefault("valor_actual", 0)
        data.setdefault("estado", "En progreso")
        data["created_by"] = created_by
        data["created_at"] = now_str()
        return self.repo.create(data)

    def update_goal(self, record_id: str, data: dict) -> bool:
        return self.repo.update(record_id, data)

    def update_progress(self, record_id: str, valor_actual: float) -> bool:
        return self.repo.update(record_id, {"valor_actual": valor_actual})

    def delete_goal(self, record_id: str) -> bool:
        return self.repo.delete(record_id)

    def duplicate_goal(self, record_id: str) -> str | None:
        return self.repo.duplicate(record_id)

    @staticmethod
    def status_color(row: pd.Series) -> str:
        deadline = parse_date(row.get("fecha_limite"))
        progreso = row.get("progreso", 0)
        if progreso >= 100:
            return "success"
        if deadline and deadline < dt.date.today():
            return "danger"
        if deadline and (deadline - dt.date.today()).days <= 7:
            return "warning"
        return "info"

    def days_to_finish_at_current_pace(self, row: pd.Series) -> int | None:
        """Estima días restantes según el ritmo actual (para Insights)."""
        created = parse_date(row.get("created_at"))
        if not created or row.get("valor_num", 0) <= 0:
            return None
        days_elapsed = max((dt.date.today() - created).days, 1)
        pace = row["valor_num"] / days_elapsed
        remaining = row["meta_num"] - row["valor_num"]
        if pace <= 0:
            return None
        return int(remaining / pace)
