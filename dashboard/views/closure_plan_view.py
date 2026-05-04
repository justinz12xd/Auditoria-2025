from __future__ import annotations

from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = PROJECT_ROOT / "docs" / "plan_cierre_auditoria_2025.md"


def render_closure_plan_view() -> None:
    st.markdown(
        """
        <div class="main-header">
            <div style="font-size:24px;font-weight:800;color:var(--text-main);">Plan de Cierre de Auditoría 2025</div>
            <div style="font-size:12px;color:var(--text-soft);margin-top:4px;">Checklist y hoja de ruta para cerrar la brecha de promociones</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not PLAN_PATH.exists():
        st.error(f"No se encontró el plan de cierre en `{PLAN_PATH}`.")
        return

    st.caption(f"Fuente: `{PLAN_PATH}`")
    st.markdown(PLAN_PATH.read_text(encoding="utf-8"))
