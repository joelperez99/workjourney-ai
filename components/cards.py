"""Componentes de tarjetas reutilizables (KPI, badge, progress bar)."""
from __future__ import annotations

import streamlit as st

from config.settings import COLORS


def kpi_card(
    label: str,
    value: str,
    icon: str = "📊",
    delta: str | None = None,
    delta_positive: bool = True,
    spark_values: list[float] | None = None,
) -> None:
    delta_html = ""
    if delta:
        cls = "up" if delta_positive else "down"
        arrow = "▲" if delta_positive else "▼"
        delta_html = f'<div class="wj-kpi-delta {cls}">{arrow} {delta}</div>'

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="wj-kpi">
                <div class="wj-kpi-icon">{icon}</div>
                <div class="wj-kpi-label">{label}</div>
                <div class="wj-kpi-value">{value}</div>
                {delta_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if spark_values and len(spark_values) >= 2:
            from components.sparkline import sparkline

            spark_color = COLORS["success"] if delta_positive else COLORS["primary"]
            sparkline(spark_values, color=spark_color)


def badge(text: str, kind: str = "gray") -> str:
    return f'<span class="wj-badge {kind}">{text}</span>'


def render_badge(text: str, kind: str = "gray") -> None:
    st.markdown(badge(text, kind), unsafe_allow_html=True)


def progress_bar(percent: float, color: str = "primary") -> None:
    percent = max(0, min(100, percent))
    hex_color = COLORS.get(color, COLORS["primary"])
    st.markdown(
        f"""
        <div class="wj-progress-track">
            <div class="wj-progress-fill" style="width:{percent}%; background:{hex_color};"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="wj-page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="wj-page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def empty_state(message: str, icon: str = "🗂️") -> None:
    st.markdown(
        f"""
        <div class="wj-card" style="text-align:center; padding:40px;">
            <div style="font-size:2.2rem;">{icon}</div>
            <div style="color:{COLORS['gray']}; margin-top:8px;">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
