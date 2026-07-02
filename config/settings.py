"""
Configuración central de WorkJourney AI.
Carga variables de entorno y define constantes usadas en toda la app.
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _get_setting(key: str, default: str = "") -> str:
    """Busca primero en st.secrets (Streamlit Cloud) y luego en el entorno/.env (local)."""
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:  # noqa: BLE001 - sin archivo secrets.toml en local
        pass
    return os.getenv(key, default)


# ----------------------------------------------------------------------
# App
# ----------------------------------------------------------------------
APP_NAME = _get_setting("APP_NAME", "WorkJourney AI")
APP_TIMEZONE = _get_setting("APP_TIMEZONE", "America/Mexico_City")
DEFAULT_CURRENCY = _get_setting("DEFAULT_CURRENCY", "USD")

# ----------------------------------------------------------------------
# Google Sheets
# ----------------------------------------------------------------------
GOOGLE_SHEET_ID = _get_setting("GOOGLE_SHEET_ID", "")
GOOGLE_SERVICE_ACCOUNT_FILE = _get_setting(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "config/service_account.json"
)

# Credenciales de la cuenta de servicio como dict, cuando se configuran vía
# st.secrets (Streamlit Cloud) bajo la sección [gcp_service_account].
GOOGLE_SERVICE_ACCOUNT_INFO: dict | None = None
try:
    if "gcp_service_account" in st.secrets:
        GOOGLE_SERVICE_ACCOUNT_INFO = dict(st.secrets["gcp_service_account"])
except Exception:  # noqa: BLE001 - sin archivo secrets.toml en local
    pass

# ----------------------------------------------------------------------
# Auth
# ----------------------------------------------------------------------
AUTH_COOKIE_KEY = _get_setting("AUTH_COOKIE_KEY", "change_this_secret_key")
AUTH_COOKIE_NAME = _get_setting("AUTH_COOKIE_NAME", "workjourney_auth")
AUTH_COOKIE_EXPIRY_DAYS = int(_get_setting("AUTH_COOKIE_EXPIRY_DAYS", "30"))

# ----------------------------------------------------------------------
# Paleta de colores (SaaS moderno: Linear / Notion / Stripe)
# ----------------------------------------------------------------------
COLORS = {
    "primary": "#6D5EF5",
    "primary_light": "#EFECFF",
    "primary_dark": "#5544E0",
    "white": "#FFFFFF",
    "bg": "#F7F7FB",
    "gray_light": "#F1F1F5",
    "gray": "#8A8A9E",
    "gray_dark": "#4B4B5A",
    "border": "#E7E7EF",
    "text": "#1A1A2E",
    "success": "#1FAA6B",
    "success_light": "#E5F8EF",
    "warning": "#F5A623",
    "warning_light": "#FFF4E0",
    "danger": "#F2545B",
    "danger_light": "#FDEAEA",
    "info": "#3B82F6",
    "info_light": "#EAF2FE",
}

CHART_COLORWAY = [
    "#6D5EF5", "#3B82F6", "#1FAA6B", "#F5A623",
    "#F2545B", "#8A5EF5", "#5EC9F5", "#F55E9D",
]

# ----------------------------------------------------------------------
# Nombres de las hojas (una por módulo)
# ----------------------------------------------------------------------
SHEET_USERS = "Users"
SHEET_JOURNEY = "Journey"
SHEET_ACTIVITIES = "Activities"
SHEET_TIME = "Time"
SHEET_FINANCE = "Finance"
SHEET_GOALS = "Goals"
SHEET_CLIENTS = "Clients"
SHEET_PROJECTS = "Projects"
SHEET_TAGS = "Tags"
SHEET_NOTIFICATIONS = "Notifications"
SHEET_SETTINGS = "Settings"

# ----------------------------------------------------------------------
# Esquemas (encabezados) de cada hoja — usados para autocrear y validar
# ----------------------------------------------------------------------
SCHEMAS: dict[str, list[str]] = {
    SHEET_USERS: [
        "id", "username", "name", "email", "password_hash", "role",
        "avatar_url", "theme", "created_at",
    ],
    SHEET_JOURNEY: [
        "id", "fecha", "hora_inicio", "hora_fin", "proyecto", "cliente",
        "objetivo", "actividad", "descripcion", "resultado", "impacto",
        "dificultad", "estado", "aprendizaje", "energia", "motivacion",
        "estres", "prioridad", "tipo_trabajo", "tags", "dinero_generado",
        "hits", "created_at", "created_by",
    ],
    SHEET_ACTIVITIES: [
        "id", "titulo", "proyecto", "cliente", "categoria", "descripcion",
        "inicio", "fin", "duracion_horas", "resultado", "status",
        "prioridad", "hit_conseguido", "valor_hit", "dinero_relacionado",
        "url", "archivos", "notas", "tags", "created_at", "created_by",
    ],
    SHEET_TIME: [
        "id", "fecha", "proyecto", "cliente", "actividad", "inicio",
        "fin", "duracion_horas", "tipo", "facturable", "estado",
        "notas", "created_at", "created_by",
    ],
    SHEET_FINANCE: [
        "id", "tipo", "fecha", "cliente", "proyecto", "monto",
        "metodo_pago", "referencia", "factura", "categoria", "notas",
        "created_at", "created_by",
    ],
    SHEET_GOALS: [
        "id", "objetivo", "descripcion", "fecha_limite", "meta",
        "valor_actual", "unidad", "estado", "categoria", "created_at",
        "created_by",
    ],
    SHEET_CLIENTS: [
        "id", "nombre", "empresa", "correo", "whatsapp", "industria",
        "tarifa_hora", "estado", "notas", "created_at", "created_by",
    ],
    SHEET_PROJECTS: [
        "id", "nombre", "cliente", "costo", "ingreso_esperado",
        "ingreso_real", "horas_estimadas", "horas_reales", "estado",
        "deadline", "prioridad", "descripcion", "created_at", "created_by",
    ],
    SHEET_TAGS: ["id", "nombre", "color", "created_at"],
    SHEET_NOTIFICATIONS: [
        "id", "tipo", "titulo", "mensaje", "leida", "fecha", "created_at",
        "created_by",
    ],
    SHEET_SETTINGS: ["id", "clave", "valor", "updated_at", "updated_by"],
}

TIPOS_TRABAJO = [
    "Profundo", "Administrativo", "Ventas", "Marketing", "Reunión",
    "Programación", "Diseño", "Investigación", "Otro",
]

ESTADOS_ACTIVIDAD = ["Pendiente", "En progreso", "Completada", "Cancelada"]
PRIORIDADES = ["Baja", "Media", "Alta", "Urgente"]
METODOS_PAGO = ["Transferencia", "Efectivo", "Tarjeta", "PayPal", "Otro"]
CATEGORIAS_FINANZAS_INGRESO = [
    "Servicio", "Consultoría", "Producto", "Proyecto", "Otro",
]
CATEGORIAS_FINANZAS_GASTO = [
    "Software", "Herramientas", "Marketing", "Impuestos", "Oficina", "Otro",
]
