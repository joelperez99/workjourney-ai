"""Página Dashboard: KPIs, gráficas principales y panel lateral 'Hoy'."""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from components.cards import empty_state, kpi_card, progress_bar, section_title
from components.charts import bar_chart, heatmap_chart, pie_chart
from components.sparkline import circular_progress
from config.settings import COLORS
from services.activities_service import ActivitiesService
from services.clients_service import ClientsService
from services.finance_service import FinanceService
from services.goals_service import GoalsService
from services.journey_service import JourneyService
from services.projects_service import ProjectsService
from services.time_service import TimeService
from utils.formatters import format_currency, format_hours, format_percent, today_str
from utils.helpers import safe_float, week_bounds


def render(username: str, display_name: str):
    time_service = TimeService()
    journey_service = JourneyService()
    activities_service = ActivitiesService()
    finance_service = FinanceService()
    clients_service = ClientsService()
    projects_service = ProjectsService()
    goals_service = GoalsService()

    hour = dt.datetime.now().hour
    saludo = "Buenos días" if hour < 12 else "Buenas tardes" if hour < 19 else "Buenas noches"
    st.markdown(
        f'<div class="wj-page-title">{saludo}, {display_name.split(" ")[0]} 👋</div>'
        f'<div class="wj-page-subtitle">Así va tu journey hoy — {dt.date.today().strftime("%d de %B, %Y")}</div>',
        unsafe_allow_html=True,
    )

    time_df = time_service.list_entries()
    activities_df = activities_service.list_activities()
    journey_df = journey_service.list_entries()
    finance_totals = finance_service.totals()
    clients_df = clients_service.list_clients()
    projects_df = projects_service.list_projects()

    week_start, week_end = week_bounds()
    time_df = time_df.copy()
    if not time_df.empty:
        time_df["_fecha_dt"] = pd.to_datetime(time_df["fecha"], errors="coerce").dt.date
        week_time = time_df[(time_df["_fecha_dt"] >= week_start) & (time_df["_fecha_dt"] <= week_end)]
    else:
        week_time = time_df

    total_horas = week_time["duracion_horas"].apply(safe_float).sum() if not week_time.empty else 0.0
    total_hits = journey_service.total_hits()
    total_ingresos = finance_totals["ingresos"]
    total_actividades = len(activities_df)
    productividad = time_service.productive_ratio()
    clientes_activos = len(clients_df[clients_df["estado"] == "Activo"]) if not clients_df.empty else 0
    proyectos_activos = len(projects_df[projects_df["estado"] == "Activo"]) if not projects_df.empty else 0

    # ------------------------------------------------------------------
    # KPI row
    # ------------------------------------------------------------------
    k1, k2, k3, k4 = st.columns(4)
    spark_base = [max(total_horas * f, 0) for f in (0.6, 0.75, 0.5, 0.9, 0.7, 1.0, 0.85)]
    with k1:
        kpi_card("Horas trabajadas (semana)", format_hours(total_horas), "🕐", spark_values=spark_base)
    with k2:
        kpi_card("Hits logrados", str(total_hits), "🎯", spark_values=[max(total_hits * f, 0) for f in (0.5, 0.7, 0.6, 0.8, 0.9, 1, 0.95)])
    with k3:
        kpi_card("Ingresos", format_currency(total_ingresos), "💰", spark_values=[max(total_ingresos * f, 0) for f in (0.4, 0.55, 0.5, 0.7, 0.8, 0.9, 1)])
    with k4:
        kpi_card("Actividades", str(total_actividades), "✅", spark_values=[max(total_actividades * f, 0) for f in (0.6, 0.65, 0.7, 0.75, 0.85, 0.9, 1)])

    k5, k6, k7, k8 = st.columns(4)
    with k5:
        kpi_card("Productividad", format_percent(productividad), "⚡")
    with k6:
        promedio_diario = total_horas / 7 if total_horas else 0
        kpi_card("Promedio diario", format_hours(promedio_diario), "📊")
    with k7:
        kpi_card("Clientes activos", str(clientes_activos), "🤝")
    with k8:
        kpi_card("Proyectos activos", str(proyectos_activos), "📁")

    # ------------------------------------------------------------------
    # Gráfica principal + panel "Hoy"
    # ------------------------------------------------------------------
    col_main, col_side = st.columns([2.3, 1])

    with col_main:
        with st.container(border=True):
            section_title("Tu journey esta semana")
            if not week_time.empty:
                by_day = week_time.copy()
                by_day["dia"] = pd.to_datetime(by_day["_fecha_dt"]).dt.strftime("%a %d")
                agg = by_day.groupby("dia", as_index=False)["duracion_horas"].apply(
                    lambda s: pd.to_numeric(s, errors="coerce").sum()
                )
                bar_chart(agg, "dia", "duracion_horas", title="")
            else:
                empty_state("Aún no registras tiempo esta semana.")

        with st.container(border=True):
            section_title("Distribución de tiempo")
            if not time_df.empty:
                dist = time_service.hours_by("tipo")
                pie_chart(dist, "tipo", "horas")
            else:
                empty_state("Sin datos de tiempo todavía.")

    with col_side:
        with st.container(border=True):
            today_time = time_df[time_df["_fecha_dt"] == dt.date.today()] if not time_df.empty else time_df
            today_hours = today_time["duracion_horas"].apply(safe_float).sum() if not today_time.empty else 0.0
            objetivo_dia = 8.0
            pct = min((today_hours / objetivo_dia) * 100, 100) if objetivo_dia else 0
            st.markdown(f"**Hoy · {dt.date.today().strftime('%d de %B')}**")
            circular_progress(pct, format_hours(today_hours), f"de {format_hours(objetivo_dia)} objetivo")

            today_journey = journey_service.today_entries()
            today_hits = journey_service.total_hits(today_journey)
            today_income = journey_service.total_income(today_journey)

            c1, c2 = st.columns(2)
            c1.metric("Hits", today_hits)
            c2.metric("Ingresos", format_currency(today_income))

        with st.container(border=True):
            st.markdown("**Objetivos del día**")
            goals_df = goals_service.list_goals()
            if goals_df.empty:
                st.caption("No tienes objetivos activos.")
            else:
                for _, g in goals_df.head(4).iterrows():
                    st.caption(f"{g['objetivo']}")
                    progress_bar(g.get("progreso", 0))

    # ------------------------------------------------------------------
    # Gráficas secundarias
    # ------------------------------------------------------------------
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            section_title("Horas por proyecto")
            bar_chart(time_service.hours_by("proyecto"), "proyecto", "horas", horizontal=True)
    with col_b:
        with st.container(border=True):
            section_title("Ingresos por cliente")
            by_client = finance_service.by_client()
            bar_chart(by_client, "cliente", "monto_num", horizontal=True)

    col_c, col_d = st.columns(2)
    with col_c:
        with st.container(border=True):
            section_title("Ingresos por proyecto")
            bar_chart(finance_service.by_project(), "proyecto", "monto_num", horizontal=True)
    with col_d:
        with st.container(border=True):
            section_title("Actividades por categoría")
            if not activities_df.empty:
                by_cat = activities_df.groupby("categoria", as_index=False).size()
                pie_chart(by_cat, "categoria", "size")
            else:
                empty_state("Sin actividades registradas.")

    with st.container(border=True):
        section_title("Heatmap de productividad", "Horas registradas por día de la semana y hora")
        heatmap_chart(_build_heatmap_matrix(time_df))


def _build_heatmap_matrix(time_df: pd.DataFrame) -> pd.DataFrame:
    if time_df.empty:
        return pd.DataFrame()
    df = time_df.copy()
    df["_fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["_fecha_dt"])
    if df.empty:
        return pd.DataFrame()
    df["dia"] = df["_fecha_dt"].dt.day_name()
    df["hora"] = df["inicio"].astype(str).str.slice(0, 2)
    df["horas"] = df["duracion_horas"].apply(safe_float)
    dias_orden = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = df.pivot_table(index="dia", columns="hora", values="horas", aggfunc="sum", fill_value=0)
    pivot = pivot.reindex(dias_orden).fillna(0)
    pivot.index = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    return pivot
