"""Centro de notificaciones (popover en la barra superior)."""
from __future__ import annotations

import streamlit as st

from services.notifications_service import NotificationsService


def render_notifications() -> None:
    service = NotificationsService()
    notifications = service.generate_dynamic_notifications()
    count = len(notifications)
    label = f"🔔 Notificaciones ({count})" if count else "🔔 Notificaciones"

    with st.popover(label, use_container_width=False):
        if not notifications:
            st.caption("No tienes notificaciones pendientes. 🎉")
            return
        for n in notifications:
            st.markdown(
                f"""
                <div class="wj-card-flat">
                    <div style="font-weight:700;">{n['icono']} {n['titulo']}</div>
                    <div style="color:#4B4B5A;font-size:0.85rem;margin-top:2px;">{n['mensaje']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
