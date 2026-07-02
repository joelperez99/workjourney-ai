"""Mini gráficas (sparkline) y anillo de progreso circular, estilo mockup."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config.settings import COLORS


def sparkline(values: list[float], color: str = COLORS["primary"]) -> None:
    if not values or len(values) < 2:
        return
    fig = go.Figure(
        go.Scatter(
            y=values, mode="lines", line=dict(color=color, width=2.5),
            fill="tozeroy", fillcolor=color + "22",
        )
    )
    fig.update_layout(
        height=46,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def circular_progress(percent: float, label: str, sub_label: str = "", color: str = COLORS["primary"]) -> None:
    percent = max(0, min(100, percent))
    fig = go.Figure(
        go.Pie(
            values=[percent, 100 - percent],
            hole=0.75,
            marker=dict(colors=[color, COLORS["gray_light"]]),
            textinfo="none",
            sort=False,
            direction="clockwise",
        )
    )
    fig.update_layout(
        height=170,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        annotations=[
            dict(text=f"<b>{label}</b>", x=0.5, y=0.56, font_size=18, showarrow=False),
            dict(text=sub_label, x=0.5, y=0.38, font_size=11, showarrow=False, font_color=COLORS["gray"]),
        ],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
