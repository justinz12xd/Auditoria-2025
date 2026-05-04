from __future__ import annotations

import streamlit as st


def theme_tokens(theme_mode: str) -> dict[str, str]:
    if theme_mode == "Oscuro":
        return {
            "color_scheme": "dark",
            "bg_main": "#0b1220",
            "text_main": "#e5e7eb",
            "text_soft": "#94a3b8",
            "card_bg": "#111827",
            "card_border": "#334155",
            "input_bg": "#0f172a",
            "input_border": "#334155",
            "input_placeholder": "#94a3b8",
            "sidebar_bg": "#020617",
            "sidebar_border": "#1e293b",
            "sidebar_text": "#e2e8f0",
            "sidebar_text_muted": "#94a3b8",
            "sidebar_input_bg": "#0f172a",
            "sidebar_input_text": "#e2e8f0",
            "sidebar_input_border": "#334155",
            "table_wrap_bg": "#111827",
            "table_wrap_border": "#334155",
            "table_header_bg": "#1f2937",
            "table_header_text": "#e5e7eb",
            "table_row_bg": "#111827",
            "table_row_alt_bg": "#0f172a",
            "table_row_border": "#1e293b",
            "plot_bg": "#111827",
            "plot_paper": "#111827",
            "plot_grid": "#334155",
            "gdg_bg_cell": "#0f172a",
            "gdg_bg_cell_medium": "#111827",
            "gdg_bg_header": "#1f2937",
            "gdg_bg_header_hovered": "#243244",
            "gdg_bg_bubble": "#0b1220",
            "gdg_bg_search_result": "#1e3a8a",
            "gdg_border_color": "#334155",
            "gdg_horizontal_border_color": "#1e293b",
            "gdg_drilldown_border": "#64748b",
            "gdg_link_color": "#e2e8f0",
            "gdg_accent_color": "#93c5fd",
            "gdg_text_dark": "#e5e7eb",
            "gdg_text_medium": "#cbd5e1",
            "gdg_text_light": "#94a3b8",
            "gdg_text_header": "#f1f5f9",
            "gdg_selection_bg": "rgba(147, 197, 253, 0.18)",
            "gdg_selection_bg_cell": "rgba(147, 197, 253, 0.24)",
        }

    return {
        "color_scheme": "light",
        "bg_main": "#f7f9fb",
        "text_main": "#191c1e",
        "text_soft": "#64748b",
        "card_bg": "#ffffff",
        "card_border": "#e2e8f0",
        "input_bg": "#ffffff",
        "input_border": "#cbd5e1",
        "input_placeholder": "#64748b",
        "sidebar_bg": "#0f172a",
        "sidebar_border": "#1e293b",
        "sidebar_text": "#f1f5f9",
        "sidebar_text_muted": "#cbd5e1",
        "sidebar_input_bg": "#ffffff",
        "sidebar_input_text": "#0f172a",
        "sidebar_input_border": "#334155",
        "table_wrap_bg": "#edf1f5",
        "table_wrap_border": "#d5dde8",
        "table_header_bg": "#e3e9f1",
        "table_header_text": "#1e293b",
        "table_row_bg": "#edf1f5",
        "table_row_alt_bg": "#e8edf3",
        "table_row_border": "#dde5ee",
        "plot_bg": "#ffffff",
        "plot_paper": "#ffffff",
        "plot_grid": "#e2e8f0",
        "gdg_bg_cell": "#eef2f6",
        "gdg_bg_cell_medium": "#e6ebf1",
        "gdg_bg_header": "#e2e8f0",
        "gdg_bg_header_hovered": "#d8e0ea",
        "gdg_bg_bubble": "#f8fafc",
        "gdg_bg_search_result": "#dbeafe",
        "gdg_border_color": "#cbd5e1",
        "gdg_horizontal_border_color": "#d8dee8",
        "gdg_drilldown_border": "#94a3b8",
        "gdg_link_color": "#0f172a",
        "gdg_accent_color": "#0f172a",
        "gdg_text_dark": "#0f172a",
        "gdg_text_medium": "#334155",
        "gdg_text_light": "#475569",
        "gdg_text_header": "#0f172a",
        "gdg_selection_bg": "rgba(15, 23, 42, 0.12)",
        "gdg_selection_bg_cell": "rgba(15, 23, 42, 0.18)",
    }


def apply_theme(theme_mode: str) -> None:
    t = theme_tokens(theme_mode)
    css = """
        <style>
            :root {
                --bg-main: __BG_MAIN__;
                --text-main: __TEXT_MAIN__;
                --text-soft: __TEXT_SOFT__;
                --card-bg: __CARD_BG__;
                --card-border: __CARD_BORDER__;
                --input-bg: __INPUT_BG__;
                --input-border: __INPUT_BORDER__;
                --input-placeholder: __INPUT_PLACEHOLDER__;
            }

            .stApp {
                background: var(--bg-main);
                color: var(--text-main);
                color-scheme: __COLOR_SCHEME__;
            }
            /* Solo el cuerpo principal: si aplicamos .stApp p al sidebar, hereda texto oscuro sobre fondo oscuro */
            [data-testid="stAppViewContainer"] .stMarkdown,
            [data-testid="stAppViewContainer"] .stCaption,
            [data-testid="stAppViewContainer"] .stText,
            [data-testid="stAppViewContainer"] .stSubheader,
            [data-testid="stAppViewContainer"] .stHeader {
                color: var(--text-main);
            }
            [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"],
            [data-testid="stAppViewContainer"] label,
            [data-testid="stAppViewContainer"] p,
            [data-testid="stAppViewContainer"] span,
            [data-testid="stAppViewContainer"] div {
                color: inherit;
            }

            /*
             * No ocultar stHeader entero: ahí vive el control del layout.
             * No ocultar stToolbar: dentro va stExpandSidebarButton; si display:none en el toolbar,
             * el botón de reabrir el sidebar queda con caja 0×0 y no se ve ni se puede pulsar.
             */
            [data-testid="stDecoration"],
            [data-testid="stStatusWidget"] {
                display: none !important;
            }
            [data-testid="stHeader"] {
                background: var(--bg-main);
                border-bottom: 1px solid var(--card-border);
            }
            [data-testid="stToolbar"] {
                background: transparent;
            }
            #MainMenu, footer {
                visibility: hidden !important;
                height: 0 !important;
            }
            .block-container {
                padding-top: 1rem !important;
            }
            [data-testid="stSidebar"] {
                background: __SIDEBAR_BG__;
                border-right: 1px solid __SIDEBAR_BORDER__;
                color: __SIDEBAR_TEXT__ !important;
            }
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] span,
            [data-testid="stSidebar"] div,
            [data-testid="stSidebar"] small,
            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3,
            [data-testid="stSidebar"] .stMarkdown,
            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
                color: __SIDEBAR_TEXT__ !important;
            }
            [data-testid="stSidebar"] .stCaption,
            [data-testid="stSidebar"] [data-testid="stCaption"] {
                color: __SIDEBAR_TEXT_MUTED__ !important;
            }
            [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
            [data-testid="stSidebar"] [data-testid="stWidgetLabel"] label {
                color: __SIDEBAR_TEXT__ !important;
            }
            [data-testid="stSidebar"] .stSlider p,
            [data-testid="stSidebar"] .stSlider label {
                color: __SIDEBAR_TEXT__ !important;
            }
            [data-testid="stSidebar"] [data-baseweb="select"] > div {
                background: __SIDEBAR_INPUT_BG__ !important;
                border: 1px solid __SIDEBAR_INPUT_BORDER__ !important;
                color: __SIDEBAR_INPUT_TEXT__ !important;
            }
            [data-testid="stSidebar"] [data-baseweb="select"] * {
                color: __SIDEBAR_INPUT_TEXT__ !important;
            }
            [data-testid="stSidebar"] .stDateInput input {
                background: __SIDEBAR_INPUT_BG__ !important;
                color: __SIDEBAR_INPUT_TEXT__ !important;
                border: 1px solid __SIDEBAR_INPUT_BORDER__ !important;
                border-radius: 6px !important;
            }
            [data-testid="stSidebar"] .stDateInput svg,
            [data-testid="stSidebar"] [data-baseweb="select"] svg {
                fill: __SIDEBAR_INPUT_TEXT__ !important;
            }
            .main-header {
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 8px;
                padding: 16px 18px;
                margin-top: 18px;
                margin-bottom: 14px;
            }
            .kpi-card {
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 8px;
                padding: 12px 14px;
                min-height: 92px;
            }
            .kpi-label {
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: var(--text-soft);
            }
            .kpi-value {
                font-size: 24px;
                font-weight: 700;
                color: var(--text-main);
                margin-top: 6px;
            }
            .panel {
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 8px;
                padding: 14px;
            }
            .audit-table-wrap {
                background: __TABLE_WRAP_BG__;
                border: 1px solid __TABLE_WRAP_BORDER__;
                border-radius: 8px;
                padding: 12px;
            }
            .stPlotlyChart > div {
                background: var(--card-bg) !important;
            }

            /* Dataframe en modo claro (Glide Data Grid vars) */
            [data-testid="stDataFrame"] {
                --gdg-bg-cell: __GDG_BG_CELL__;
                --gdg-bg-cell-medium: __GDG_BG_CELL_MEDIUM__;
                --gdg-bg-header: __GDG_BG_HEADER__;
                --gdg-bg-header-hovered: __GDG_BG_HEADER_HOVERED__;
                --gdg-bg-bubble: __GDG_BG_BUBBLE__;
                --gdg-bg-search-result: __GDG_BG_SEARCH_RESULT__;
                --gdg-border-color: __GDG_BORDER_COLOR__;
                --gdg-horizontal-border-color: __GDG_HORIZONTAL_BORDER_COLOR__;
                --gdg-drilldown-border: __GDG_DRILLDOWN_BORDER__;
                --gdg-link-color: __GDG_LINK_COLOR__;
                --gdg-accent-color: __GDG_ACCENT_COLOR__;
                --gdg-text-dark: __GDG_TEXT_DARK__;
                --gdg-text-medium: __GDG_TEXT_MEDIUM__;
                --gdg-text-light: __GDG_TEXT_LIGHT__;
                --gdg-text-header: __GDG_TEXT_HEADER__;
                --gdg-selection-bg: __GDG_SELECTION_BG__;
                --gdg-selection-bg-cell: __GDG_SELECTION_BG_CELL__;
            }

            [data-testid="stDataFrame"] [role="grid"],
            [data-testid="stDataFrame"] canvas {
                background: __GDG_BG_CELL__ !important;
                color: __GDG_TEXT_DARK__ !important;
            }
            [data-testid="stDataFrame"],
            [data-testid="stDataFrame"] * {
                color: __GDG_TEXT_DARK__ !important;
            }

            /* Inputs del cuerpo (no sidebar) */
            [data-testid="stAppViewContainer"] [data-baseweb="select"] > div,
            [data-testid="stAppViewContainer"] .stTextInput input,
            [data-testid="stAppViewContainer"] .stNumberInput input,
            [data-testid="stAppViewContainer"] .stDateInput input {
                background: var(--input-bg) !important;
                border: 1px solid var(--input-border) !important;
                color: var(--text-main) !important;
            }
            [data-testid="stAppViewContainer"] [data-baseweb="select"] * {
                color: var(--text-main) !important;
            }
            [data-testid="stAppViewContainer"] input::placeholder {
                color: var(--input-placeholder) !important;
                opacity: 1;
            }
            [role="listbox"] {
                background: var(--card-bg) !important;
                color: var(--text-main) !important;
                border: 1px solid var(--card-border) !important;
            }

            .audit-table-shell {
                background: __TABLE_WRAP_BG__;
                border: 1px solid __TABLE_WRAP_BORDER__;
                border-radius: 8px;
                overflow: auto;
                max-height: 520px;
            }
            .audit-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
                color: var(--text-main);
                min-width: 1200px;
            }
            .audit-table thead th {
                position: sticky;
                top: 0;
                background: __TABLE_HEADER_BG__;
                color: __TABLE_HEADER_TEXT__;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                font-size: 11px;
                font-weight: 700;
                border-bottom: 1px solid __TABLE_WRAP_BORDER__;
                padding: 10px 8px;
                text-align: left;
                z-index: 1;
            }
            .audit-table tbody td {
                border-bottom: 1px solid __TABLE_ROW_BORDER__;
                padding: 8px;
                vertical-align: top;
                background: __TABLE_ROW_BG__;
            }
            .audit-table tbody tr:nth-child(even) td {
                background: __TABLE_ROW_ALT_BG__;
            }
        </style>
    """
    css = (
        css.replace("__BG_MAIN__", t["bg_main"])
        .replace("__COLOR_SCHEME__", t["color_scheme"])
        .replace("__TEXT_MAIN__", t["text_main"])
        .replace("__TEXT_SOFT__", t["text_soft"])
        .replace("__CARD_BG__", t["card_bg"])
        .replace("__CARD_BORDER__", t["card_border"])
        .replace("__INPUT_BG__", t["input_bg"])
        .replace("__INPUT_BORDER__", t["input_border"])
        .replace("__INPUT_PLACEHOLDER__", t["input_placeholder"])
        .replace("__SIDEBAR_BG__", t["sidebar_bg"])
        .replace("__SIDEBAR_BORDER__", t["sidebar_border"])
        .replace("__SIDEBAR_TEXT__", t["sidebar_text"])
        .replace("__SIDEBAR_TEXT_MUTED__", t["sidebar_text_muted"])
        .replace("__SIDEBAR_INPUT_BG__", t["sidebar_input_bg"])
        .replace("__SIDEBAR_INPUT_TEXT__", t["sidebar_input_text"])
        .replace("__SIDEBAR_INPUT_BORDER__", t["sidebar_input_border"])
        .replace("__TABLE_WRAP_BG__", t["table_wrap_bg"])
        .replace("__TABLE_WRAP_BORDER__", t["table_wrap_border"])
        .replace("__TABLE_HEADER_BG__", t["table_header_bg"])
        .replace("__TABLE_HEADER_TEXT__", t["table_header_text"])
        .replace("__TABLE_ROW_BORDER__", t["table_row_border"])
        .replace("__TABLE_ROW_BG__", t["table_row_bg"])
        .replace("__TABLE_ROW_ALT_BG__", t["table_row_alt_bg"])
        .replace("__GDG_BG_CELL__", t["gdg_bg_cell"])
        .replace("__GDG_BG_CELL_MEDIUM__", t["gdg_bg_cell_medium"])
        .replace("__GDG_BG_HEADER__", t["gdg_bg_header"])
        .replace("__GDG_BG_HEADER_HOVERED__", t["gdg_bg_header_hovered"])
        .replace("__GDG_BG_BUBBLE__", t["gdg_bg_bubble"])
        .replace("__GDG_BG_SEARCH_RESULT__", t["gdg_bg_search_result"])
        .replace("__GDG_BORDER_COLOR__", t["gdg_border_color"])
        .replace("__GDG_HORIZONTAL_BORDER_COLOR__", t["gdg_horizontal_border_color"])
        .replace("__GDG_DRILLDOWN_BORDER__", t["gdg_drilldown_border"])
        .replace("__GDG_LINK_COLOR__", t["gdg_link_color"])
        .replace("__GDG_ACCENT_COLOR__", t["gdg_accent_color"])
        .replace("__GDG_TEXT_DARK__", t["gdg_text_dark"])
        .replace("__GDG_TEXT_MEDIUM__", t["gdg_text_medium"])
        .replace("__GDG_TEXT_LIGHT__", t["gdg_text_light"])
        .replace("__GDG_TEXT_HEADER__", t["gdg_text_header"])
        .replace("__GDG_SELECTION_BG__", t["gdg_selection_bg"])
        .replace("__GDG_SELECTION_BG_CELL__", t["gdg_selection_bg_cell"])
    )
    st.markdown(css, unsafe_allow_html=True)
