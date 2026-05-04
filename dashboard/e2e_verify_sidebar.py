"""Smoke: Streamlit sidebar + resumen promos (Playwright). Run from repo root or dashboard/."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

DASHBOARD_DIR = Path(__file__).resolve().parent
PORT = int(os.environ.get("E2E_STREAMLIT_PORT", "8502"))
BASE = f"http://127.0.0.1:{PORT}"


def _wait_http_ready(timeout_s: float = 90.0) -> None:
    import urllib.error
    import urllib.request

    deadline = time.monotonic() + timeout_s
    paths = ("/_stcore/health", "/healthz", "/")
    while time.monotonic() < deadline:
        for path in paths:
            try:
                urllib.request.urlopen(f"{BASE}{path}", timeout=2)
                return
            except (urllib.error.URLError, OSError):
                continue
        time.sleep(0.5)
    raise RuntimeError(f"Streamlit no respondió en {BASE} tras {timeout_s}s")


def main() -> int:
    env = {**os.environ, "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false"}
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(DASHBOARD_DIR / "app.py"),
            "--server.port",
            str(PORT),
            "--server.headless",
            "true",
            "--server.address",
            "127.0.0.1",
        ],
        cwd=str(DASHBOARD_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_http_ready()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(BASE, wait_until="domcontentloaded", timeout=120_000)
                page.wait_for_timeout(4000)
                sidebar = page.locator('[data-testid="stSidebar"]')
                sidebar.wait_for(state="visible", timeout=60_000)
                collapsed = page.locator('[data-testid="collapsedControl"]')
                if collapsed.count() and collapsed.first.is_visible():
                    collapsed.first.click()
                    page.wait_for_timeout(800)
                body = page.locator('[data-testid="stSidebar"]')
                expect_texts = ["Tema", "Audit Pro 2025", "Mes", "robadas"]
                missing = [t for t in expect_texts if body.get_by_text(t, exact=False).count() == 0]
                if missing:
                    page.screenshot(path=str(DASHBOARD_DIR / "e2e_sidebar_failure.png"), full_page=True)
                    raise AssertionError(f"Texto no encontrado en sidebar: {missing}")
                main = page.locator('[data-testid="stAppViewContainer"]')
                for label in (
                    "Monto total esperado del año sin promos",
                    "Monto total esperado del año con promos",
                    "Monto de promos del año",
                    "Monto robado aprox",
                ):
                    if main.get_by_text(label, exact=False).count() == 0:
                        page.screenshot(path=str(DASHBOARD_DIR / "e2e_sidebar_failure.png"), full_page=True)
                        raise AssertionError(f"Resumen sin métrica: {label}")

                # Colapsar / reabrir: en Streamlit reciente el toggle es el button dentro de stSidebarCollapseButton
                # (Playwright lo marca a veces como no visible → force=True). No hay collapsedControl; reabrir = stExpandSidebarButton.
                def _sidebar_width() -> float:
                    return float(
                        page.locator('[data-testid="stSidebar"]').evaluate(
                            "e => parseFloat(getComputedStyle(e).width)"
                        )
                    )

                toggle_btn = page.locator('[data-testid="stSidebarCollapseButton"] button')
                toggle_btn.wait_for(state="attached", timeout=15_000)
                for _ in range(5):
                    if _sidebar_width() < 80:
                        break
                    toggle_btn.click(force=True)
                    page.wait_for_timeout(700)
                else:
                    page.screenshot(path=str(DASHBOARD_DIR / "e2e_sidebar_failure.png"), full_page=True)
                    raise AssertionError("El sidebar no llegó a estado colapsado (ancho sigue alto).")

                opened = page.evaluate(
                    """() => {
                    const b = document.querySelector('[data-testid="stExpandSidebarButton"]');
                    if (!b) return false;
                    b.click();
                    return true;
                }"""
                )
                if not opened:
                    page.screenshot(path=str(DASHBOARD_DIR / "e2e_sidebar_failure.png"), full_page=True)
                    raise AssertionError("No existe stExpandSidebarButton para reabrir el sidebar.")
                page.wait_for_timeout(1500)
                if _sidebar_width() < 200:
                    page.screenshot(path=str(DASHBOARD_DIR / "e2e_sidebar_failure.png"), full_page=True)
                    raise AssertionError("Tras reabrir, el ancho del sidebar sigue colapsado.")

                body_after = page.locator('[data-testid="stSidebar"]')
                missing2 = [t for t in expect_texts if body_after.get_by_text(t, exact=False).count() == 0]
                if missing2:
                    page.screenshot(path=str(DASHBOARD_DIR / "e2e_sidebar_failure.png"), full_page=True)
                    raise AssertionError(f"Tras colapsar/reabrir, sidebar sin texto: {missing2}")
            finally:
                browser.close()
        print("OK: sidebar + 4 métricas; colapsar (toggle) → stExpandSidebarButton → sidebar legible.")
        return 0
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
