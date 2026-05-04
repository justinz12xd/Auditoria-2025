from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data.loaders import load_details_csv, load_headers_csv
from src.audit.sri_audit import (
    build_document_report,
    build_duplicate_report,
    build_monthly_report,
    build_product_report,
    build_summary,
)
from src.config import PROCESSED_DIR
from ui.components import kpi_card, render_audit_table


def render_sri_view(theme_mode: str, t: dict[str, str]) -> None:
    headers_path = PROCESSED_DIR / "compras_2025_cabeceras.csv"
    details_path = PROCESSED_DIR / "compras_2025_detalles.csv"

    headers_df = load_headers_csv(headers_path)
    details_df = load_details_csv(details_path)

    if headers_df.empty:
        st.warning(
            "No encontré los CSV de compras SRI. Ejecuta primero:\n"
            "1) `python -m cli parse compras-dir data/pdf_sri`\n"
            "2) `python -m cli audit sri`"
        )
        return

    st.markdown(
        """
        <div class="main-header">
            <div style="font-size:24px;font-weight:800;color:var(--text-main);">Auditoría SRI 2025</div>
            <div style="font-size:12px;color:var(--text-soft);margin-top:4px;">Compras autorizadas, duplicados, montos y calidad de archivo desde data/pdf_sri</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    min_date = pd.Timestamp(headers_df["fecha"].min()).date()
    max_date = pd.Timestamp(headers_df["fecha"].max()).date()

    st.sidebar.markdown("## Audit Pro 2025")
    st.sidebar.caption("Filtros globales")
    start_date = st.sidebar.date_input("Fecha desde", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("Fecha hasta", value=max_date, min_value=min_date, max_value=max_date)

    if start_date > end_date:
        st.error("La fecha inicial no puede ser mayor que la final.")
        return

    headers_f = headers_df[(headers_df["fecha"].dt.date >= start_date) & (headers_df["fecha"].dt.date <= end_date)]
    details_f = details_df.copy()
    if not details_f.empty and "fecha" in details_f.columns:
        details_f = details_f[(details_f["fecha"].dt.date >= start_date) & (details_f["fecha"].dt.date <= end_date)]

    if headers_f.empty:
        st.info("No hay registros para el rango seleccionado.")
        return

    summary = build_summary(headers_f, details_f)
    monthly_df = build_monthly_report(headers_f)
    dup_df = build_duplicate_report(headers_f)
    doc_df = build_document_report(headers_f)
    prod_df = build_product_report(details_f) if not details_f.empty else pd.DataFrame()

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        kpi_card("Documentos", f"{summary['total_documentos']:,.0f}")
    with k2:
        kpi_card("Duplicados", f"{summary['documentos_duplicados']:,.0f}")
    with k3:
        kpi_card("Importe total", f"${summary['importe_total']:,.2f}")
    with k4:
        kpi_card("Rango fechas", f"{summary['fecha_inicio']} → {summary['fecha_fin']}")
    with k5:
        kpi_card("Compradores únicos", f"{summary['compradores_unicos']:,.0f}")
    with k6:
        kpi_card("Archivos anómalos", f"{summary['archivos_anomalos']:,.0f}")

    chart_col, dup_col = st.columns([1.2, 1])
    with chart_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Tendencia mensual")
        if not monthly_df.empty:
            monthly_fig = go.Figure()
            monthly_fig.add_trace(
                go.Bar(
                    x=monthly_df["anio_mes"],
                    y=monthly_df["documentos"],
                    name="Documentos",
                    marker_color="#0f172a",
                    opacity=0.8,
                )
            )
            monthly_fig.add_trace(
                go.Scatter(
                    x=monthly_df["anio_mes"],
                    y=monthly_df["importe_total"],
                    name="Importe total",
                    mode="lines+markers",
                    line=dict(color="#0ea5e9", width=3),
                    yaxis="y2",
                )
            )
            monthly_fig.update_layout(
                template="plotly_white",
                margin=dict(t=10, l=10, r=10, b=10),
                xaxis_title="Mes",
                yaxis=dict(title="Documentos", showgrid=True, gridcolor=t["plot_grid"]),
                yaxis2=dict(title="Importe USD", overlaying="y", side="right", showgrid=False),
                plot_bgcolor=t["plot_bg"],
                paper_bgcolor=t["plot_paper"],
                font=dict(color=t["text_main"]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                height=360,
            )
            st.plotly_chart(monthly_fig, use_container_width=True, config={"displaylogo": False})
        else:
            st.info("Sin datos mensuales para el rango seleccionado.")
        st.markdown("</div>", unsafe_allow_html=True)

    with dup_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Duplicados por clave de acceso")
        if not dup_df.empty:
            dup_plot = dup_df.head(10).copy()
            dup_plot["clave_acceso"] = dup_plot["clave_acceso"].astype(str).str[-8:]
            fig = px.bar(
                dup_plot,
                x="clave_acceso",
                y="veces_clave",
                color="veces_clave",
                template="plotly_white",
                color_continuous_scale=["#bae6fd", "#0284c7"],
                hover_data=["fecha_emision_min", "fecha_emision_max", "importe_total", "archivos"],
            )
            fig.update_layout(
                margin=dict(t=10, l=10, r=10, b=10),
                plot_bgcolor=t["plot_bg"],
                paper_bgcolor=t["plot_paper"],
                font=dict(color=t["text_main"]),
                xaxis_title="Clave (últimos 8 dígitos)",
                yaxis_title="Repeticiones",
                height=360,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
        else:
            st.info("No se detectaron duplicados en el rango seleccionado.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="audit-table-wrap">', unsafe_allow_html=True)
    st.subheader("Detalle documental")
    doc_cols = [
        "source_file",
        "fecha_emision",
        "clave_acceso",
        "estado",
        "importe_total",
        "duplicado",
        "veces_clave",
        "archivo_anomalo",
        "identificacion_comprador",
        "razon_social_comprador",
    ]
    doc_headers = {
        "source_file": "Archivo",
        "fecha_emision": "Fecha emisión",
        "clave_acceso": "Clave de acceso",
        "estado": "Estado",
        "importe_total": "Importe total",
        "duplicado": "Duplicado",
        "veces_clave": "Veces",
        "archivo_anomalo": "Archivo anómalo",
        "identificacion_comprador": "ID comprador",
        "razon_social_comprador": "Comprador",
    }
    render_audit_table(doc_df, doc_cols, theme_mode, header_labels=doc_headers)
    st.markdown("</div>", unsafe_allow_html=True)

    if not prod_df.empty:
        prod_col, prod_table_col = st.columns([1.05, 0.95])
        with prod_col:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.subheader("Productos más comprados")
            prod_plot = prod_df.head(10).copy()
            prod_plot["sku"] = prod_plot["sku"].astype(str)
            fig = px.bar(
                prod_plot,
                x="sku",
                y="unidades",
                color="unidades_gratis",
                template="plotly_white",
                color_continuous_scale=["#e2e8f0", "#0ea5e9"],
                hover_data=["descripcion", "importe_total", "lineas"],
            )
            fig.update_layout(
                margin=dict(t=10, l=10, r=10, b=10),
                plot_bgcolor=t["plot_bg"],
                paper_bgcolor=t["plot_paper"],
                font=dict(color=t["text_main"]),
                xaxis_title="SKU",
                yaxis_title="Unidades",
                xaxis=dict(type="category", tickangle=-25),
                height=360,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with prod_table_col:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.subheader("Resumen de líneas")
            prod_cols = ["sku", "descripcion", "lineas", "unidades", "unidades_gratis", "importe_total"]
            prod_headers = {
                "sku": "SKU",
                "descripcion": "Descripción",
                "lineas": "Líneas",
                "unidades": "Unidades",
                "unidades_gratis": "Líneas gratis",
                "importe_total": "Importe total",
            }
            render_audit_table(prod_df, prod_cols, theme_mode, header_labels=prod_headers)
            st.markdown("</div>", unsafe_allow_html=True)

    st.caption(
        f"Cabeceras: `{headers_path}` | Detalles: `{details_path}` | Documentos visibles: {len(headers_f)}"
    )
