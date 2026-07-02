"""
Cliente singleton de Google Sheets usando gspread + google-auth.

Se conecta con una cuenta de servicio, abre (o crea) el spreadsheet indicado
por GOOGLE_SHEET_ID y garantiza que todas las hojas definidas en
config.settings.SCHEMAS existan con sus encabezados correctos.
"""
from __future__ import annotations

import gspread
from google.oauth2.service_account import Credentials

from config.settings import (
    GOOGLE_SERVICE_ACCOUNT_FILE,
    GOOGLE_SERVICE_ACCOUNT_INFO,
    GOOGLE_SHEET_ID,
    SCHEMAS,
)
from helpers.cache import cache_resource
from helpers.logger import get_logger

logger = get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class SheetsConnectionError(RuntimeError):
    """Se lanza cuando no es posible conectar con Google Sheets."""


@cache_resource()
def get_gspread_client() -> gspread.Client:
    try:
        if GOOGLE_SERVICE_ACCOUNT_INFO:
            creds = Credentials.from_service_account_info(
                GOOGLE_SERVICE_ACCOUNT_INFO, scopes=SCOPES
            )
        else:
            creds = Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
        return gspread.authorize(creds)
    except FileNotFoundError as exc:
        raise SheetsConnectionError(
            f"No se encontró el archivo de credenciales en "
            f"'{GOOGLE_SERVICE_ACCOUNT_FILE}'. Revisa el README para "
            f"configurar la cuenta de servicio de Google."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error autenticando con Google Sheets")
        raise SheetsConnectionError(str(exc)) from exc


@cache_resource()
def get_spreadsheet() -> gspread.Spreadsheet:
    if not GOOGLE_SHEET_ID:
        raise SheetsConnectionError(
            "GOOGLE_SHEET_ID no está configurado. Define esta variable en tu "
            "archivo .env con el ID de tu Google Sheet."
        )
    client = get_gspread_client()
    try:
        return client.open_by_key(GOOGLE_SHEET_ID)
    except gspread.exceptions.SpreadsheetNotFound as exc:
        raise SheetsConnectionError(
            "No se encontró el spreadsheet. Verifica GOOGLE_SHEET_ID y que "
            "hayas compartido la hoja con el email de la cuenta de servicio."
        ) from exc


def ensure_all_worksheets() -> None:
    """Crea las hojas faltantes y valida encabezados según SCHEMAS."""
    spreadsheet = get_spreadsheet()
    existing = {ws.title: ws for ws in spreadsheet.worksheets()}

    for sheet_name, headers in SCHEMAS.items():
        if sheet_name not in existing:
            logger.info("Creando hoja '%s'", sheet_name)
            ws = spreadsheet.add_worksheet(
                title=sheet_name, rows=1000, cols=max(len(headers), 10)
            )
            ws.append_row(headers, value_input_option="USER_ENTERED")
        else:
            ws = existing[sheet_name]
            first_row = ws.row_values(1)
            if first_row != headers:
                if not first_row:
                    ws.append_row(headers, value_input_option="USER_ENTERED")
                else:
                    logger.warning(
                        "La hoja '%s' tiene encabezados distintos a los "
                        "esperados. No se modifican automáticamente.",
                        sheet_name,
                    )


def get_worksheet(sheet_name: str) -> gspread.Worksheet:
    spreadsheet = get_spreadsheet()
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ensure_all_worksheets()
        return spreadsheet.worksheet(sheet_name)
