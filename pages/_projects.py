"""Página Proyectos: registro y dashboard de rentabilidad/horas/ROI."""
from __future__ import annotations

import streamlit as st

from components.cards import badge, empty_state, kpi_card, progress_bar, section_title
from config.settings import PRIORIDADES
from services.clients_service import ClientsService
from services.projects_service import ProjectsService
from utils.formatters import format_currency, format_hours, format_percent
from utils.helpers import badge_color_for_status


def render(username: str):
    section_title("Proyectos", "Rentabilidad, horas y ROI de cada proyecto.")

    service = ProjectsService()
    clients = ClientsService().client_names()

    with st.expander("➕ Nuevo proyecto", expanded=False):
        with st.form("project_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre")
            cliente = c2.selectbox("Cliente", [""] + clients)

            c3, c4 = st.columns(2)
            costo = c3.number_input("Costo", min_value=0.0, step=50.0)
            ingreso_esperado = c4.number_input("Ingreso esperado", min_value=0.0, step=50.0)

            c5, c6 = st.columns(2)
            horas_estimadas = c5.number_input("Horas estimadas", min_value=0.0, step=1.0)
            deadline = c6.date_input("Deadline")

            c7, c8 = st.columns(2)
            estado = c7.selectbox("Estado", ["Activo", "Pausado", "Completado", "Cancelado"])
            prioridad = c8.selectbox("Prioridad", PRIORIDADES)

            descripcion = st.text_area("Descripción", height=60)

            submitted = st.form_submit_button("Guardar proyecto", type="primary")
            if submitted and nombre:
                service.create_project(
                    {
                        "nombre": nombre, "cliente": cliente, "costo": costo,
                        "ingreso_esperado": ingreso_esperado, "ingreso_real": 0,
                        "horas_estimadas": horas_estimadas, "horas_reales": 0,
                        "estado": estado, "deadline": str(deadline),
                        "prioridad": prioridad, "descripcion": descripcion,
                    },
                    created_by=username,
                )
                st.success("Proyecto guardado.")
                st.rerun()

    stats = service.project_stats()
    if stats.empty:
        empty_state("Aún no tienes proyectos registrados.")
        return

    k1, k2, k3 = st.columns(3)
    kpi_card("Proyectos activos", str((stats["estado"] == "Activo").sum()), "📁")
    kpi_card("Rentabilidad total", format_currency(stats["rentabilidad"].sum()), "📈")
    kpi_card("Horas registradas", format_hours(stats["horas_reales"].sum()), "🕐")

    st.divider()

    for _, project in stats.iterrows():
        with st.container(border=True):
            color = badge_color_for_status(project["estado"])
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"<b>{project['nombre']}</b>{badge(project['estado'], color)}</div>",
                unsafe_allow_html=True,
            )
            st.caption(f"Cliente: {project.get('cliente','-')}")

            progreso = 0
            if project["horas_estimadas"]:
                progreso = min((project["horas_reales"] / project["horas_estimadas"]) * 100, 100)
            progress_bar(progreso)
            st.caption(f"{format_hours(project['horas_reales'])} de {format_hours(project['horas_estimadas'])} estimadas")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Rentabilidad", format_currency(project["rentabilidad"]))
            m2.metric("Costo/Hora", format_currency(project["costo_hora"]))
            m3.metric("ROI", format_percent(project["roi"]))
            dias = project["dias_restantes"]
            m4.metric("Días restantes", str(dias) if dias is not None else "-")

            b1, b2, b3 = st.columns(3)
            ingreso_real = b1.number_input(
                "Actualizar ingreso real", min_value=0.0,
                value=float(project["ingreso_real"]),
                key=f"proj_ing_{project['id']}", label_visibility="collapsed",
            )
            if b2.button("Guardar ingreso", key=f"proj_save_{project['id']}"):
                service.update_project(project["id"], {"ingreso_real": ingreso_real})
                st.rerun()
            if b3.button("Eliminar", key=f"proj_del_{project['id']}"):
                service.delete_project(project["id"])
                st.rerun()
