"""Timeline estilo Notion para el módulo Journey."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.formatters import duration_hours, format_currency, format_hours
from utils.helpers import safe_float

TIPO_ICONS = {
    "Profundo": "🧠", "Administrativo": "🗂️", "Ventas": "💼",
    "Marketing": "📣", "Reunión": "🤝", "Programación": "💻",
    "Diseño": "🎨", "Investigación": "🔎", "Otro": "✨",
}


def render_timeline(df: pd.DataFrame, on_edit=None, on_delete=None) -> None:
    if df.empty:
        st.info("Aún no hay registros en tu Journey. ¡Agrega el primero!")
        return

    for _, row in df.iterrows():
        icon = TIPO_ICONS.get(row.get("tipo_trabajo", ""), "✨")
        horas = duration_hours(row.get("hora_inicio", ""), row.get("hora_fin", ""))
        dinero = safe_float(row.get("dinero_generado"))

        with st.container():
            st.markdown('<div class="wj-timeline-item">', unsafe_allow_html=True)
            st.markdown('<div class="wj-timeline-dot"></div>', unsafe_allow_html=True)

            col_main, col_actions = st.columns([9, 1])
            with col_main:
                st.markdown(
                    f"""
                    <div class="wj-card-flat">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div style="font-weight:700;">{icon} {row.get('actividad', 'Actividad')}</div>
                            <div style="color:#8A8A9E;font-size:0.8rem;">
                                {row.get('fecha','')} · {row.get('hora_inicio','')}–{row.get('hora_fin','')}
                                ({format_hours(horas)})
                            </div>
                        </div>
                        <div style="color:#4B4B5A;font-size:0.88rem;margin-top:6px;">
                            {row.get('descripcion','')}
                        </div>
                        <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;">
                            <span class="wj-badge primary">{row.get('proyecto','') or 'Sin proyecto'}</span>
                            <span class="wj-badge info">{row.get('cliente','') or 'Sin cliente'}</span>
                            <span class="wj-badge success">{format_currency(dinero)}</span>
                            <span class="wj-badge warning">🎯 {row.get('hits', 0)} hits</span>
                        </div>
                        {f'<div style="margin-top:6px;font-size:0.85rem;color:#1FAA6B;"><b>Resultado:</b> {row.get("resultado")}</div>' if row.get('resultado') else ''}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_actions:
                if on_edit and st.button("✏️", key=f"edit_{row['id']}"):
                    on_edit(row["id"])
                if on_delete and st.button("🗑️", key=f"del_{row['id']}"):
                    on_delete(row["id"])

            st.markdown("</div>", unsafe_allow_html=True)
