"""Exportación de DataFrames a Excel, CSV y PDF, e importación desde archivos."""
from __future__ import annotations

import io

import pandas as pd
from fpdf import FPDF


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Datos") -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return buffer.getvalue()


def to_pdf_bytes(df: pd.DataFrame, title: str = "Reporte") -> bytes:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, title, ln=True)
    pdf.set_font("Helvetica", "", 8)

    columns = list(df.columns)[:10]  # limitar ancho para que quepa en la página
    col_width = 277 / max(len(columns), 1)

    pdf.set_font("Helvetica", "B", 8)
    for col in columns:
        pdf.cell(col_width, 8, str(col)[:20], border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    for _, row in df.head(300).iterrows():
        for col in columns:
            pdf.cell(col_width, 7, str(row[col])[:25], border=1)
        pdf.ln()

    return bytes(pdf.output(dest="S"))


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Lee un archivo subido (Excel o CSV) y devuelve un DataFrame."""
    if uploaded_file.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)
