from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

load_dotenv(BASE_DIR / ".env")


class Settings:
    D2FAC_URL: str = os.getenv("D2FAC_URL", "https://www.d2fac.com/sistema/")
    D2FAC_USERNAME: str | None = os.getenv("D2_USER") or os.getenv("D2FAC_USERNAME")
    D2FAC_PASSWORD: str | None = os.getenv("D2_PASS") or os.getenv("D2FAC_PASSWORD")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/scraping_admin",
    )
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() in {"1", "true", "yes", "y"}
    DOWNLOAD_TIMEOUT_MS: int = int(os.getenv("DOWNLOAD_TIMEOUT_MS", "120000"))


settings = Settings()
