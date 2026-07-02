"""Gráficas Plotly reutilizables con el estilo visual de WorkJourney AI."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config.settings import CHART_COLORWAY, COLORS

BASE_LAYOUT = dict(
    font=dict(family="Inter, sans-serif", color=COLORS["text"], size=12),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=40, b=10),
    colorway=CHART_COLORWAY,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def _apply_theme(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(**BASE_LAYOUT, title=dict(text=title, font=dict(size=14)))
    fig.update_xaxes(showgrid=False, showline=True, linecolor=COLORS["border"])
    fig.update_yaxes(showgrid=True, gridcolor=COLORS["border"], zeroline=False)
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "", horizontal: bool = False):
    if df.empty:
        st.info("Sin datos suficientes todavía.")
        return
    fig = px.bar(df, x=y if horizontal else x, y=x if horizontal else y,
                 orientation="h" if horizontal else "v")
    fig.update_traces(marker_color=COLORS["primary"], marker_cornerradius=8)
    st.plotly_chart(_apply_theme(fig, title), use_container_width=True)


def line_chart(df: pd.DataFrame, x: str, y: str, title: str = ""):
    if df.empty:
        st.info("Sin datos suficientes todavía.")
        return
    fig = px.line(df, x=x, y=y, markers=True)
    fig.update_traces(line=dict(color=COLORS["primary"], width=3))
    st.plotly_chart(_apply_theme(fig, title), use_container_width=True)


def pie_chart(df: pd.DataFrame, names: str, values: str, title: str = ""):
    if df.empty:
        st.info("Sin datos suficientes todavía.")
        return
    fig = px.pie(df, names=names, values=values, hole=0.55)
    st.plotly_chart(_apply_theme(fig, title), use_container_width=True)


def heatmap_chart(matrix: pd.DataFrame, title: str = "Heatmap de productividad"):
    if matrix.empty:
        st.info("Sin datos suficientes todavía.")
        return
    fig = go.Figure(
        data=go.Heatmap(
            z=matrix.values,
            x=list(matrix.columns),
            y=list(matrix.index),
            colorscale=[[0, COLORS["gray_light"]], [1, COLORS["primary"]]],
            showscale=False,
            hoverongaps=False,
        )
    )
    st.plotly_chart(_apply_theme(fig, title), use_container_width=True)


def multi_bar_chart(df: pd.DataFrame, x: str, y_cols: list[str], title: str = ""):
    if df.empty:
        st.info("Sin datos suficientes todavía.")
        return
    fig = go.Figure()
    for i, col in enumerate(y_cols):
        fig.add_bar(x=df[x], y=df[col], name=col, marker_color=CHART_COLORWAY[i % len(CHART_COLORWAY)])
    fig.update_layout(barmode="group")
    st.plotly_chart(_apply_theme(fig, title), use_container_width=True)
