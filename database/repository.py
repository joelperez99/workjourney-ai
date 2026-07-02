"""
Repositorio genérico de CRUD sobre una hoja de Google Sheets.

Todos los servicios de módulo (Journey, Activities, Time, Finance, etc.)
reutilizan esta clase en vez de reimplementar lectura/escritura, evitando
código duplicado y centralizando el manejo de errores y cache.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import SCHEMAS
from database.sheets_client import SheetsConnectionError, get_worksheet
from helpers.cache import cache_dataframe
from helpers.logger import get_logger
from utils.formatters import new_id, now_str

logger = get_logger(__name__)


class SheetRepository:
    """CRUD genérico para una hoja de Google Sheets con esquema fijo."""

    def __init__(self, sheet_name: str):
        if sheet_name not in SCHEMAS:
            raise ValueError(f"Hoja desconocida: {sheet_name}")
        self.sheet_name = sheet_name
        self.headers = SCHEMAS[sheet_name]

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------
    def fetch_all(self) -> pd.DataFrame:
        """Lee todos los registros. Cacheado por hoja durante 30s."""
        return _fetch_cached(self.sheet_name, self.headers)

    def get_by_id(self, record_id: str) -> dict | None:
        df = self.fetch_all()
        if df.empty or "id" not in df.columns:
            return None
        match = df[df["id"] == record_id]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------
    def create(self, data: dict) -> str:
        """Inserta un registro nuevo. Devuelve el id generado."""
        record = {h: data.get(h, "") for h in self.headers}
        if not record.get("id"):
            record["id"] = new_id()
        if "created_at" in self.headers and not record.get("created_at"):
            record["created_at"] = now_str()

        try:
            ws = get_worksheet(self.sheet_name)
            row = [str(record.get(h, "")) for h in self.headers]
            ws.append_row(row, value_input_option="USER_ENTERED")
        except SheetsConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error creando registro en %s", self.sheet_name)
            raise SheetsConnectionError(str(exc)) from exc

        self._invalidate_cache()
        return record["id"]

    def update(self, record_id: str, data: dict) -> bool:
        """Actualiza un registro existente identificado por 'id'."""
        try:
            ws = get_worksheet(self.sheet_name)
            cell = ws.find(record_id, in_column=self.headers.index("id") + 1)
            if cell is None:
                return False

            current = dict(zip(self.headers, ws.row_values(cell.row)))
            current.update({k: v for k, v in data.items() if k in self.headers})
            row = [str(current.get(h, "")) for h in self.headers]
            ws.update(
                f"A{cell.row}:{_col_letter(len(self.headers))}{cell.row}",
                [row],
                value_input_option="USER_ENTERED",
            )
        except SheetsConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error actualizando registro en %s", self.sheet_name)
            raise SheetsConnectionError(str(exc)) from exc

        self._invalidate_cache()
        return True

    def delete(self, record_id: str) -> bool:
        try:
            ws = get_worksheet(self.sheet_name)
            cell = ws.find(record_id, in_column=self.headers.index("id") + 1)
            if cell is None:
                return False
            ws.delete_rows(cell.row)
        except SheetsConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error eliminando registro en %s", self.sheet_name)
            raise SheetsConnectionError(str(exc)) from exc

        self._invalidate_cache()
        return True

    def duplicate(self, record_id: str) -> str | None:
        record = self.get_by_id(record_id)
        if record is None:
            return None
        record = dict(record)
        record.pop("id", None)
        record.pop("created_at", None)
        return self.create(record)

    # ------------------------------------------------------------------
    def _invalidate_cache(self) -> None:
        _fetch_cached.clear()


def _col_letter(n: int) -> str:
    letters = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


@cache_dataframe(ttl=20)
def _fetch_cached(sheet_name: str, headers: list[str]) -> pd.DataFrame:
    try:
        ws = get_worksheet(sheet_name)
        records = ws.get_all_records(expected_headers=headers)
    except SheetsConnectionError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error leyendo hoja %s", sheet_name)
        raise SheetsConnectionError(str(exc)) from exc

    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame(columns=headers)
    for col in headers:
        if col not in df.columns:
            df[col] = ""
    return df[headers]


def clear_all_cache() -> None:
    _fetch_cached.clear()
    st.cache_data.clear()
