"""Lógica de negocio del módulo Proyectos."""
from __future__ import annotations

import datetime as dt

import pandas as pd

from config.settings import SHEET_PROJECTS, SHEET_TIME
from database.repository import SheetRepository
from utils.formatters import now_str, parse_date
from utils.helpers import safe_float


class ProjectsService:
    def __init__(self):
        self.repo = SheetRepository(SHEET_PROJECTS)
        self.time_repo = SheetRepository(SHEET_TIME)

    def list_projects(self) -> pd.DataFrame:
        return self.repo.fetch_all()

    def project_names(self) -> list[str]:
        df = self.list_projects()
        return sorted([p for p in df.get("nombre", pd.Series(dtype=str)).unique() if p])

    def create_project(self, data: dict, created_by: str) -> str:
        data["created_by"] = created_by
        data["created_at"] = now_str()
        return self.repo.create(data)

    def update_project(self, record_id: str, data: dict) -> bool:
        return self.repo.update(record_id, data)

    def delete_project(self, record_id: str) -> bool:
        return self.repo.delete(record_id)

    def duplicate_project(self, record_id: str) -> str | None:
        return self.repo.duplicate(record_id)

    def project_stats(self) -> pd.DataFrame:
        """Rentabilidad, horas, tiempo restante, costo/hora y ROI por proyecto."""
        projects = self.list_projects()
        if projects.empty:
            return pd.DataFrame(
                columns=[
                    "id", "nombre", "cliente", "rentabilidad", "horas_reales",
                    "horas_restantes", "costo_hora", "roi", "dias_restantes",
                    "estado", "prioridad",
                ]
            )

        time_df = self.time_repo.fetch_all()
        rows = []
        today = dt.date.today()

        for _, project in projects.iterrows():
            name = project["nombre"]
            costo = safe_float(project.get("costo"))
            ingreso_real = safe_float(project.get("ingreso_real"))
            ingreso_esperado = safe_float(project.get("ingreso_esperado"))
            horas_estimadas = safe_float(project.get("horas_estimadas"))

            horas_reales = safe_float(project.get("horas_reales"))
            if not time_df.empty:
                tracked = (
                    time_df.loc[time_df["proyecto"] == name, "duracion_horas"]
                    .apply(safe_float)
                    .sum()
                )
                if tracked:
                    horas_reales = tracked

            rentabilidad = ingreso_real - costo
            costo_hora = (costo / horas_reales) if horas_reales else 0.0
            roi = ((ingreso_real - costo) / costo * 100) if costo else 0.0
            horas_restantes = max(horas_estimadas - horas_reales, 0.0)

            deadline = parse_date(project.get("deadline"))
            dias_restantes = (deadline - today).days if deadline else None

            rows.append(
                {
                    "id": project["id"],
                    "nombre": name,
                    "cliente": project.get("cliente", ""),
                    "rentabilidad": rentabilidad,
                    "ingreso_esperado": ingreso_esperado,
                    "ingreso_real": ingreso_real,
                    "horas_estimadas": horas_estimadas,
                    "horas_reales": horas_reales,
                    "horas_restantes": horas_restantes,
                    "costo_hora": costo_hora,
                    "roi": roi,
                    "dias_restantes": dias_restantes,
                    "estado": project.get("estado", ""),
                    "prioridad": project.get("prioridad", ""),
                    "deadline": project.get("deadline", ""),
                }
            )
        return pd.DataFrame(rows)
