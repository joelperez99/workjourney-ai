"""Página Tiempo: temporizador, registro manual, calendario, listas y gráficas."""
from __future__ import annotations

import calendar
import datetime as dt

import pandas as pd
import streamlit as st

from components.cards import empty_state, kpi_card, section_title
from components.charts import bar_chart
from config.settings import TIPOS_TRABAJO
from services.clients_service import ClientsService
from services.projects_service import ProjectsService
from services.time_service import TimeService
from utils.formatters import duration_hours, format_hours, format_percent
from utils.helpers import safe_float, week_bounds


def render(username: str):
    section_title("Tiempo", "Temporizador, registros y análisis de cómo usas tu tiempo.")

    service = TimeService()
    clients = ClientsService().client_names()
    projects = ProjectsService().project_names()

    _render_timer_panel(service, clients, projects, username)

    df = service.list_entries()
    total_horas = df["duracion_horas"].apply(safe_float).sum() if not df.empty else 0.0
    productividad = service.productive_ratio()
    tiempo_perdido = df.loc[df["tipo"] == "Administrativo", "duracion_horas"].apply(safe_float).sum() if not df.empty else 0.0

    k1, k2, k3, k4 = st.columns(4)
    kpi_card("Tiempo total", format_hours(total_horas), "⏱️")
    kpi_card("Productividad", format_percent(productividad), "⚡")
    kpi_card("Tiempo profundo", format_hours(
        df.loc[df["tipo"] == "Profundo", "duracion_horas"].apply(safe_float).sum() if not df.empty else 0
    ), "🧠")
    kpi_card("Tiempo administrativo", format_hours(tiempo_perdido), "🗂️")

    tab_list, tab_calendar, tab_week, tab_manual = st.tabs(
        ["📋 Lista", "📅 Calendario", "📆 Semanal", "✍️ Registro manual"]
    )

    with tab_list:
        if df.empty:
            empty_state("Sin registros de tiempo todavía.")
        else:
            st.dataframe(
                df.drop(columns=["created_by", "created_at"], errors="ignore"),
                use_container_width=True, hide_index=True,
            )

    with tab_calendar:
        _render_calendar(df)

    with tab_week:
        _render_weekly_view(df)

    with tab_manual:
        _render_manual_form(service, clients, projects, username)

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            section_title("Tiempo por cliente")
            bar_chart(service.hours_by("cliente"), "cliente", "horas", horizontal=True)
    with col_b:
        with st.container(border=True):
            section_title("Tiempo por proyecto")
            bar_chart(service.hours_by("proyecto"), "proyecto", "horas", horizontal=True)


def _render_timer_panel(service: TimeService, clients, projects, username):
    with st.container(border=True):
        st.markdown("**⏱️ Temporizador**")
        if not TimeService.has_active_timer():
            c1, c2, c3, c4 = st.columns(4)
            proyecto = c1.selectbox("Proyecto", [""] + projects, key="t_proj")
            cliente = c2.selectbox("Cliente", [""] + clients, key="t_client")
            actividad = c3.text_input("Actividad", key="t_activity")
            tipo = c4.selectbox("Tipo", TIPOS_TRABAJO, key="t_type")
            if st.button("▶️ Iniciar", type="primary"):
                TimeService.start_timer(proyecto, cliente, actividad, tipo)
                st.rerun()
        else:
            timer = st.session_state["active_timer"]
            elapsed = service.get_elapsed_seconds()
            hours, rem = divmod(int(elapsed), 3600)
            minutes, seconds = divmod(rem, 60)
            st.markdown(
                f"<div style='font-size:2rem;font-weight:700;'>{hours:02d}:{minutes:02d}:{seconds:02d}</div>",
                unsafe_allow_html=True,
            )
            st.caption(f"{timer['actividad'] or 'Sin descripción'} · {timer['proyecto']} · {timer['cliente']}")

            c1, c2, c3 = st.columns(3)
            if not timer["paused"]:
                if c1.button("⏸️ Pausar"):
                    TimeService.pause_timer()
                    st.rerun()
            else:
                if c1.button("▶️ Reanudar"):
                    TimeService.resume_timer()
                    st.rerun()
            facturable = c2.selectbox("Facturable", ["Sí", "No"], key="t_billable")
            if c3.button("⏹️ Detener", type="primary"):
                service.stop_timer(created_by=username, facturable=facturable)
                st.success("Tiempo guardado.")
                st.rerun()

            st_autorefresh_hint()


def st_autorefresh_hint():
    st.caption("El cronómetro se actualiza al interactuar con la página. Usa 'Pausar/Detener' para fijar el tiempo exacto.")


def _render_manual_form(service: TimeService, clients, projects, username):
    with st.form("manual_time_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        fecha = c1.date_input("Fecha")
        tipo = c2.selectbox("Tipo", TIPOS_TRABAJO)

        c3, c4 = st.columns(2)
        proyecto = c3.selectbox("Proyecto", [""] + projects)
        cliente = c4.selectbox("Cliente", [""] + clients)

        c5, c6 = st.columns(2)
        inicio = c5.time_input("Inicio")
        fin = c6.time_input("Fin")

        actividad = st.text_input("Actividad")
        facturable = st.selectbox("Facturable", ["Sí", "No"])
        notas = st.text_area("Notas", height=60)

        submitted = st.form_submit_button("Guardar registro", type="primary")
        if submitted:
            horas = duration_hours(inicio.strftime("%H:%M"), fin.strftime("%H:%M"))
            service.create_manual_entry(
                {
                    "fecha": str(fecha), "proyecto": proyecto, "cliente": cliente,
                    "actividad": actividad, "inicio": inicio.strftime("%H:%M"),
                    "fin": fin.strftime("%H:%M"), "duracion_horas": horas,
                    "tipo": tipo, "facturable": facturable, "notas": notas,
                },
                created_by=username,
            )
            st.success("Registro guardado.")
            st.rerun()


def _render_calendar(df: pd.DataFrame):
    today = dt.date.today()
    year = st.session_state.get("time_cal_year", today.year)
    month = st.session_state.get("time_cal_month", today.month)

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⬅️ Mes anterior"):
        month -= 1
        if month == 0:
            month, year = 12, year - 1
        st.session_state["time_cal_year"], st.session_state["time_cal_month"] = year, month
        st.rerun()
    c2.markdown(
        f"<div style='text-align:center;font-weight:700;'>"
        f"{calendar.month_name[month]} {year}</div>", unsafe_allow_html=True,
    )
    if c3.button("Mes siguiente ➡️"):
        month += 1
        if month == 13:
            month, year = 1, year + 1
        st.session_state["time_cal_year"], st.session_state["time_cal_month"] = year, month
        st.rerun()

    daily_hours: dict[int, float] = {}
    if not df.empty:
        df = df.copy()
        df["_fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
        month_df = df[(df["_fecha_dt"].dt.year == year) & (df["_fecha_dt"].dt.month == month)]
        for day, group in month_df.groupby(month_df["_fecha_dt"].dt.day):
            daily_hours[day] = group["duracion_horas"].apply(safe_float).sum()

    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(year, month)
    day_labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    header_cols = st.columns(7)
    for hc, label in zip(header_cols, day_labels):
        hc.markdown(f"<div style='text-align:center;color:#8A8A9E;font-size:0.8rem;'>{label}</div>", unsafe_allow_html=True)

    for week in weeks:
        cols = st.columns(7)
        for col, day in zip(cols, week):
            if day == 0:
                col.markdown("&nbsp;", unsafe_allow_html=True)
                continue
            hours = daily_hours.get(day, 0)
            intensity = "#EFECFF" if hours == 0 else ("#6D5EF5" if hours > 4 else "#B8AEF9")
            text_color = "#1A1A2E" if hours <= 4 else "#FFFFFF"
            col.markdown(
                f"""
                <div style="background:{intensity};color:{text_color};border-radius:10px;
                            padding:8px 4px;text-align:center;font-size:0.78rem;min-height:52px;">
                    <div style="font-weight:700;">{day}</div>
                    <div>{f'{hours:.1f}h' if hours else ''}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.caption("Vista de calendario mensual. Usa 'Registro manual' para reprogramar o agregar tiempo en un día específico.")


def _render_weekly_view(df: pd.DataFrame):
    start, end = week_bounds()
    st.caption(f"Semana del {start.strftime('%d %b')} al {end.strftime('%d %b')}")
    if df.empty:
        empty_state("Sin registros esta semana.")
        return
    df = df.copy()
    df["_fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
    week_df = df[(df["_fecha_dt"] >= start) & (df["_fecha_dt"] <= end)]
    if week_df.empty:
        empty_state("Sin registros esta semana.")
        return
    agg = week_df.groupby("_fecha_dt", as_index=False)["duracion_horas"].apply(
        lambda s: pd.to_numeric(s, errors="coerce").sum()
    )
    agg["_fecha_dt"] = agg["_fecha_dt"].astype(str)
    bar_chart(agg, "_fecha_dt", "duracion_horas", title="Horas por día")
