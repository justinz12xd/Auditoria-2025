from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings

engine = create_engine(settings.DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session():
    """Generador de sesión SQLAlchemy para usos futuros."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
