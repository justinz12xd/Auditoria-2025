"""Wrapper para permitir `python -m cli ...` desde la raíz del proyecto."""
from src.cli import app

if __name__ == "__main__":
    app()
