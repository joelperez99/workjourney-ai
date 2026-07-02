"""Página Actividades: data entry, tabla editable, kanban y export."""
from __future__ import annotations

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder, GridUpdateMode

from components.cards import badge, section_title
from config.settings import ESTADOS_ACTIVIDAD, PRIORIDADES, TIPOS_TRABAJO
from services.activities_service import ActivitiesService
from services.clients_service import ClientsService
from services.export_service import to_csv_bytes, to_excel_bytes, to_pdf_bytes
from services.projects_service import ProjectsService
from utils.helpers import badge_color_for_status


def render(username: str):
    section_title("Actividades", "Registro detallado de tu trabajo diario.")

    service = ActivitiesService()
    clients = ClientsService().client_names()
    projects = ProjectsService().project_names()

    with st.expander("➕ Nueva actividad", expanded=False):
        with st.form("activity_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            titulo = c1.text_input("Título")
            proyecto = c2.selectbox("Proyecto", [""] + projects)
            cliente = c3.selectbox("Cliente", [""] + clients)

            c4, c5, c6 = st.columns(3)
            categoria = c4.selectbox("Categoría", TIPOS_TRABAJO)
            status = c5.selectbox("Status", ESTADOS_ACTIVIDAD)
            prioridad = c6.selectbox("Prioridad", PRIORIDADES)

            descripcion = st.text_area("Descripción", height=70)

            c7, c8 = st.columns(2)
            inicio = c7.text_input("Inicio (YYYY-MM-DD HH:MM)", placeholder="2026-07-01 09:00")
            fin = c8.text_input("Fin (YYYY-MM-DD HH:MM)", placeholder="2026-07-01 11:00")

            resultado = st.text_input("Resultado")

            c9, c10, c11 = st.columns(3)
            hit_conseguido = c9.selectbox("Hit conseguido", ["No", "Sí"])
            valor_hit = c10.number_input("Valor del hit", min_value=0.0, step=1.0)
            dinero_relacionado = c11.number_input("Dinero relacionado", min_value=0.0, step=10.0)

            c12, c13 = st.columns(2)
            url = c12.text_input("URL")
            archivos = c13.text_input("Archivos (links separados por coma)")

            notas = st.text_area("Notas", height=60)
            tags = st.text_input("Tags (separados por coma)")

            submitted = st.form_submit_button("Guardar actividad", type="primary")
            if submitted and titulo:
                service.create_activity(
                    {
                        "titulo": titulo, "proyecto": proyecto, "cliente": cliente,
                        "categoria": categoria, "descripcion": descripcion,
                        "inicio": inicio, "fin": fin, "resultado": resultado,
                        "status": status, "prioridad": prioridad,
                        "hit_conseguido": hit_conseguido, "valor_hit": valor_hit,
                        "dinero_relacionado": dinero_relacionado, "url": url,
                        "archivos": archivos, "notas": notas, "tags": tags,
                    },
                    created_by=username,
                )
                st.success("Actividad guardada.")
                st.rerun()

    df = service.list_activities()

    tab_table, tab_kanban = st.tabs(["📋 Tabla", "🗂️ Kanban"])

    with tab_table:
        if df.empty:
            st.info("Aún no hay actividades registradas.")
        else:
            f1, f2, f3, f4 = st.columns(4)
            proyecto_f = f1.selectbox("Proyecto", ["Todos"] + projects, key="a_f_proj")
            status_f = f2.selectbox("Status", ["Todos"] + ESTADOS_ACTIVIDAD, key="a_f_status")
            prioridad_f = f3.selectbox("Prioridad", ["Todos"] + PRIORIDADES, key="a_f_prio")
            search = f4.text_input("Buscar", key="a_search")

            filtered = df.copy()
            if proyecto_f != "Todos":
                filtered = filtered[filtered["proyecto"] == proyecto_f]
            if status_f != "Todos":
                filtered = filtered[filtered["status"] == status_f]
            if prioridad_f != "Todos":
                filtered = filtered[filtered["prioridad"] == prioridad_f]
            if search:
                mask = filtered.apply(
                    lambda r: search.lower() in str(r.to_dict()).lower(), axis=1
                )
                filtered = filtered[mask]

            group_by_project = st.checkbox("Agrupar por proyecto")

            display_df = filtered.drop(columns=["created_by"], errors="ignore")

            if group_by_project and not display_df.empty:
                for proj, group in display_df.groupby("proyecto"):
                    with st.expander(f"📁 {proj or 'Sin proyecto'} ({len(group)})", expanded=True):
                        _render_grid(group, key_suffix=proj or "none")
            else:
                _render_grid(display_df, key_suffix="all")

            st.markdown("**Exportar**")
            e1, e2, e3 = st.columns(3)
            e1.download_button(
                "⬇️ CSV", to_csv_bytes(filtered), "actividades.csv", "text/csv",
                use_container_width=True,
            )
            e2.download_button(
                "⬇️ Excel", to_excel_bytes(filtered, "Actividades"),
                "actividades.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            e3.download_button(
                "⬇️ PDF", to_pdf_bytes(filtered, "Actividades"), "actividades.pdf",
                "application/pdf", use_container_width=True,
            )

    with tab_kanban:
        _render_kanban(service)


def _render_grid(df: pd.DataFrame, key_suffix: str) -> None:
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False, filter=True, sortable=True, resizable=True)
    gb.configure_selection("single")
    grid_options = gb.build()
    AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.NO_UPDATE,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        theme="alpine",
        height=min(400, 60 + 32 * len(df)),
        key=f"grid_{key_suffix}",
    )


def _render_kanban(service: ActivitiesService) -> None:
    columns_data = service.kanban_columns()
    cols = st.columns(len(columns_data))
    for col, (status, df) in zip(cols, columns_data.items()):
        with col:
            st.markdown(
                f'<div class="wj-kanban-col"><div class="wj-kanban-title">{status} '
                f'({len(df)})</div>',
                unsafe_allow_html=True,
            )
            for _, row in df.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['titulo']}**")
                    st.caption(f"{row.get('proyecto','')} · {row.get('cliente','')}")
                    color = badge_color_for_status(row.get("prioridad", ""))
                    st.markdown(badge(row.get("prioridad", ""), "warning"), unsafe_allow_html=True)
                    new_status = st.selectbox(
                        "Mover a", ESTADOS_ACTIVIDAD,
                        index=ESTADOS_ACTIVIDAD.index(status) if status in ESTADOS_ACTIVIDAD else 0,
                        key=f"kanban_move_{row['id']}",
                        label_visibility="collapsed",
                    )
                    if new_status != status:
                        service.update_status(row["id"], new_status)
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
