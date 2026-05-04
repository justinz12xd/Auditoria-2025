from contextlib import contextmanager
from typing import Iterator

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from src.config import settings


@contextmanager
def browser_page(headless: bool | None = None) -> Iterator[Page]:
    """Inicializa Playwright y entrega una página lista para automatizar."""
    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(
            headless=settings.HEADLESS if headless is None else headless
        )
        context: BrowserContext = browser.new_context(accept_downloads=True)
        page: Page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()
