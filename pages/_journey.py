"""Página Journey: diario profesional con timeline estilo Notion."""
from __future__ import annotations

import streamlit as st

from components.cards import section_title
from components.timeline import render_timeline
from config.settings import PRIORIDADES, TIPOS_TRABAJO
from services.clients_service import ClientsService
from services.journey_service import JourneyService
from services.projects_service import ProjectsService
from utils.formatters import today_str
from utils.validators import validate_required_fields


def render(username: str):
    section_title("Journey", "Tu diario profesional — cada entrada se convierte en estadísticas.")

    journey_service = JourneyService()
    clients = ClientsService().client_names()
    projects = ProjectsService().project_names()

    col_main, col_side = st.columns([2.3, 1])

    with col_side:
        with st.container(border=True):
            st.markdown("**Nueva entrada**")
            with st.form("journey_form", clear_on_submit=True):
                fecha = st.date_input("Fecha")
                c1, c2 = st.columns(2)
                hora_inicio = c1.time_input("Hora inicio")
                hora_fin = c2.time_input("Hora fin")

                proyecto = st.selectbox("Proyecto", [""] + projects)
                cliente = st.selectbox("Cliente", [""] + clients)
                objetivo = st.text_input("Objetivo")
                actividad = st.text_input("Actividad")
                descripcion = st.text_area("Descripción", height=70)
                resultado = st.text_area("Resultado obtenido", height=60)
                impacto = st.selectbox("Impacto", ["Bajo", "Medio", "Alto"])
                dificultad = st.selectbox("Dificultad", ["Baja", "Media", "Alta"])
                estado = st.selectbox("Estado", ["Completado", "En progreso", "Bloqueado"])
                aprendizaje = st.text_area("Aprendizaje", height=60)

                c3, c4, c5 = st.columns(3)
                energia = c3.slider("Energía", 1, 10, 7)
                motivacion = c4.slider("Motivación", 1, 10, 7)
                estres = c5.slider("Estrés", 1, 10, 3)

                prioridad = st.selectbox("Prioridad", PRIORIDADES)
                tipo_trabajo = st.selectbox("Tipo de trabajo", TIPOS_TRABAJO)
                tags = st.text_input("Tags (separados por coma)")
                dinero_generado = st.number_input("Dinero generado", min_value=0.0, step=10.0)

                submitted = st.form_submit_button("Guardar entrada", type="primary", use_container_width=True)

                if submitted:
                    data = {
                        "fecha": str(fecha),
                        "hora_inicio": hora_inicio.strftime("%H:%M"),
                        "hora_fin": hora_fin.strftime("%H:%M"),
                        "proyecto": proyecto,
                        "cliente": cliente,
                        "objetivo": objetivo,
                        "actividad": actividad,
                        "descripcion": descripcion,
                        "resultado": resultado,
                        "impacto": impacto,
                        "dificultad": dificultad,
                        "estado": estado,
                        "aprendizaje": aprendizaje,
                        "energia": energia,
                        "motivacion": motivacion,
                        "estres": estres,
                        "prioridad": prioridad,
                        "tipo_trabajo": tipo_trabajo,
                        "tags": tags,
                        "dinero_generado": dinero_generado,
                    }
                    missing = validate_required_fields(data, ["actividad"])
                    if missing:
                        st.error("Completa al menos el campo 'Actividad'.")
                    else:
                        journey_service.create_entry(data, created_by=username)
                        st.success("Entrada guardada en tu Journey.")
                        st.rerun()

    with col_main:
        df = journey_service.list_entries()

        f1, f2, f3 = st.columns(3)
        cliente_filter = f1.selectbox("Filtrar por cliente", ["Todos"] + clients, key="j_filter_client")
        proyecto_filter = f2.selectbox("Filtrar por proyecto", ["Todos"] + projects, key="j_filter_project")
        tipo_filter = f3.selectbox("Filtrar por tipo", ["Todos"] + TIPOS_TRABAJO, key="j_filter_type")

        filtered = df
        if not filtered.empty:
            if cliente_filter != "Todos":
                filtered = filtered[filtered["cliente"] == cliente_filter]
            if proyecto_filter != "Todos":
                filtered = filtered[filtered["proyecto"] == proyecto_filter]
            if tipo_filter != "Todos":
                filtered = filtered[filtered["tipo_trabajo"] == tipo_filter]

        def on_delete(record_id: str):
            journey_service.delete_entry(record_id)
            st.rerun()

        render_timeline(filtered, on_delete=on_delete)
