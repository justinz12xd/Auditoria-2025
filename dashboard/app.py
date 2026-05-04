from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.theme import apply_theme, theme_tokens
from views.promos_view import render_promos_view


def main() -> None:
    st.set_page_config(
        page_title="Auditoría SRI y Promociones 2025",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    theme_mode = st.sidebar.selectbox("Tema", options=["Claro", "Oscuro"], index=0)
    apply_theme(theme_mode)
    tokens = theme_tokens(theme_mode)
    render_promos_view(theme_mode, tokens)


if __name__ == "__main__":
    main()
