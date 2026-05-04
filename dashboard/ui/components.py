from __future__ import annotations

import pandas as pd
import streamlit as st

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

    AGGRID_AVAILABLE = True
except Exception:  # pragma: no cover - fallback runtime guard
    AGGRID_AVAILABLE = False


def render_audit_table(
    df: pd.DataFrame,
    cols: list[str],
    theme_mode: str,
    header_labels: dict[str, str] | None = None,
) -> None:
    if df.empty:
        st.info("Sin datos para mostrar en la tabla.")
        return

    if not AGGRID_AVAILABLE:
        st.dataframe(df[cols], use_container_width=True, hide_index=True)
        return

    table_df = df[cols].copy()
    if header_labels:
        table_df = table_df.rename(columns=header_labels)
    gb = GridOptionsBuilder.from_dataframe(table_df)
    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
    )
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    gb.configure_grid_options(
        rowHeight=38,
        headerHeight=38,
        suppressRowClickSelection=True,
        animateRows=False,
    )

    grid_options = gb.build()
    # Modo estable por defecto: dataframe nativo.
    # AgGrid queda como beta porque en algunos entornos queda en blanco.
    st.dataframe(table_df, use_container_width=True, hide_index=True)


def kpi_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
