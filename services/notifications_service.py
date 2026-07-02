"""
Centro de notificaciones: recordatorios de objetivos, tareas pendientes y
seguimiento de clientes. Se generan dinámicamente (no se guardan todas en
Sheets) y se combinan con notificaciones persistidas manualmente.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from config.settings import SHEET_NOTIFICATIONS
from database.repository import SheetRepository
from services.activities_service import ActivitiesService
from services.clients_service import ClientsService
from services.goals_service import GoalsService
from utils.formatters import now_str, parse_date


class NotificationsService:
    def __init__(self):
        self.repo = SheetRepository(SHEET_NOTIFICATIONS)
        self.goals_service = GoalsService()
        self.activities_service = ActivitiesService()
        self.clients_service = ClientsService()

    def generate_dynamic_notifications(self) -> list[dict]:
        notifications: list[dict] = []
        today = dt.date.today()

        # Objetivos próximos a vencer o vencidos
        goals = self.goals_service.list_goals()
        for _, goal in goals.iterrows():
            if goal.get("estado") == "Completado" or goal.get("progreso", 0) >= 100:
                continue
            deadline = parse_date(goal.get("fecha_limite"))
            if not deadline:
                continue
            days_left = (deadline - today).days
            if days_left < 0:
                notifications.append(
                    {
                        "tipo": "danger",
                        "icono": "⚠️",
                        "titulo": "Objetivo vencido",
                        "mensaje": f"'{goal['objetivo']}' venció hace {abs(days_left)} días.",
                    }
                )
            elif days_left <= 3:
                notifications.append(
                    {
                        "tipo": "warning",
                        "icono": "⏰",
                        "titulo": "Objetivo por vencer",
                        "mensaje": f"'{goal['objetivo']}' vence en {days_left} días "
                        f"({goal.get('progreso', 0)}% completado).",
                    }
                )

        # Actividades pendientes de alta prioridad
        activities = self.activities_service.list_activities()
        if not activities.empty:
            pending = activities[
                (activities["status"] == "Pendiente")
                & (activities["prioridad"].isin(["Alta", "Urgente"]))
            ]
            for _, act in pending.iterrows():
                notifications.append(
                    {
                        "tipo": "info",
                        "icono": "📌",
                        "titulo": "Actividad pendiente",
                        "mensaje": f"'{act['titulo']}' está marcada como {act['prioridad']} "
                        "y sigue pendiente.",
                    }
                )

        # Clientes inactivos con seguimiento sugerido
        clients = self.clients_service.list_clients()
        if not clients.empty:
            inactive = clients[clients["estado"] == "Inactivo"]
            for _, client in inactive.iterrows():
                notifications.append(
                    {
                        "tipo": "info",
                        "icono": "🤝",
                        "titulo": "Cliente inactivo",
                        "mensaje": f"Podrías retomar contacto con {client['nombre']}.",
                    }
                )

        return notifications

    def persisted_notifications(self) -> pd.DataFrame:
        return self.repo.fetch_all()

    def add_notification(
        self, tipo: str, titulo: str, mensaje: str, created_by: str
    ) -> str:
        return self.repo.create(
            {
                "tipo": tipo,
                "titulo": titulo,
                "mensaje": mensaje,
                "leida": "No",
                "fecha": now_str(),
                "created_by": created_by,
                "created_at": now_str(),
            }
        )

    def mark_read(self, record_id: str) -> bool:
        return self.repo.update(record_id, {"leida": "Sí"})
