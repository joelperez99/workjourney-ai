"""Menú lateral principal construido con streamlit-option-menu."""
from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

MENU_ITEMS = [
    ("Dashboard", "speedometer2"),
    ("Journey", "journal-richtext"),
    ("Actividades", "kanban"),
    ("Tiempo", "clock-history"),
    ("Finanzas", "cash-coin"),
    ("Objetivos", "flag"),
    ("Clientes", "people"),
    ("Proyectos", "folder2-open"),
    ("Analítica", "graph-up-arrow"),
    ("Insights AI", "stars"),
    ("Configuración", "gear"),
]


def render_sidebar(user_name: str, avatar_url: str = "") -> str:
    with st.sidebar:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:10px;padding:4px 4px 18px 4px;">
                <div style="width:34px;height:34px;border-radius:10px;
                            background:#6D5EF5;display:flex;align-items:center;
                            justify-content:center;color:white;font-weight:700;">W</div>
                <div style="font-weight:700;font-size:1.05rem;color:#1A1A2E;">WorkJourney AI</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        selected = option_menu(
            menu_title=None,
            options=[label for label, _ in MENU_ITEMS],
            icons=[icon for _, icon in MENU_ITEMS],
            default_index=0,
            key="main_menu",
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#8A8A9E", "font-size": "16px"},
                "nav-link": {
                    "font-size": "14px",
                    "font-weight": "600",
                    "text-align": "left",
                    "margin": "2px 0",
                    "border-radius": "10px",
                    "color": "#4B4B5A",
                    "padding": "10px 12px",
                },
                "nav-link-selected": {
                    "background-color": "#EFECFF",
                    "color": "#5544E0",
                },
            },
        )

        st.markdown("<div style='margin-top:auto;'></div>", unsafe_allow_html=True)
        st.divider()
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:30px;height:30px;border-radius:50%;background:#EFECFF;
                            display:flex;align-items:center;justify-content:center;
                            color:#5544E0;font-weight:700;font-size:0.85rem;">
                    {user_name[:1].upper() if user_name else "U"}
                </div>
                <div style="font-size:0.85rem;font-weight:600;color:#1A1A2E;">{user_name}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected
