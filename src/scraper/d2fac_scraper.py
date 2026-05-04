from pathlib import Path

from loguru import logger
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from src.config import RAW_DIR, settings
from src.scraper import utils_selectors as selectors
from src.scraper.utils_browser import browser_page

DEFAULT_START_DATE = "2025-01-01"
DEFAULT_END_DATE = "2025-12-31"
DEFAULT_OUTPUT_FILE = RAW_DIR / "reporte_2025.zip"


class D2FacScraper:
    """Scraper inicial para d2fac.com.

    Por ahora solo implementa:
    - login
    - navegación Dashboard -> COMPROBANTES -> Reporte
    - espera del modal Reporte de Facturación
    - escritura manual de fechas en inputs Angular Material
    - descarga ZIP con archivos XML del periodo 2025
    """

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        headless: bool | None = None,
    ) -> None:
        self.username = username or settings.D2FAC_USERNAME
        self.password = password or settings.D2FAC_PASSWORD
        self.headless = headless

        if not self.username or not self.password:
            raise ValueError(
                "Faltan credenciales. Define D2_USER y D2_PASS en .env"
            )

    def login(self, page: Page) -> None:
        logger.info("Iniciando sesión…")
        page.goto(settings.D2FAC_URL, wait_until="domcontentloaded")
        page.fill(selectors.USERNAME_SELECTOR, self.username)
        page.fill(selectors.PASSWORD_SELECTOR, self.password)
        page.get_by_role("button", name=selectors.LOGIN_BUTTON_ROLE_NAME).click()
        page.wait_for_load_state("networkidle")

    def go_to_reports(self, page: Page) -> None:
        logger.info("Navegando a COMPROBANTES…")
        page.wait_for_selector(selectors.COMPROBANTES_TEXT_SELECTOR)
        try:
            page.click(selectors.COMPROBANTES_TEXT_SELECTOR)
        except PlaywrightError:
            logger.warning(
                "Click por texto en COMPROBANTES falló; intentando fallback Ionic…"
            )
            page.locator(selectors.COMPROBANTES_IONIC_FALLBACK_SELECTOR).click()

        logger.info("Abriendo Reporte…")
        page.wait_for_selector(selectors.REPORT_BUTTON_TEXT_SELECTOR)
        page.click(selectors.REPORT_BUTTON_TEXT_SELECTOR)
        page.wait_for_selector(selectors.REPORT_MODAL_TITLE_SELECTOR)

    def fill_dates(
        self,
        page: Page,
        start_date: str = DEFAULT_START_DATE,
        end_date: str = DEFAULT_END_DATE,
    ) -> None:
        logger.info("Llenando fechas: {} a {}", start_date, end_date)
        date_inputs = page.locator(selectors.DATE_INPUTS_SELECTOR)
        date_inputs.nth(0).fill(start_date)
        date_inputs.nth(1).fill(end_date)

    def download_xml(
        self,
        page: Page,
        output_path: Path = DEFAULT_OUTPUT_FILE,
    ) -> Path:
        logger.info("Descargando archivos XML…")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with page.expect_download(timeout=settings.DOWNLOAD_TIMEOUT_MS) as download_info:
                page.click(selectors.XML_DOWNLOAD_BUTTON_SELECTOR)
            download = download_info.value
            download.save_as(output_path)
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(
                "No se detectó la descarga. Revisa XML_DOWNLOAD_BUTTON_SELECTOR o el flujo del portal."
            ) from exc

        logger.info("Archivo guardado en {}", output_path)
        return output_path

    def run(
        self,
        start_date: str = DEFAULT_START_DATE,
        end_date: str = DEFAULT_END_DATE,
        output_path: Path = DEFAULT_OUTPUT_FILE,
    ) -> Path:
        with browser_page(headless=self.headless) as page:
            self.login(page)
            self.go_to_reports(page)
            self.fill_dates(page, start_date=start_date, end_date=end_date)
            return self.download_xml(page, output_path=output_path)


def scrape_d2fac_2025(output_path: Path = DEFAULT_OUTPUT_FILE) -> Path:
    scraper = D2FacScraper()
    return scraper.run(output_path=output_path)
