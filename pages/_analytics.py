"""Página Analítica: filtros de rango, comparativas y métricas avanzadas."""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from components.cards import kpi_card, section_title
from components.charts import line_chart, pie_chart
from services.finance_service import FinanceService
from services.goals_service import GoalsService
from services.projects_service import ProjectsService
from services.time_service import TimeService
from utils.formatters import format_currency, format_hours, format_percent
from utils.helpers import compute_streak, filter_by_date_range, safe_float
from utils.formatters import parse_date


RANGE_PRESETS = {
    "Hoy": 0, "Últimos 7 días": 7, "Últimos 30 días": 30,
    "Este año": 365,
}


def render(username: str):
    section_title("Analítica", "Filtra por rango de fechas y compara periodos.")

    time_service = TimeService()
    finance_service = FinanceService()
    projects_service = ProjectsService()
    goals_service = GoalsService()

    c1, c2, c3 = st.columns([1, 1, 1])
    preset = c1.selectbox("Rango rápido", list(RANGE_PRESETS.keys()), index=2)
    today = dt.date.today()
    days = RANGE_PRESETS[preset]
    default_start = today - dt.timedelta(days=days) if days else today
    start_date = c2.date_input("Desde", value=default_start)
    end_date = c3.date_input("Hasta", value=today)

    time_df = time_service.list_entries()
    finance_df = finance_service.list_transactions()

    time_range = filter_by_date_range(time_df, "fecha", start_date, end_date)
    finance_range = filter_by_date_range(finance_df, "fecha", start_date, end_date)

    total_horas = time_range["duracion_horas"].apply(safe_float).sum() if not time_range.empty else 0.0
    totals = finance_service.totals(finance_range)
    valor_por_hora = (totals["ingresos"] / total_horas) if total_horas else 0.0

    billable = 0.0
    non_billable = 0.0
    if not time_range.empty:
        billable = time_range.loc[
            time_range["facturable"].astype(str).str.lower().isin(["sí", "si"]), "duracion_horas"
        ].apply(safe_float).sum()
        non_billable = total_horas - billable

    k1, k2, k3, k4 = st.columns(4)
    kpi_card("Valor generado / hora", format_currency(valor_por_hora), "💎")
    kpi_card("Horas facturables", format_hours(billable), "🧾")
    kpi_card("Horas no facturables", format_hours(non_billable), "🕳️")
    kpi_card("Eficiencia", format_percent(time_service.productive_ratio()), "⚡")

    dates = [d for d in time_df["fecha"].apply(parse_date).tolist() if d] if not time_df.empty else []
    streak = compute_streak(dates)
    goals_df = goals_service.list_goals()
    cumplimiento = goals_df["progreso"].mean() if not goals_df.empty else 0.0

    k5, k6 = st.columns(2)
    kpi_card("Racha de días productivos", f"{streak} días", "🔥")
    kpi_card("Cumplimiento de objetivos", format_percent(cumplimiento), "🎯")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            section_title("Comparativa de utilidad")
            monthly = finance_service.monthly_summary()
            line_chart(monthly, "mes", "utilidad")
    with col_b:
        with st.container(border=True):
            section_title("ROI por proyecto")
            stats = projects_service.project_stats()
            if not stats.empty:
                pie_chart(stats, "nombre", "roi")
            else:
                st.info("Sin proyectos registrados.")

    with st.container(border=True):
        section_title("Detalle del periodo seleccionado")
        st.dataframe(
            time_range.drop(columns=["created_by", "created_at"], errors="ignore"),
            use_container_width=True, hide_index=True,
        )
