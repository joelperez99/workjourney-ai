"""
Lógica de negocio del módulo Tiempo: temporizador start/pause/stop,
registro manual y agregaciones por cliente/proyecto/tipo.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from config.settings import SHEET_TIME
from database.repository import SheetRepository
from utils.formatters import now_str, today_str
from utils.helpers import safe_float

TIMER_KEY = "active_timer"


class TimeService:
    def __init__(self):
        self.repo = SheetRepository(SHEET_TIME)

    # ------------------------------------------------------------------
    # Temporizador (estado en session_state; se persiste al detener)
    # ------------------------------------------------------------------
    @staticmethod
    def start_timer(proyecto: str, cliente: str, actividad: str, tipo: str) -> None:
        st.session_state[TIMER_KEY] = {
            "proyecto": proyecto,
            "cliente": cliente,
            "actividad": actividad,
            "tipo": tipo,
            "start": dt.datetime.now(),
            "elapsed_before_pause": 0.0,
            "paused": False,
            "pause_started": None,
        }

    @staticmethod
    def pause_timer() -> None:
        timer = st.session_state.get(TIMER_KEY)
        if timer and not timer["paused"]:
            timer["paused"] = True
            timer["pause_started"] = dt.datetime.now()

    @staticmethod
    def resume_timer() -> None:
        timer = st.session_state.get(TIMER_KEY)
        if timer and timer["paused"]:
            pause_duration = (dt.datetime.now() - timer["pause_started"]).total_seconds()
            timer["elapsed_before_pause"] += pause_duration
            timer["paused"] = False
            timer["pause_started"] = None

    @staticmethod
    def get_elapsed_seconds() -> float:
        timer = st.session_state.get(TIMER_KEY)
        if not timer:
            return 0.0
        if timer["paused"]:
            end = timer["pause_started"]
        else:
            end = dt.datetime.now()
        return (end - timer["start"]).total_seconds() - timer["elapsed_before_pause"]

    def stop_timer(self, created_by: str, facturable: str = "Sí", notas: str = "") -> str | None:
        timer = st.session_state.get(TIMER_KEY)
        if not timer:
            return None
        elapsed_hours = round(self.get_elapsed_seconds() / 3600, 2)
        record_id = self.repo.create(
            {
                "fecha": today_str(),
                "proyecto": timer["proyecto"],
                "cliente": timer["cliente"],
                "actividad": timer["actividad"],
                "inicio": timer["start"].strftime("%H:%M"),
                "fin": dt.datetime.now().strftime("%H:%M"),
                "duracion_horas": elapsed_hours,
                "tipo": timer["tipo"],
                "facturable": facturable,
                "estado": "Completado",
                "notas": notas,
                "created_by": created_by,
                "created_at": now_str(),
            }
        )
        st.session_state.pop(TIMER_KEY, None)
        return record_id

    @staticmethod
    def has_active_timer() -> bool:
        return TIMER_KEY in st.session_state

    # ------------------------------------------------------------------
    # Registro manual / CRUD
    # ------------------------------------------------------------------
    def create_manual_entry(self, data: dict, created_by: str) -> str:
        data["created_by"] = created_by
        data["created_at"] = now_str()
        data.setdefault("estado", "Completado")
        return self.repo.create(data)

    def update_entry(self, record_id: str, data: dict) -> bool:
        return self.repo.update(record_id, data)

    def delete_entry(self, record_id: str) -> bool:
        return self.repo.delete(record_id)

    def list_entries(self) -> pd.DataFrame:
        return self.repo.fetch_all()

    # ------------------------------------------------------------------
    # Agregaciones
    # ------------------------------------------------------------------
    def hours_by(self, column: str) -> pd.DataFrame:
        df = self.list_entries()
        if df.empty or column not in df.columns:
            return pd.DataFrame(columns=[column, "horas"])
        df = df.copy()
        df["horas"] = df["duracion_horas"].apply(safe_float)
        return df.groupby(column, as_index=False)["horas"].sum().sort_values(
            "horas", ascending=False
        )

    def productive_ratio(self, df: pd.DataFrame | None = None) -> float:
        df = df if df is not None else self.list_entries()
        if df.empty:
            return 0.0
        total = df["duracion_horas"].apply(safe_float).sum()
        productive = df.loc[
            df["tipo"].isin(["Profundo", "Programación", "Diseño", "Investigación"]),
            "duracion_horas",
        ].apply(safe_float).sum()
        return round((productive / total) * 100, 1) if total else 0.0
