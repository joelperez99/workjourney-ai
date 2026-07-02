"""Lógica de negocio del módulo Clientes."""
from __future__ import annotations

import pandas as pd

from config.settings import SHEET_ACTIVITIES, SHEET_CLIENTS, SHEET_FINANCE, SHEET_TIME
from database.repository import SheetRepository
from utils.helpers import safe_float
from utils.formatters import now_str


class ClientsService:
    def __init__(self):
        self.repo = SheetRepository(SHEET_CLIENTS)
        self.time_repo = SheetRepository(SHEET_TIME)
        self.finance_repo = SheetRepository(SHEET_FINANCE)
        self.activities_repo = SheetRepository(SHEET_ACTIVITIES)

    def list_clients(self, only_active: bool = False) -> pd.DataFrame:
        df = self.repo.fetch_all()
        if only_active and not df.empty:
            df = df[df["estado"] == "Activo"]
        return df

    def client_names(self) -> list[str]:
        df = self.list_clients()
        return sorted([c for c in df.get("nombre", pd.Series(dtype=str)).unique() if c])

    def create_client(self, data: dict, created_by: str) -> str:
        data["created_by"] = created_by
        data["created_at"] = now_str()
        return self.repo.create(data)

    def update_client(self, record_id: str, data: dict) -> bool:
        return self.repo.update(record_id, data)

    def delete_client(self, record_id: str) -> bool:
        return self.repo.delete(record_id)

    def duplicate_client(self, record_id: str) -> str | None:
        return self.repo.duplicate(record_id)

    def client_stats(self) -> pd.DataFrame:
        """Ingresos, tiempo invertido y ROI por cliente."""
        clients = self.list_clients()
        if clients.empty:
            return pd.DataFrame(
                columns=["nombre", "ingresos", "horas", "roi"]
            )

        finance = self.finance_repo.fetch_all()
        time_df = self.time_repo.fetch_all()

        rows = []
        for _, client in clients.iterrows():
            name = client["nombre"]
            ingresos = 0.0
            if not finance.empty:
                income_mask = (finance["cliente"] == name) & (finance["tipo"] == "Ingreso")
                ingresos = finance.loc[income_mask, "monto"].apply(safe_float).sum()

            horas = 0.0
            if not time_df.empty:
                horas = (
                    time_df.loc[time_df["cliente"] == name, "duracion_horas"]
                    .apply(safe_float)
                    .sum()
                )

            tarifa = safe_float(client.get("tarifa_hora"))
            costo_estimado = tarifa * horas
            roi = ((ingresos - costo_estimado) / costo_estimado * 100) if costo_estimado else 0.0

            rows.append(
                {
                    "id": client["id"],
                    "nombre": name,
                    "empresa": client.get("empresa", ""),
                    "estado": client.get("estado", ""),
                    "ingresos": ingresos,
                    "horas": horas,
                    "roi": roi,
                }
            )
        return pd.DataFrame(rows)
