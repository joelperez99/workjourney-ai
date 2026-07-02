"""
Command Palette (Ctrl+K): navegación rápida entre módulos + búsqueda global.

Nota: la captura del atajo Ctrl+K se hace vía JS inyectado (best-effort);
el buscador también funciona haciendo clic normal en el campo de texto.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from components.sidebar import MENU_ITEMS
from services.search_service import global_search

PALETTE_PLACEHOLDER = "🔍  Buscar módulos, clientes, proyectos... (Ctrl+K)"


def render_command_palette() -> None:
    query = st.text_input(
        "command_palette",
        placeholder=PALETTE_PLACEHOLDER,
        key="cmd_palette_query",
        label_visibility="collapsed",
    )

    components.html(
        f"""
        <script>
        const doc = window.parent.document;
        function focusPalette() {{
            const inputs = doc.querySelectorAll('input[placeholder^="🔍"]');
            if (inputs.length) {{ inputs[0].focus(); }}
        }}
        if (!window.__wjCmdkBound) {{
            window.__wjCmdkBound = true;
            doc.addEventListener('keydown', function(e) {{
                if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {{
                    e.preventDefault();
                    focusPalette();
                }}
            }});
        }}
        </script>
        """,
        height=0,
    )

    if not query:
        return

    query_lower = query.lower()
    page_matches = [label for label, _ in MENU_ITEMS if query_lower in label.lower()]
    search_results = global_search(query)

    if not page_matches and not search_results:
        st.caption("Sin resultados.")
        return

    with st.container():
        st.markdown('<div class="wj-card-flat">', unsafe_allow_html=True)
        if page_matches:
            st.caption("Módulos")
            cols = st.columns(min(len(page_matches), 4))
            for i, label in enumerate(page_matches):
                with cols[i % len(cols)]:
                    if st.button(f"📂 {label}", key=f"cmdk_nav_{label}", use_container_width=True):
                        st.session_state["main_menu"] = label
                        st.rerun()
        if search_results:
            st.caption("Resultados")
            for r in search_results[:10]:
                st.markdown(
                    f"<div style='padding:6px 0;border-bottom:1px solid #E7E7EF;'>"
                    f"<span class='wj-badge primary'>{r['module']}</span> "
                    f"<span style='color:#4B4B5A;'>{r['preview']}</span></div>",
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)
