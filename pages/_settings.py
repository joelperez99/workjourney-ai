"""Página Configuración: perfil, avatar, tema e importación/exportación de datos."""
from __future__ import annotations

import streamlit as st

from components.cards import section_title
from database.repository import clear_all_cache
from services.auth_service import AuthService
from services.export_service import read_uploaded_file, to_csv_bytes, to_excel_bytes
from database.sheets_client import get_worksheet
from config.settings import SCHEMAS
from utils.validators import is_valid_email


def render(username: str):
    section_title("Configuración", "Perfil, preferencias y datos de tu cuenta.")

    auth_service = AuthService()
    user = auth_service.get_user(username) or {}

    tab_profile, tab_theme, tab_data = st.tabs(["👤 Perfil", "🎨 Tema", "📦 Datos"])

    with tab_profile:
        with st.form("profile_form"):
            c1, c2 = st.columns([1, 3])
            with c1:
                avatar_url = user.get("avatar_url") or ""
                if avatar_url:
                    st.image(avatar_url, width=80)
                else:
                    st.markdown(
                        f"""
                        <div style="width:80px;height:80px;border-radius:50%;background:#EFECFF;
                                    display:flex;align-items:center;justify-content:center;
                                    color:#5544E0;font-weight:700;font-size:1.8rem;">
                            {username[:1].upper()}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            with c2:
                name = st.text_input("Nombre", value=user.get("name", ""))
                email = st.text_input("Correo", value=user.get("email", ""))
                avatar_url_input = st.text_input("URL de avatar", value=avatar_url)

            submitted = st.form_submit_button("Guardar cambios", type="primary")
            if submitted:
                if email and not is_valid_email(email):
                    st.error("Correo inválido.")
                else:
                    auth_service.update_profile(
                        username, {"name": name, "email": email, "avatar_url": avatar_url_input}
                    )
                    st.success("Perfil actualizado.")
                    st.rerun()

    with tab_theme:
        theme = st.radio(
            "Tema de la aplicación", ["Claro", "Oscuro (opcional)"],
            index=0 if user.get("theme", "light") == "light" else 1,
        )
        if st.button("Guardar tema"):
            auth_service.update_profile(username, {"theme": "light" if theme == "Claro" else "dark"})
            st.success("Preferencia guardada. Se aplicará en tu próxima sesión.")
        st.caption(
            "Nota: el modo oscuro completo requiere configurar el tema en "
            "`.streamlit/config.toml`. Esta preferencia queda guardada en tu perfil."
        )

    with tab_data:
        st.markdown("**Importar datos**")
        target_sheet = st.selectbox("Hoja destino", list(SCHEMAS.keys()))
        uploaded = st.file_uploader("Sube un archivo Excel o CSV", type=["xlsx", "csv"])
        if uploaded and st.button("Importar"):
            try:
                df = read_uploaded_file(uploaded)
                ws = get_worksheet(target_sheet)
                headers = SCHEMAS[target_sheet]
                rows = []
                for _, row in df.iterrows():
                    rows.append([str(row.get(h, "")) for h in headers])
                for row in rows:
                    ws.append_row(row, value_input_option="USER_ENTERED")
                clear_all_cache()
                st.success(f"Se importaron {len(rows)} filas a '{target_sheet}'.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Error al importar: {exc}")

        st.divider()
        st.markdown("**Exportar todos los datos**")
        export_sheet = st.selectbox("Hoja a exportar", list(SCHEMAS.keys()), key="export_sheet")
        if st.button("Generar exportación"):
            from database.repository import SheetRepository

            df = SheetRepository(export_sheet).fetch_all()
            c1, c2 = st.columns(2)
            c1.download_button(
                "⬇️ CSV", to_csv_bytes(df), f"{export_sheet.lower()}.csv", "text/csv",
                use_container_width=True,
            )
            c2.download_button(
                "⬇️ Excel", to_excel_bytes(df, export_sheet), f"{export_sheet.lower()}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.divider()
        if st.button("🔄 Limpiar caché y recargar datos"):
            clear_all_cache()
            st.success("Caché limpiada.")
            st.rerun()
