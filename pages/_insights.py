"""Página Insights AI: observaciones generadas 100% con Python (sin APIs)."""
from __future__ import annotations

import streamlit as st

from components.cards import section_title
from services.insights_service import InsightsService


def render(username: str):
    section_title("Insights AI", "Análisis automático de tu productividad — generado localmente, sin APIs externas.")

    service = InsightsService()
    insights = service.generate_insights()

    cols = st.columns(2)
    for i, insight in enumerate(insights):
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="display:flex;gap:12px;align-items:flex-start;">
                        <div style="font-size:1.6rem;">{insight['icon']}</div>
                        <div>
                            <div style="font-weight:700;color:#1A1A2E;">{insight['title']}</div>
                            <div style="color:#4B4B5A;font-size:0.9rem;margin-top:4px;">{insight['message']}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
