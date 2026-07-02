"""Quick Add (+): registrar actividad, iniciar timer o agregar ingreso en un clic."""
from __future__ import annotations

import datetime as dt

import streamlit as st

from config.settings import CATEGORIAS_FINANZAS_INGRESO, TIPOS_TRABAJO
from services.activities_service import ActivitiesService
from services.clients_service import ClientsService
from services.finance_service import FinanceService
from services.projects_service import ProjectsService
from services.time_service import TimeService
from utils.formatters import today_str


def render_quick_add(username: str) -> None:
    with st.popover("➕ Quick Add", use_container_width=False):
        tab_activity, tab_timer, tab_income = st.tabs(
            ["📝 Actividad", "⏱️ Timer", "💵 Ingreso"]
        )

        clients = ClientsService().client_names()
        projects = ProjectsService().project_names()

        with tab_activity:
            with st.form("quick_activity_form", clear_on_submit=True):
                titulo = st.text_input("Título")
                proyecto = st.selectbox("Proyecto", [""] + projects)
                cliente = st.selectbox("Cliente", [""] + clients)
                categoria = st.selectbox("Categoría", TIPOS_TRABAJO)
                status = st.selectbox("Status", ["Pendiente", "En progreso", "Completada"])
                submitted = st.form_submit_button("Guardar actividad", type="primary")
                if submitted and titulo:
                    ActivitiesService().create_activity(
                        {
                            "titulo": titulo,
                            "proyecto": proyecto,
                            "cliente": cliente,
                            "categoria": categoria,
                            "status": status,
                        },
                        created_by=username,
                    )
                    st.success("Actividad guardada.")
                    st.rerun()

        with tab_timer:
            proyecto_t = st.selectbox("Proyecto", [""] + projects, key="qa_timer_proj")
            cliente_t = st.selectbox("Cliente", [""] + clients, key="qa_timer_client")
            actividad_t = st.text_input("¿En qué estás trabajando?", key="qa_timer_activity")
            tipo_t = st.selectbox("Tipo de trabajo", TIPOS_TRABAJO, key="qa_timer_type")
            if not TimeService.has_active_timer():
                if st.button("▶️ Iniciar temporizador", type="primary", key="qa_start_timer"):
                    TimeService.start_timer(proyecto_t, cliente_t, actividad_t, tipo_t)
                    st.success("Temporizador iniciado.")
                    st.rerun()
            else:
                st.info("Ya hay un temporizador activo. Ve al módulo Tiempo para gestionarlo.")

        with tab_income:
            with st.form("quick_income_form", clear_on_submit=True):
                monto = st.number_input("Monto", min_value=0.0, step=10.0)
                cliente_i = st.selectbox("Cliente", [""] + clients, key="qa_income_client")
                proyecto_i = st.selectbox("Proyecto", [""] + projects, key="qa_income_proj")
                categoria_i = st.selectbox("Categoría", CATEGORIAS_FINANZAS_INGRESO)
                submitted_i = st.form_submit_button("Guardar ingreso", type="primary")
                if submitted_i and monto > 0:
                    FinanceService().create_transaction(
                        {
                            "tipo": "Ingreso",
                            "fecha": today_str(),
                            "cliente": cliente_i,
                            "proyecto": proyecto_i,
                            "monto": monto,
                            "categoria": categoria_i,
                        },
                        created_by=username,
                    )
                    st.success("Ingreso registrado.")
                    st.rerun()
