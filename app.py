"""
WorkJourney AI — punto de entrada principal.

Ejecutar con:
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from components.command_palette import render_command_palette
from components.notifications_panel import render_notifications
from components.quick_add import render_quick_add
from components.sidebar import render_sidebar
from config.settings import APP_NAME
from database.sheets_client import SheetsConnectionError, ensure_all_worksheets
from helpers.logger import get_logger
from services.auth_service import AuthService
from utils.helpers import inject_css

logger = get_logger(__name__)

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css("assets/style.css")


def _bootstrap_sheets() -> bool:
    """Verifica la conexión a Google Sheets y crea las hojas necesarias."""
    try:
        ensure_all_worksheets()
        return True
    except SheetsConnectionError as exc:
        st.error(f"⚠️ No se pudo conectar con Google Sheets: {exc}")
        with st.expander("Cómo solucionarlo"):
            st.markdown(
                """
                1. Verifica que exista un archivo `.env` con `GOOGLE_SHEET_ID` configurado.
                2. Verifica que el archivo de credenciales de la cuenta de servicio
                   exista en la ruta indicada por `GOOGLE_SERVICE_ACCOUNT_FILE`.
                3. Confirma que compartiste la Google Sheet con el email de la
                   cuenta de servicio (rol *Editor*).
                4. Revisa el `README.md` para la guía completa de configuración.
                """
            )
        return False


def _render_login() -> None:
    st.markdown(
        f"""
        <div style="max-width:420px;margin:60px auto 0 auto;text-align:center;">
            <div style="width:56px;height:56px;border-radius:16px;background:#6D5EF5;
                        display:flex;align-items:center;justify-content:center;
                        color:white;font-weight:700;font-size:1.6rem;margin:0 auto 16px auto;">W</div>
            <div style="font-size:1.4rem;font-weight:700;color:#1A1A2E;">{APP_NAME}</div>
            <div style="color:#8A8A9E;margin-bottom:24px;">
                Tu sistema completo de productividad personal.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    auth_service = AuthService()
    has_users = auth_service.has_users()

    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        with st.container(border=True):
            if not has_users:
                st.info("Configura la primera cuenta de administrador para comenzar.")
                with st.form("first_user_form"):
                    username = st.text_input("Usuario")
                    name = st.text_input("Nombre completo")
                    email = st.text_input("Correo")
                    password = st.text_input("Contraseña", type="password")
                    submitted = st.form_submit_button("Crear cuenta", type="primary", use_container_width=True)
                    if submitted:
                        ok, message = auth_service.register_user(
                            username, name, email, password, role="admin"
                        )
                        if ok:
                            st.success(message + " Ahora inicia sesión.")
                            st.rerun()
                        else:
                            st.error(message)
                return

            authenticator = auth_service.get_authenticator()
            authenticator.login(location="main")

            auth_status = st.session_state.get("authentication_status")
            if auth_status is False:
                st.error("Usuario o contraseña incorrectos.")
            elif auth_status is None:
                st.info("Ingresa tus credenciales para continuar.")

            with st.expander("¿No tienes cuenta? Regístrate"):
                with st.form("register_form"):
                    r_username = st.text_input("Usuario", key="reg_username")
                    r_name = st.text_input("Nombre completo", key="reg_name")
                    r_email = st.text_input("Correo", key="reg_email")
                    r_password = st.text_input("Contraseña", type="password", key="reg_password")
                    r_submitted = st.form_submit_button("Crear cuenta")
                    if r_submitted:
                        ok, message = auth_service.register_user(
                            r_username, r_name, r_email, r_password
                        )
                        if ok:
                            st.success(message)
                        else:
                            st.error(message)


def _render_topbar(username: str) -> None:
    col_search, col_notif, col_add = st.columns([6, 1, 1.2])
    with col_search:
        render_command_palette()
    with col_notif:
        render_notifications()
    with col_add:
        render_quick_add(username)


PAGE_ROUTES = {
    "Dashboard": "pages._dashboard",
    "Journey": "pages._journey",
    "Actividades": "pages._activities",
    "Tiempo": "pages._time",
    "Finanzas": "pages._finance",
    "Objetivos": "pages._goals",
    "Clientes": "pages._clients",
    "Proyectos": "pages._projects",
    "Analítica": "pages._analytics",
    "Insights AI": "pages._insights",
    "Configuración": "pages._settings",
}


def _render_app(username: str, display_name: str) -> None:
    selected = render_sidebar(display_name)
    with st.sidebar:
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            for key in ("authentication_status", "username", "name"):
                st.session_state.pop(key, None)
            st.rerun()
    _render_topbar(username)
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    import importlib

    module = importlib.import_module(PAGE_ROUTES.get(selected, "pages._dashboard"))
    try:
        if selected == "Dashboard":
            module.render(username, display_name)
        else:
            module.render(username)
    except SheetsConnectionError as exc:
        st.error(f"Error de conexión con Google Sheets: {exc}")
    except Exception:  # noqa: BLE001
        logger.exception("Error renderizando la página %s", selected)
        st.error(
            "Ocurrió un error inesperado al cargar este módulo. "
            "Revisa el archivo logs/app.log para más detalles."
        )


def main() -> None:
    if not _bootstrap_sheets():
        return

    auth_service = AuthService()
    if not auth_service.has_users():
        _render_login()
        return

    if not st.session_state.get("authentication_status"):
        _render_login()
        return

    username = st.session_state.get("username", "")
    display_name = st.session_state.get("name", username)

    _render_app(username, display_name)


if __name__ == "__main__":
    main()
