"""Página Objetivos: creación y seguimiento de metas."""
from __future__ import annotations

import streamlit as st

from components.cards import badge, empty_state, progress_bar, section_title
from services.goals_service import GoalsService
from utils.formatters import format_date


def render(username: str):
    section_title("Objetivos", "Define metas y monitorea tu avance.")

    service = GoalsService()

    with st.expander("➕ Nuevo objetivo", expanded=False):
        with st.form("goal_form", clear_on_submit=True):
            objetivo = st.text_input("Objetivo")
            descripcion = st.text_area("Descripción", height=60)
            c1, c2, c3 = st.columns(3)
            fecha_limite = c1.date_input("Fecha límite")
            meta = c2.number_input("Meta", min_value=0.0, step=1.0)
            unidad = c3.text_input("Unidad (horas, $, hits...)", value="unidades")
            categoria = st.selectbox("Categoría", ["Ingresos", "Horas", "Hits", "Clientes", "Otro"])

            submitted = st.form_submit_button("Crear objetivo", type="primary")
            if submitted and objetivo:
                service.create_goal(
                    {
                        "objetivo": objetivo, "descripcion": descripcion,
                        "fecha_limite": str(fecha_limite), "meta": meta,
                        "unidad": unidad, "categoria": categoria,
                    },
                    created_by=username,
                )
                st.success("Objetivo creado.")
                st.rerun()

    df = service.list_goals()
    if df.empty:
        empty_state("Aún no tienes objetivos. ¡Crea el primero!")
        return

    cols = st.columns(2)
    for i, (_, goal) in enumerate(df.iterrows()):
        with cols[i % 2]:
            with st.container(border=True):
                color = service.status_color(goal)
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                    f"<b>{goal['objetivo']}</b>{badge(goal.get('estado','En progreso'), color)}</div>",
                    unsafe_allow_html=True,
                )
                st.caption(goal.get("descripcion", ""))
                progress_bar(goal.get("progreso", 0), color=color)
                st.caption(
                    f"{goal['valor_num']:.0f} / {goal['meta_num']:.0f} {goal.get('unidad','')} · "
                    f"Vence: {format_date(goal.get('fecha_limite'))} · {goal.get('progreso',0)}%"
                )

                c1, c2, c3 = st.columns(3)
                new_value = c1.number_input(
                    "Actualizar valor", min_value=0.0, value=float(goal["valor_num"]),
                    key=f"goal_val_{goal['id']}", label_visibility="collapsed",
                )
                if c2.button("Guardar", key=f"goal_save_{goal['id']}"):
                    service.update_progress(goal["id"], new_value)
                    st.rerun()
                if c3.button("Eliminar", key=f"goal_del_{goal['id']}"):
                    service.delete_goal(goal["id"])
                    st.rerun()
