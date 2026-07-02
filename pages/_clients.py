"""Página Clientes: registro y dashboard de clientes."""
from __future__ import annotations

import streamlit as st

from components.cards import badge, empty_state, kpi_card, section_title
from services.clients_service import ClientsService
from utils.formatters import format_currency, format_hours, format_percent
from utils.helpers import badge_color_for_status
from utils.validators import is_valid_email


def render(username: str):
    section_title("Clientes", "Gestiona tu cartera de clientes y su rentabilidad.")

    service = ClientsService()

    with st.expander("➕ Nuevo cliente", expanded=False):
        with st.form("client_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre")
            empresa = c2.text_input("Empresa")

            c3, c4 = st.columns(2)
            correo = c3.text_input("Correo")
            whatsapp = c4.text_input("WhatsApp")

            c5, c6 = st.columns(2)
            industria = c5.text_input("Industria")
            tarifa_hora = c6.number_input("Tarifa por hora", min_value=0.0, step=5.0)

            estado = st.selectbox("Estado", ["Activo", "Inactivo"])
            notas = st.text_area("Notas", height=60)

            submitted = st.form_submit_button("Guardar cliente", type="primary")
            if submitted and nombre:
                if correo and not is_valid_email(correo):
                    st.error("Correo inválido.")
                else:
                    service.create_client(
                        {
                            "nombre": nombre, "empresa": empresa, "correo": correo,
                            "whatsapp": whatsapp, "industria": industria,
                            "tarifa_hora": tarifa_hora, "estado": estado, "notas": notas,
                        },
                        created_by=username,
                    )
                    st.success("Cliente guardado.")
                    st.rerun()

    stats = service.client_stats()
    if stats.empty:
        empty_state("Aún no tienes clientes registrados.")
        return

    k1, k2, k3 = st.columns(3)
    kpi_card("Clientes activos", str((stats["estado"] == "Activo").sum()), "🤝")
    kpi_card("Ingresos totales", format_currency(stats["ingresos"].sum()), "💰")
    kpi_card("Horas invertidas", format_hours(stats["horas"].sum()), "🕐")

    st.divider()

    cols = st.columns(3)
    for i, (_, client) in enumerate(stats.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                color = badge_color_for_status(client["estado"])
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;'>"
                    f"<b>{client['nombre']}</b>{badge(client['estado'], color)}</div>",
                    unsafe_allow_html=True,
                )
                st.caption(client.get("empresa", ""))
                st.markdown(
                    f"💰 {format_currency(client['ingresos'])} &nbsp;|&nbsp; "
                    f"🕐 {format_hours(client['horas'])} &nbsp;|&nbsp; "
                    f"📈 ROI {format_percent(client['roi'])}"
                )
                b1, b2 = st.columns(2)
                if b1.button("Duplicar", key=f"dup_client_{client['id']}", use_container_width=True):
                    service.duplicate_client(client["id"])
                    st.rerun()
                if b2.button("Eliminar", key=f"del_client_{client['id']}", use_container_width=True):
                    service.delete_client(client["id"])
                    st.rerun()
