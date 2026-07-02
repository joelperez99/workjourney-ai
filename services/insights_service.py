"""
Insights AI — generados 100% con Python/Pandas (sin llamadas a APIs externas).

Analiza Journey, Time, Finance, Clients, Projects y Goals para producir
observaciones accionables tipo "coach de productividad".
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from services.clients_service import ClientsService
from services.finance_service import FinanceService
from services.goals_service import GoalsService
from services.journey_service import JourneyService
from services.projects_service import ProjectsService
from services.time_service import TimeService
from utils.helpers import compute_streak
from utils.formatters import parse_date


class InsightsService:
    def __init__(self):
        self.journey_service = JourneyService()
        self.time_service = TimeService()
        self.finance_service = FinanceService()
        self.clients_service = ClientsService()
        self.projects_service = ProjectsService()
        self.goals_service = GoalsService()

    def generate_insights(self) -> list[dict]:
        insights: list[dict] = []
        insights += self._best_hours_insight()
        insights += self._best_day_insight()
        insights += self._top_client_insight()
        insights += self._time_hungry_project_insight()
        insights += self._productivity_trend_insight()
        insights += self._streak_insight()
        insights += self._goal_pace_insight()
        insights += self._billable_ratio_insight()
        if not insights:
            insights.append(
                {
                    "icon": "✨",
                    "color": "info",
                    "title": "Aún no hay suficientes datos",
                    "message": "Registra más actividades en Journey y Tiempo para "
                    "desbloquear insights personalizados.",
                }
            )
        return insights

    # ------------------------------------------------------------------
    def _best_hours_insight(self) -> list[dict]:
        df = self.journey_service.list_entries()
        if df.empty or "hora_inicio" not in df.columns:
            return []
        hours = df["hora_inicio"].dropna().astype(str).str.slice(0, 2)
        hours = hours[hours.str.isdigit()]
        if hours.empty:
            return []
        top_hour = hours.value_counts().idxmax()
        start = int(top_hour)
        end = (start + 2) % 24
        return [
            {
                "icon": "🌅",
                "color": "primary",
                "title": "Tu horario más productivo",
                "message": f"Registras más actividad entre las {start:02d}:00 y "
                f"las {end:02d}:00. Aprovecha ese bloque para trabajo profundo.",
            }
        ]

    def _best_day_insight(self) -> list[dict]:
        df = self.time_service.list_entries()
        if df.empty:
            return []
        df = df.copy()
        df["_fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
        df = df.dropna(subset=["_fecha_dt"])
        if df.empty:
            return []
        df["dia"] = df["_fecha_dt"].dt.day_name()
        df["horas"] = df["duracion_horas"].astype(float, errors="ignore")
        by_day = df.groupby("dia")["duracion_horas"].apply(
            lambda s: pd.to_numeric(s, errors="coerce").sum()
        )
        if by_day.empty:
            return []
        top_day = by_day.idxmax()
        dias_es = {
            "Monday": "los lunes", "Tuesday": "los martes", "Wednesday": "los miércoles",
            "Thursday": "los jueves", "Friday": "los viernes", "Saturday": "los sábados",
            "Sunday": "los domingos",
        }
        return [
            {
                "icon": "📅",
                "color": "success",
                "title": "Tu día más productivo",
                "message": f"Eres más productivo {dias_es.get(top_day, top_day)}, con un "
                f"promedio de {by_day.max():.1f}h registradas.",
            }
        ]

    def _top_client_insight(self) -> list[dict]:
        by_client = self.finance_service.by_client()
        if by_client.empty:
            return []
        top = by_client.iloc[0]
        if not top["cliente"]:
            return []
        return [
            {
                "icon": "💰",
                "color": "success",
                "title": "Tu cliente más rentable",
                "message": f"{top['cliente']} genera el mayor ingreso: "
                f"${top['monto_num']:,.2f} hasta ahora.",
            }
        ]

    def _time_hungry_project_insight(self) -> list[dict]:
        stats = self.projects_service.project_stats()
        if stats.empty:
            return []
        stats = stats.dropna(subset=["horas_reales"])
        if stats.empty:
            return []
        worst = stats.sort_values("costo_hora", ascending=False).iloc[0]
        if worst["horas_reales"] <= 0 or worst["roi"] >= 0:
            heavy = stats.sort_values("horas_reales", ascending=False).iloc[0]
            return [
                {
                    "icon": "⏳",
                    "color": "warning",
                    "title": "Proyecto que más tiempo consume",
                    "message": f"'{heavy['nombre']}' acumula {heavy['horas_reales']:.1f}h. "
                    "Evalúa si el ritmo de inversión sigue siendo rentable.",
                }
            ]
        return [
            {
                "icon": "⚠️",
                "color": "danger",
                "title": "Proyecto con ROI negativo",
                "message": f"'{worst['nombre']}' tiene un ROI de {worst['roi']:.1f}%. "
                "Podría estar consumiendo más recursos de los que genera.",
            }
        ]

    def _productivity_trend_insight(self) -> list[dict]:
        df = self.time_service.list_entries()
        if df.empty:
            return []
        df = df.copy()
        df["_fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
        df = df.dropna(subset=["_fecha_dt"])
        if df.empty:
            return []
        df["horas"] = pd.to_numeric(df["duracion_horas"], errors="coerce").fillna(0)
        today = pd.Timestamp(dt.date.today())
        last_week = df[df["_fecha_dt"] >= today - pd.Timedelta(days=7)]["horas"].sum()
        prev_week = df[
            (df["_fecha_dt"] < today - pd.Timedelta(days=7))
            & (df["_fecha_dt"] >= today - pd.Timedelta(days=14))
        ]["horas"].sum()
        if prev_week == 0:
            return []
        change = round(((last_week - prev_week) / prev_week) * 100, 1)
        if abs(change) < 5:
            return []
        direction = "subió" if change > 0 else "bajó"
        icon = "📈" if change > 0 else "📉"
        color = "success" if change > 0 else "danger"
        return [
            {
                "icon": icon,
                "color": color,
                "title": "Tendencia de productividad",
                "message": f"Tu tiempo registrado {direction} {abs(change):.1f}% "
                "respecto a la semana anterior.",
            }
        ]

    def _streak_insight(self) -> list[dict]:
        df = self.journey_service.list_entries()
        if df.empty:
            return []
        dates = [d for d in df["fecha"].apply(parse_date).tolist() if d]
        streak = compute_streak(dates)
        if streak < 2:
            return []
        return [
            {
                "icon": "🔥",
                "color": "primary",
                "title": "Racha de productividad",
                "message": f"Llevas {streak} días consecutivos registrando trabajo. "
                "¡No rompas la racha!",
            }
        ]

    def _goal_pace_insight(self) -> list[dict]:
        goals = self.goals_service.list_goals()
        if goals.empty:
            return []
        insights = []
        for _, goal in goals.iterrows():
            if goal.get("progreso", 0) >= 100:
                continue
            days = self.goals_service.days_to_finish_at_current_pace(goal)
            if days is not None and 0 < days <= 60:
                insights.append(
                    {
                        "icon": "🎯",
                        "color": "info",
                        "title": f"Proyección: {goal['objetivo']}",
                        "message": f"Si mantienes este ritmo, terminarás en "
                        f"aproximadamente {days} días.",
                    }
                )
        return insights[:2]

    def _billable_ratio_insight(self) -> list[dict]:
        df = self.time_service.list_entries()
        if df.empty or "facturable" not in df.columns:
            return []
        df = df.copy()
        df["horas"] = pd.to_numeric(df["duracion_horas"], errors="coerce").fillna(0)
        total = df["horas"].sum()
        if not total:
            return []
        billable = df.loc[df["facturable"].astype(str).str.lower().isin(["sí", "si", "yes"]), "horas"].sum()
        ratio = round((billable / total) * 100, 1)
        return [
            {
                "icon": "🧾",
                "color": "success" if ratio >= 60 else "warning",
                "title": "Horas facturables",
                "message": f"El {ratio}% de tu tiempo registrado es facturable "
                f"({billable:.1f}h de {total:.1f}h).",
            }
        ]
