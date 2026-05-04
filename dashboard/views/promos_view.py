from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data.loaders import load_details_csv
from src.audit.promo_audit import compute_promo_audit_df
from src.config import PROCESSED_DIR
from ui.components import render_audit_table


def render_promos_view(theme_mode: str, t: dict[str, str]) -> None:
    sales_path = PROCESSED_DIR / "facturas_2025_detalles.csv"
    purchases_path = PROCESSED_DIR / "compras_2025_detalles.csv"

    sales_df = load_details_csv(sales_path)
    purchases_df = load_details_csv(purchases_path)

    if sales_df.empty or purchases_df.empty:
        st.warning(
            "No hay datos suficientes. Ejecuta primero:\n"
            "1) `python -m cli parse xml-dir ...`\n"
            "2) `python -m cli parse compras-dir ...`"
        )
        return

    st.markdown(
        """
        <div class="main-header">
            <div style="font-size:24px;font-weight:800;color:var(--text-main);">Auditoría de Promociones 2025</div>
            <div style="font-size:12px;color:var(--text-soft);margin-top:4px;">Vista ejecutiva de ingresos reales, promociones y brecha estimada</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("## Audit Pro 2025")
    st.sidebar.caption("Filtros globales")

    sales_df["anio_mes"] = sales_df["fecha"].dt.to_period("M").astype(str)
    purchases_df["anio_mes"] = purchases_df["fecha"].dt.to_period("M").astype(str)
    available_months = sorted(set(sales_df["anio_mes"].dropna()) | set(purchases_df["anio_mes"].dropna()))
    available_months_2025 = [m for m in available_months if m.startswith("2025-")]

    month_options = ["Todo 2025"] + available_months_2025
    selected_month = st.sidebar.selectbox("Mes", options=month_options, index=0)

    if selected_month == "Todo 2025":
        sales_f = sales_df[sales_df["fecha"].dt.year == 2025]
        purchases_f = purchases_df[purchases_df["fecha"].dt.year == 2025]
    else:
        sales_f = sales_df[sales_df["anio_mes"] == selected_month]
        purchases_f = purchases_df[purchases_df["anio_mes"] == selected_month]

    audit_df = compute_promo_audit_df(sales_f, purchases_f)
    if audit_df.empty:
        st.info("No hay registros para el rango seleccionado.")
        return

    product_catalog = (
        audit_df[["sku", "descripcion"]]
        .fillna("")
        .assign(
            sku=lambda d: d["sku"].astype(str).str.strip(),
            descripcion=lambda d: d["descripcion"].astype(str).str.strip(),
        )
        .drop_duplicates(subset=["sku", "descripcion"])
    )
    product_catalog["label"] = product_catalog.apply(
        lambda r: f"{r['descripcion']} ({r['sku']})" if r["descripcion"] else r["sku"],
        axis=1,
    )
    product_catalog = product_catalog.sort_values(by=["descripcion", "sku"], ascending=True)

    product_choice = st.sidebar.selectbox(
        "Producto",
        options=["Todos los productos"] + product_catalog["label"].tolist(),
        index=0,
        help="Escribí mientras el selector está enfocado para filtrar por nombre o SKU.",
    )

    if product_choice == "Todos los productos":
        selected_skus = []
    else:
        selected_skus = product_catalog.loc[
            product_catalog["label"] == product_choice, "sku"
        ].tolist()

    promo_filter = st.sidebar.selectbox(
        "Filtrar por promociones",
        options=["Todos", "Con promociones", "Solo sin promociones", "Con brecha", "Sin brecha"],
    )

    if selected_skus:
        audit_df = audit_df[audit_df["sku"].astype(str).isin(selected_skus)]

    if promo_filter == "Con promociones":
        audit_df = audit_df[audit_df["unidades_promocion_obtenidas"] > 0]
    elif promo_filter == "Solo sin promociones":
        audit_df = audit_df[audit_df["unidades_promocion_obtenidas"] <= 0]
    elif promo_filter == "Con brecha":
        audit_df = audit_df[audit_df["brecha_ingreso_promos"] > 0]
    elif promo_filter == "Sin brecha":
        audit_df = audit_df[audit_df["brecha_ingreso_promos"] <= 0]

    if audit_df.empty:
        st.info("No quedaron datos tras aplicar filtros.")
        return

    if "costo_unitario_referencia" not in audit_df.columns:
        audit_df["costo_unitario_referencia"] = 0.0
    if "perdida_promos_no_monetizadas_costo" not in audit_df.columns:
        audit_df["perdida_promos_no_monetizadas_costo"] = (
            audit_df["unidades_promo_no_monetizadas"] * audit_df["costo_unitario_referencia"]
        )
    if "ingreso_no_cobrado_potencial" not in audit_df.columns:
        audit_df["ingreso_no_cobrado_potencial"] = (
            audit_df["unidades_promo_no_monetizadas"] * audit_df["precio_promedio_venta"]
        )
    if "margen_unitario_estimado" not in audit_df.columns:
        audit_df["margen_unitario_estimado"] = (
            audit_df["precio_promedio_venta"] - audit_df["costo_unitario_referencia"]
        ).clip(lower=0.0)
    if "ganancia_no_realizada_promos" not in audit_df.columns:
        audit_df["ganancia_no_realizada_promos"] = (
            audit_df["unidades_promo_no_monetizadas"] * audit_df["margen_unitario_estimado"]
        )
    if "impacto_total_no_monetizadas" not in audit_df.columns:
        audit_df["impacto_total_no_monetizadas"] = (
            audit_df["perdida_promos_no_monetizadas_costo"] + audit_df["ganancia_no_realizada_promos"]
        )
    if "stock_teorico_cierre_2025" not in audit_df.columns:
        audit_df["stock_teorico_cierre_2025"] = (
            audit_df["unidades_compradas_pagadas"] + audit_df["unidades_promocion_obtenidas"] - audit_df["unidades_vendidas"]
        ).clip(lower=0.0)
    if "deficit_unidades_vs_entradas_2025" not in audit_df.columns:
        audit_df["deficit_unidades_vs_entradas_2025"] = (
            -(audit_df["unidades_compradas_pagadas"] + audit_df["unidades_promocion_obtenidas"] - audit_df["unidades_vendidas"])
        ).clip(lower=0.0)

    total_brecha = float(audit_df["brecha_ingreso_promos"].sum())
    total_promos = float(audit_df["unidades_promocion_obtenidas"].sum())
    total_no_monetizadas = float(audit_df["unidades_promo_no_monetizadas"].sum())
    pct_no_monetizadas = (total_no_monetizadas / total_promos * 100) if total_promos > 0 else 0.0
    ingreso_esperado_promos = float(audit_df["ingreso_esperado_promos"].sum())
    ingreso_monetizado_promos = float(audit_df["ingreso_estimado_promos_monetizados"].sum())
    perdida_no_monetizadas_costo = float(audit_df["perdida_promos_no_monetizadas_costo"].sum())
    ganancia_no_realizada_promos = float(audit_df["ganancia_no_realizada_promos"].sum())
    impacto_total_no_monetizadas = float(audit_df["impacto_total_no_monetizadas"].sum())
    ingreso_no_cobrado_potencial = float(audit_df["ingreso_no_cobrado_potencial"].sum())
    stock_teorico_cierre_2025 = float(audit_df["stock_teorico_cierre_2025"].sum())
    deficit_unidades_2025 = float(audit_df["deficit_unidades_vs_entradas_2025"].sum())

    robo_estimado_pct = st.sidebar.slider(
        "Supuesto: % promos no monetizadas robadas",
        min_value=0,
        max_value=100,
        value=30,
        step=5,
        help=(
            "No se puede distinguir automáticamente entre robo y stock no vendido. "
            "Este supuesto separa ambos escenarios para estimar pérdida."
        ),
    )
    robo_factor = robo_estimado_pct / 100.0
    perdida_robadas_estimada = perdida_no_monetizadas_costo * robo_factor
    perdida_no_vendidas_estimada = perdida_no_monetizadas_costo * (1.0 - robo_factor)
    impacto_robadas_estimado = impacto_total_no_monetizadas * robo_factor
    impacto_no_vendidas_estimado = impacto_total_no_monetizadas * (1.0 - robo_factor)

    sales_merged = sales_f.merge(
        audit_df[["sku"]].drop_duplicates(),
        on="sku",
        how="inner",
    )
    ingresos_reales_pagados = float(sales_merged.loc[~sales_merged["es_linea_gratis"], "precio_total_sin_impuesto"].sum())
    monto_esperado_sin_promos = ingresos_reales_pagados
    monto_esperado_con_promos = ingresos_reales_pagados + ingreso_esperado_promos
    monto_promos_anio = ingreso_esperado_promos
    monto_robado_aprox = impacto_robadas_estimado

    st.subheader("Resumen")
    e1, e2, e3, e4 = st.columns(4)
    with e1:
        st.metric(
            "Monto total esperado del año sin promos",
            f"${monto_esperado_sin_promos:,.2f}",
            help="Suma de ventas facturadas por líneas pagadas (excluye líneas gratis).",
        )
    with e2:
        st.metric(
            "Monto total esperado del año con promos",
            f"${monto_esperado_con_promos:,.2f}",
            help="Ventas pagadas + ingreso esperado si todas las promos obtenidas se vendieran al precio promedio.",
        )
    with e3:
        st.metric(
            "Monto de promos del año",
            f"${monto_promos_anio:,.2f}",
            help="Ingreso esperado por todas las unidades de promoción obtenidas en compras (× precio promedio de venta).",
        )
    with e4:
        st.metric(
            "Monto robado aprox.",
            f"${monto_robado_aprox:,.2f}",
            help=(
                f"Aproximación: {robo_estimado_pct}% del impacto total de promos no monetizadas "
                "(costo + margen no realizado). Ajustá el % en el panel lateral."
            ),
        )
    st.caption(
        "Con promos = ventas pagadas + ingreso esperado por promos obtenidas. "
        "Robo aprox. = porcentaje del impacto total no monetizado (sidebar)."
    )

    with st.expander("Detalle técnico de la auditoría", expanded=False):
        r1a, r1b, r1c = st.columns(3)
        with r1a:
            st.metric("Ingreso monetizado (promos)", f"${ingreso_monetizado_promos:,.2f}")
        with r1b:
            st.metric("Brecha total (promos)", f"${total_brecha:,.2f}")
        with r1c:
            st.metric("Ingreso no cobrado potencial", f"${ingreso_no_cobrado_potencial:,.2f}")
        r2a, r2b, r2c = st.columns(3)
        with r2a:
            st.metric("Unidades promo no monetizadas", f"{total_no_monetizadas:,.0f}")
        with r2b:
            st.metric("% promo no monetizada", f"{pct_no_monetizadas:,.2f}%")
        with r2c:
            st.metric("Pérdida estimada robadas (costo)", f"${perdida_robadas_estimada:,.2f}")
        r3a, r3b, r3c = st.columns(3)
        with r3a:
            st.metric("Pérdida estimada no vendidas (costo)", f"${perdida_no_vendidas_estimada:,.2f}")
        with r3b:
            st.metric("Ganancia no realizada (promos)", f"${ganancia_no_realizada_promos:,.2f}")
        with r3c:
            st.metric("Impacto total no monetizadas", f"${impacto_total_no_monetizadas:,.2f}")
        r4a, r4b, r4c = st.columns(3)
        with r4a:
            st.metric("Impacto no vendidas estimado", f"${impacto_no_vendidas_estimado:,.2f}")
        with r4b:
            st.metric("Stock teórico cierre 2025 (unid.)", f"{stock_teorico_cierre_2025:,.0f}")
        with r4c:
            st.metric("Déficit vs entradas 2025 (unid.)", f"{deficit_unidades_2025:,.0f}")
        st.caption(
            f"Inventario teórico: entradas 2025 − ventas 2025 (sin saldo inicial ni ajustes externos). "
            f"Escenario robo/no vendido: {robo_estimado_pct}% / {100 - robo_estimado_pct}%."
        )

    st.markdown('<div class="audit-table-wrap">', unsafe_allow_html=True)
    st.subheader("Detalle por producto")

    audit_table_df = audit_df.copy()
    promo_units = audit_table_df["unidades_promocion_obtenidas"].astype(float)
    audit_table_df["pct_promo_no_monetizada"] = 0.0
    has_promos = promo_units > 0
    audit_table_df.loc[has_promos, "pct_promo_no_monetizada"] = (
        audit_table_df.loc[has_promos, "unidades_promo_no_monetizadas"].astype(float)
        / promo_units.loc[has_promos]
        * 100
    )

    def classify_priority(row: pd.Series) -> str:
        if row["brecha_ingreso_promos"] >= 1000 or row["pct_promo_no_monetizada"] >= 50:
            return "Alta"
        if row["brecha_ingreso_promos"] >= 300 or row["pct_promo_no_monetizada"] >= 20:
            return "Media"
        return "Baja"

    audit_table_df["prioridad"] = audit_table_df.apply(classify_priority, axis=1)
    audit_table_df["unidades_robadas_estimadas"] = audit_table_df["unidades_promo_no_monetizadas"] * robo_factor
    audit_table_df["unidades_no_vendidas_estimadas"] = (
        audit_table_df["unidades_promo_no_monetizadas"] - audit_table_df["unidades_robadas_estimadas"]
    )
    audit_table_df["perdida_robadas_estimada"] = (
        audit_table_df["perdida_promos_no_monetizadas_costo"] * robo_factor
    )
    audit_table_df["perdida_no_vendidas_estimada"] = (
        audit_table_df["perdida_promos_no_monetizadas_costo"] * (1.0 - robo_factor)
    )
    audit_table_df["impacto_robadas_estimado"] = audit_table_df["impacto_total_no_monetizadas"] * robo_factor
    audit_table_df["impacto_no_vendidas_estimado"] = (
        audit_table_df["impacto_total_no_monetizadas"] * (1.0 - robo_factor)
    )

    table_view_col, table_priority_col, table_brecha_col = st.columns([1.2, 1, 1])
    with table_view_col:
        table_view_mode = st.radio(
            "Vista de columnas",
            options=["Esencial", "Completa"],
            horizontal=True,
            help="Esencial muestra solo campos para priorizar decisiones rápidas.",
        )
    with table_priority_col:
        table_priority_filter = st.selectbox(
            "Prioridad",
            options=["Todas", "Alta", "Alta y media"],
            index=0,
        )
    with table_brecha_col:
        only_positive_gap = st.checkbox("Solo con brecha > 0", value=True)

    search_query = st.text_input(
        "Buscar producto (SKU o nombre)",
        value="",
        placeholder="Ej: PERSPIREX o 7750187005097",
    ).strip()

    if only_positive_gap:
        audit_table_df = audit_table_df[audit_table_df["brecha_ingreso_promos"] > 0]
    if table_priority_filter == "Alta":
        audit_table_df = audit_table_df[audit_table_df["prioridad"] == "Alta"]
    elif table_priority_filter == "Alta y media":
        audit_table_df = audit_table_df[audit_table_df["prioridad"].isin(["Alta", "Media"])]
    if search_query:
        query = search_query.casefold()
        sku_match = audit_table_df["sku"].astype(str).str.casefold().str.contains(query, na=False)
        name_match = audit_table_df["descripcion"].astype(str).str.casefold().str.contains(query, na=False)
        audit_table_df = audit_table_df[sku_match | name_match]

    if audit_table_df.empty:
        st.info("No hay productos que cumplan los filtros de la tabla.")
    else:
        st.caption("Ordenado por mayor brecha de ingreso (USD), luego por mayor % no monetizada.")
        essential_cols = [
            "sku",
            "descripcion",
            "unidades_promocion_obtenidas",
            "unidades_promo_no_monetizadas",
            "impacto_robadas_estimado",
            "ingreso_no_cobrado_potencial",
            "prioridad",
        ]
        full_cols = [
            "sku",
            "descripcion",
            "unidades_compradas_pagadas",
            "unidades_promocion_obtenidas",
            "unidades_vendidas",
            "unidades_promo_monetizadas",
            "unidades_promo_no_monetizadas",
            "stock_teorico_cierre_2025",
            "deficit_unidades_vs_entradas_2025",
            "unidades_robadas_estimadas",
            "unidades_no_vendidas_estimadas",
            "pct_promo_no_monetizada",
            "costo_unitario_referencia",
            "margen_unitario_estimado",
            "precio_promedio_venta",
            "ingreso_esperado_promos",
            "ingreso_estimado_promos_monetizados",
            "brecha_ingreso_promos",
            "perdida_promos_no_monetizadas_costo",
            "ganancia_no_realizada_promos",
            "impacto_total_no_monetizadas",
            "perdida_robadas_estimada",
            "perdida_no_vendidas_estimada",
            "impacto_robadas_estimado",
            "impacto_no_vendidas_estimado",
            "ingreso_no_cobrado_potencial",
            "prioridad",
        ]
        show_cols = essential_cols if table_view_mode == "Esencial" else full_cols
        friendly_headers = {
            "sku": "SKU",
            "descripcion": "Producto",
            "unidades_compradas_pagadas": "Unidades compradas (pagadas)",
            "unidades_promocion_obtenidas": "Promos obtenidas",
            "unidades_vendidas": "Unidades vendidas",
            "unidades_promo_monetizadas": "Promos monetizadas",
            "unidades_promo_no_monetizadas": "Promos no justificadas",
            "stock_teorico_cierre_2025": "Stock teórico cierre 2025 (unid.)",
            "deficit_unidades_vs_entradas_2025": "Déficit vs entradas 2025 (unid.)",
            "unidades_robadas_estimadas": f"Promos robadas est. ({robo_estimado_pct}%)",
            "unidades_no_vendidas_estimadas": f"Promos no vendidas est. ({100 - robo_estimado_pct}%)",
            "pct_promo_no_monetizada": "% promo no monetizada",
            "costo_unitario_referencia": "Costo unitario ref. (USD)",
            "margen_unitario_estimado": "Margen unitario estimado (USD)",
            "precio_promedio_venta": "Precio promedio (USD)",
            "ingreso_esperado_promos": "Ingreso esperado promos (USD)",
            "ingreso_estimado_promos_monetizados": "Ingreso monetizado promos (USD)",
            "brecha_ingreso_promos": "Brecha promos (USD)",
            "perdida_promos_no_monetizadas_costo": "Pérdida total no monetizadas (costo)",
            "ganancia_no_realizada_promos": "Ganancia no realizada (USD)",
            "impacto_total_no_monetizadas": "Impacto total no monetizadas (USD)",
            "perdida_robadas_estimada": "Pérdida robadas est. (USD)",
            "perdida_no_vendidas_estimada": "Pérdida no vendidas est. (USD)",
            "impacto_robadas_estimado": "Riesgo estimado pérdida/robo (USD)",
            "impacto_no_vendidas_estimado": "Impacto no vendidas estimado (USD)",
            "ingreso_no_cobrado_potencial": "Ingreso no cobrado potencial (USD)",
            "prioridad": "Prioridad",
        }
        audit_for_table = audit_table_df.sort_values(
            by=["brecha_ingreso_promos", "pct_promo_no_monetizada"],
            ascending=[False, False],
        )
        render_audit_table(audit_for_table, show_cols, theme_mode, header_labels=friendly_headers)
    st.markdown("</div>", unsafe_allow_html=True)

    tab_graficos, tab_tendencia = st.tabs(["Composición y brecha por producto", "Tendencia mensual"])

    with tab_graficos:
        pie_col, bar_col = st.columns([1, 1.35])
        with pie_col:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.subheader("Composición de ingresos")
            pie_df = pd.DataFrame(
                {
                    "categoria": [
                        "Ingreso total por mercancía pagada",
                        "Ingreso que debió lograrse por promociones",
                    ],
                    "valor": [
                        ingresos_reales_pagados,
                        ingreso_esperado_promos,
                    ],
                }
            )
            pie_fig = px.pie(
                pie_df,
                names="categoria",
                values="valor",
                hole=0.45,
                template="plotly_white",
                color="categoria",
                color_discrete_map={
                    "Ingreso total por mercancía pagada": "#0f172a",
                    "Ingreso que debió lograrse por promociones": "#0ea5e9",
                },
            )
            pie_fig.update_layout(
                margin=dict(t=10, l=10, r=10, b=10),
                legend_title_text="",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="left",
                    x=0,
                    font=dict(color=t["text_main"], size=12),
                    bgcolor=t["plot_paper"],
                ),
                plot_bgcolor=t["plot_bg"],
                paper_bgcolor=t["plot_paper"],
                font=dict(color=t["text_main"]),
                height=360,
            )
            pie_fig.update_traces(
                textinfo="percent+label",
                textfont_size=12,
                textfont_color=t["text_main"],
                marker=dict(line=dict(color=t["plot_paper"], width=1)),
            )
            st.plotly_chart(pie_fig, use_container_width=True, config={"displaylogo": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with bar_col:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.subheader("Productos con mayor riesgo de pérdida o robo")
            top = audit_df[audit_df["brecha_ingreso_promos"] > 0].copy()
            top["producto_label"] = top["descripcion"].fillna("").astype(str).str.strip()
            top.loc[top["producto_label"] == "", "producto_label"] = top["sku"].astype(str)
            top = top.sort_values("brecha_ingreso_promos", ascending=False).head(15)
            top["estado_brecha"] = "Riesgo por pérdida o robo"
            fig = px.bar(
                top,
                x="producto_label",
                y="brecha_ingreso_promos",
                hover_data=["descripcion", "unidades_promocion_obtenidas", "unidades_promo_no_monetizadas"],
                color="estado_brecha",
                template="plotly_white",
                color_discrete_map={
                    "Riesgo por pérdida o robo": "#0ea5e9",
                },
            )
            fig.update_layout(
                margin=dict(t=10, l=10, r=10, b=10),
                plot_bgcolor=t["plot_bg"],
                paper_bgcolor=t["plot_paper"],
                font=dict(color=t["text_main"]),
                xaxis_title="Producto",
                yaxis_title="Riesgo estimado USD",
                xaxis=dict(
                    type="category",
                    tickangle=-25,
                    tickfont=dict(color=t["text_main"]),
                    title=dict(font=dict(color=t["text_main"])),
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=t["plot_grid"],
                    zeroline=True,
                    zerolinecolor="#94a3b8",
                    tickfont=dict(color=t["text_main"]),
                    title=dict(font=dict(color=t["text_main"])),
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="left",
                    x=0,
                    font=dict(color=t["text_main"], size=12),
                    bgcolor=t["plot_paper"],
                ),
                height=360,
            )
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_tendencia:
        monthly_sales = sales_merged.copy()
        monthly_sales["mes"] = monthly_sales["fecha"].dt.to_period("M").astype(str)
        monthly_paid = (
            monthly_sales.loc[~monthly_sales["es_linea_gratis"]]
            .groupby("mes", as_index=False)["precio_total_sin_impuesto"]
            .sum()
            .rename(columns={"precio_total_sin_impuesto": "ingresos_pagados"})
        )

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Tendencia mensual (ingresos pagados)")
        if not monthly_paid.empty:
            monthly_paid = monthly_paid.sort_values("mes")
            trend_fig = go.Figure()
            trend_fig.add_trace(
                go.Scatter(
                    x=monthly_paid["mes"],
                    y=monthly_paid["ingresos_pagados"],
                    mode="lines+markers",
                    line=dict(color="#0f172a", width=3),
                    marker=dict(size=7),
                    name="Ingresos pagados",
                    fill="tozeroy",
                    fillcolor="rgba(14,165,233,0.12)",
                )
            )
            trend_fig.update_layout(
                template="plotly_white",
                margin=dict(t=10, l=10, r=10, b=10),
                xaxis_title="Mes",
                yaxis_title="USD",
                plot_bgcolor=t["plot_bg"],
                paper_bgcolor=t["plot_paper"],
                font=dict(color=t["text_main"]),
                xaxis=dict(
                    type="category",
                    tickangle=-20,
                    tickfont=dict(color=t["text_main"]),
                    title=dict(font=dict(color=t["text_main"])),
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=t["plot_grid"],
                    tickfont=dict(color=t["text_main"]),
                    title=dict(font=dict(color=t["text_main"])),
                ),
                legend=dict(font=dict(color=t["text_main"]), bgcolor=t["plot_paper"]),
                height=340,
            )
            st.plotly_chart(trend_fig, use_container_width=True, config={"displaylogo": False})
        else:
            st.info("Sin datos mensuales para el rango seleccionado.")
        st.markdown("</div>", unsafe_allow_html=True)

    periodo = "Todo 2025" if selected_month == "Todo 2025" else selected_month
    st.caption(
        f"Periodo: {periodo} | Ventas: `{sales_path}` | Compras: `{purchases_path}` | Registros mostrados: {len(audit_df)}"
    )
