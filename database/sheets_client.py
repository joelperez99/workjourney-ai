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
    """Crea las hojas faltantes y valida encabezados según SCHEMAS.

    Usa values_batch_get para leer los encabezados de todas las hojas
    existentes en una sola llamada a la API (en vez de una por hoja), ya
    que la cuota de la API de Google Sheets es fácil de agotar si se hace
    una petición por hoja en cada arranque de la app.
    """
    spreadsheet = get_spreadsheet()
    try:
        existing = {ws.title: ws for ws in spreadsheet.worksheets()}

        missing = [name for name in SCHEMAS if name not in existing]
        for sheet_name in missing:
            headers = SCHEMAS[sheet_name]
            logger.info("Creando hoja '%s'", sheet_name)
            ws = spreadsheet.add_worksheet(
                title=sheet_name, rows=1000, cols=max(len(headers), 10)
            )
            ws.append_row(headers, value_input_option="USER_ENTERED")
            existing[sheet_name] = ws

        present = [name for name in SCHEMAS if name not in missing]
        if present:
            ranges = [f"'{name}'!1:1" for name in present]
            result = spreadsheet.values_batch_get(ranges)
            for value_range in result.get("valueRanges", []):
                sheet_name = value_range["range"].split("!")[0].strip("'")
                headers = SCHEMAS[sheet_name]
                values = value_range.get("values")
                first_row = values[0] if values else []
                if first_row != headers:
                    if not first_row:
                        existing[sheet_name].append_row(
                            headers, value_input_option="USER_ENTERED"
                        )
                    else:
                        logger.warning(
                            "La hoja '%s' tiene encabezados distintos a los "
                            "esperados. No se modifican automáticamente.",
                            sheet_name,
                        )
    except gspread.exceptions.APIError as exc:
        raise SheetsConnectionError(
            "Error al comunicarse con la API de Google Sheets (posible "
            "límite de tasa temporal). Intenta recargar la app en unos "
            "segundos."
        ) from exc


def get_worksheet(sheet_name: str) -> gspread.Worksheet:
    spreadsheet = get_spreadsheet()
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ensure_all_worksheets()
        return spreadsheet.worksheet(sheet_name)
