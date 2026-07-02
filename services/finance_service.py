"""Lógica de negocio del módulo Finanzas."""
from __future__ import annotations

import pandas as pd

from config.settings import SHEET_FINANCE
from database.repository import SheetRepository
from utils.formatters import now_str
from utils.helpers import safe_float


class FinanceService:
    def __init__(self):
        self.repo = SheetRepository(SHEET_FINANCE)

    def list_transactions(self) -> pd.DataFrame:
        df = self.repo.fetch_all()
        if df.empty:
            return df
        df = df.copy()
        df["monto_num"] = df["monto"].apply(safe_float)
        df["_fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
        return df

    def create_transaction(self, data: dict, created_by: str) -> str:
        data["created_by"] = created_by
        data["created_at"] = now_str()
        return self.repo.create(data)

    def update_transaction(self, record_id: str, data: dict) -> bool:
        return self.repo.update(record_id, data)

    def delete_transaction(self, record_id: str) -> bool:
        return self.repo.delete(record_id)

    def duplicate_transaction(self, record_id: str) -> str | None:
        return self.repo.duplicate(record_id)

    def totals(self, df: pd.DataFrame | None = None) -> dict:
        df = df if df is not None else self.list_transactions()
        if df.empty:
            return {"ingresos": 0.0, "gastos": 0.0, "utilidad": 0.0}
        ingresos = df.loc[df["tipo"] == "Ingreso", "monto_num"].sum()
        gastos = df.loc[df["tipo"] == "Gasto", "monto_num"].sum()
        return {"ingresos": ingresos, "gastos": gastos, "utilidad": ingresos - gastos}

    def by_client(self) -> pd.DataFrame:
        df = self.list_transactions()
        if df.empty:
            return pd.DataFrame(columns=["cliente", "monto_num"])
        income = df[df["tipo"] == "Ingreso"]
        return (
            income.groupby("cliente", as_index=False)["monto_num"]
            .sum()
            .sort_values("monto_num", ascending=False)
        )

    def by_project(self) -> pd.DataFrame:
        df = self.list_transactions()
        if df.empty:
            return pd.DataFrame(columns=["proyecto", "monto_num"])
        income = df[df["tipo"] == "Ingreso"]
        return (
            income.groupby("proyecto", as_index=False)["monto_num"]
            .sum()
            .sort_values("monto_num", ascending=False)
        )

    def monthly_summary(self) -> pd.DataFrame:
        df = self.list_transactions()
        if df.empty:
            return pd.DataFrame(columns=["mes", "ingresos", "gastos", "utilidad"])
        df = df.dropna(subset=["_fecha_dt"]).copy()
        df["mes"] = df["_fecha_dt"].dt.to_period("M").astype(str)
        pivot = (
            df.pivot_table(
                index="mes", columns="tipo", values="monto_num", aggfunc="sum", fill_value=0
            )
            .reset_index()
        )
        for col in ("Ingreso", "Gasto"):
            if col not in pivot.columns:
                pivot[col] = 0.0
        pivot = pivot.rename(columns={"Ingreso": "ingresos", "Gasto": "gastos"})
        pivot["utilidad"] = pivot["ingresos"] - pivot["gastos"]
        return pivot.sort_values("mes")

    def forecast_next_month(self) -> float:
        """Forecast simple basado en el promedio móvil de los últimos 3 meses."""
        monthly = self.monthly_summary()
        if monthly.empty:
            return 0.0
        return round(monthly["ingresos"].tail(3).mean(), 2)
