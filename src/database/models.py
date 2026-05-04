from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class InvoiceProduct(Base):
    """Modelo inicial para líneas de productos extraídas de facturas."""

    __tablename__ = "invoice_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_producto: Mapped[str] = mapped_column(String(500), nullable=False)
    cantidad: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    es_gratis: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_file: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
