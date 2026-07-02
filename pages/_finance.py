"""Página Finanzas: registro de ingresos/gastos y dashboard financiero."""
from __future__ import annotations

import streamlit as st

from components.cards import empty_state, kpi_card, section_title
from components.charts import bar_chart, line_chart
from config.settings import CATEGORIAS_FINANZAS_GASTO, CATEGORIAS_FINANZAS_INGRESO, METODOS_PAGO
from services.clients_service import ClientsService
from services.export_service import to_csv_bytes, to_excel_bytes
from services.finance_service import FinanceService
from services.projects_service import ProjectsService
from utils.formatters import format_currency


def render(username: str):
    section_title("Finanzas", "Ingresos, gastos y proyecciones de tu negocio.")

    service = FinanceService()
    clients = ClientsService().client_names()
    projects = ProjectsService().project_names()

    with st.expander("➕ Nuevo movimiento", expanded=False):
        tipo = st.radio("Tipo", ["Ingreso", "Gasto"], horizontal=True)
        with st.form("finance_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            cliente = c1.selectbox("Cliente", [""] + clients)
            proyecto = c2.selectbox("Proyecto", [""] + projects)

            c3, c4 = st.columns(2)
            monto = c3.number_input("Monto", min_value=0.0, step=10.0)
            metodo_pago = c4.selectbox("Método de pago", METODOS_PAGO)

            c5, c6 = st.columns(2)
            categorias = CATEGORIAS_FINANZAS_INGRESO if tipo == "Ingreso" else CATEGORIAS_FINANZAS_GASTO
            categoria = c5.selectbox("Categoría", categorias)
            fecha = c6.date_input("Fecha")

            c7, c8 = st.columns(2)
            referencia = c7.text_input("Referencia")
            factura = c8.text_input("Factura")

            notas = st.text_area("Notas", height=60)

            submitted = st.form_submit_button("Guardar movimiento", type="primary")
            if submitted and monto > 0:
                service.create_transaction(
                    {
                        "tipo": tipo, "fecha": str(fecha), "cliente": cliente,
                        "proyecto": proyecto, "monto": monto, "metodo_pago": metodo_pago,
                        "referencia": referencia, "factura": factura,
                        "categoria": categoria, "notas": notas,
                    },
                    created_by=username,
                )
                st.success("Movimiento guardado.")
                st.rerun()

    df = service.list_transactions()
    totals = service.totals(df)

    k1, k2, k3, k4 = st.columns(4)
    kpi_card("Ingresos", format_currency(totals["ingresos"]), "💰")
    kpi_card("Gastos", format_currency(totals["gastos"]), "💸")
    kpi_card("Utilidad", format_currency(totals["utilidad"]), "📈")
    kpi_card("Forecast próximo mes", format_currency(service.forecast_next_month()), "🔮")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            section_title("Ingresos por cliente")
            bar_chart(service.by_client(), "cliente", "monto_num", horizontal=True)
    with col_b:
        with st.container(border=True):
            section_title("Ingresos por proyecto")
            bar_chart(service.by_project(), "proyecto", "monto_num", horizontal=True)

    with st.container(border=True):
        section_title("Comparativa mensual")
        monthly = service.monthly_summary()
        if monthly.empty:
            empty_state("Sin datos financieros todavía.")
        else:
            line_chart(monthly, "mes", "utilidad", title="Utilidad mensual")
            st.dataframe(monthly, use_container_width=True, hide_index=True)

    with st.container(border=True):
        section_title("Meta mensual")
        meta = st.number_input("Establece tu meta de ingresos mensuales", min_value=0.0, value=5000.0, step=500.0)
        if meta > 0:
            pct = min((totals["ingresos"] / meta) * 100, 100)
            st.progress(pct / 100, text=f"{pct:.1f}% de la meta alcanzado")

    st.markdown("**Movimientos**")
    if df.empty:
        empty_state("Aún no hay movimientos registrados.")
    else:
        display_df = df.drop(columns=["created_by", "_fecha_dt"], errors="ignore")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        e1, e2 = st.columns(2)
        e1.download_button("⬇️ CSV", to_csv_bytes(display_df), "finanzas.csv", "text/csv", use_container_width=True)
        e2.download_button(
            "⬇️ Excel", to_excel_bytes(display_df, "Finanzas"), "finanzas.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
