from pathlib import Path

import typer
from loguru import logger

from src.audit.sri_audit import save_sri_audit_reports
from src.audit.promo_audit import run_promo_audit
from src.parser.xml_parser import save_invoices_csv, save_sri_audit_csvs
from src.scraper.d2fac_scraper import DEFAULT_OUTPUT_FILE, scrape_d2fac_2025

app = typer.Typer(help="CLI del sistema de scraping administrativo")
scrape_app = typer.Typer(help="Comandos de scraping")
parse_app = typer.Typer(help="Comandos de procesamiento")
audit_app = typer.Typer(help="Comandos de auditoría")
app.add_typer(scrape_app, name="scrape")
app.add_typer(parse_app, name="parse")
app.add_typer(audit_app, name="audit")


@scrape_app.command("d2fac")
def scrape_d2fac(
    output: Path = typer.Option(
        DEFAULT_OUTPUT_FILE,
        "--output",
        "-o",
        help="Ruta local donde guardar el ZIP descargado con archivos XML.",
    )
) -> None:
    """Descarga el ZIP de archivos XML de facturas 2025 desde d2fac."""
    path = scrape_d2fac_2025(output_path=output)
    typer.echo(f"ZIP descargado: {path}")


@parse_app.command("xml")
def parse_xml(
    filename: str = typer.Argument(..., help="Archivo XML en data/raw o ruta absoluta."),
    output: Path = typer.Option(
        Path("facturas_2025.csv"),
        "--output",
        "-o",
        help="Archivo CSV de salida en data/processed o ruta absoluta.",
    ),
) -> None:
    """Procesa facturas XML y genera CSV limpio."""
    path = save_invoices_csv(filename, output_path=output)
    typer.echo(f"CSV generado: {path}")


@parse_app.command("xml-dir")
def parse_xml_dir(
    input_dir: str = typer.Argument(
        ...,
        help="Directorio con XMLs SRI (relativo a data/raw o ruta absoluta).",
    ),
    headers_output: Path = typer.Option(
        Path("facturas_2025_cabeceras.csv"),
        "--headers-output",
        help="Archivo CSV de salida para cabeceras en data/processed o ruta absoluta.",
    ),
    details_output: Path = typer.Option(
        Path("facturas_2025_detalles.csv"),
        "--details-output",
        help="Archivo CSV de salida para detalles en data/processed o ruta absoluta.",
    ),
) -> None:
    """Procesa un directorio de XML SRI y genera CSVs de auditoría."""
    headers_path, details_path = save_sri_audit_csvs(
        input_dir,
        headers_output=headers_output,
        details_output=details_output,
    )
    typer.echo(f"CSV cabeceras: {headers_path}")
    typer.echo(f"CSV detalles: {details_path}")


@parse_app.command("compras-dir")
def parse_compras_dir(
    input_dir: str = typer.Argument(
        ...,
        help="Directorio con XMLs de compras SRI (relativo a data/raw o ruta absoluta).",
    ),
    headers_output: Path = typer.Option(
        Path("compras_2025_cabeceras.csv"),
        "--headers-output",
        help="Archivo CSV de salida para cabeceras de compras.",
    ),
    details_output: Path = typer.Option(
        Path("compras_2025_detalles.csv"),
        "--details-output",
        help="Archivo CSV de salida para detalles de compras.",
    ),
) -> None:
    """Procesa un directorio de XML de compras y genera CSVs normalizados."""
    headers_path, details_path = save_sri_audit_csvs(
        input_dir,
        headers_output=headers_output,
        details_output=details_output,
    )
    typer.echo(f"CSV cabeceras compras: {headers_path}")
    typer.echo(f"CSV detalles compras: {details_path}")


@audit_app.command("promos")
def audit_promos(
    sales_details: Path = typer.Option(
        Path("facturas_2025_detalles.csv"),
        "--sales-details",
        help="CSV de detalles de ventas (generado con parse xml-dir).",
    ),
    purchases_details: Path = typer.Option(
        Path("compras_2025_detalles.csv"),
        "--purchases-details",
        help="CSV de detalles de compras (generado con parse compras-dir).",
    ),
    output: Path = typer.Option(
        Path("auditoria_promociones_2025.csv"),
        "--output",
        "-o",
        help="Archivo CSV de salida de la auditoría de promociones.",
    ),
    deduplicate_by_document: bool = typer.Option(
        True,
        "--deduplicate-by-document/--no-deduplicate-by-document",
        help="Depura líneas duplicadas de compras por clave/documento para cierre de auditoría.",
    ),
    exclude_anomalous_files: bool = typer.Option(
        True,
        "--exclude-anomalous-files/--include-anomalous-files",
        help="Excluye líneas de archivos con nombre anómalo para no sesgar el cierre.",
    ),
) -> None:
    """Cruza compras y ventas para estimar fuga por productos promocionales."""
    report_path = run_promo_audit(
        sales_details_path=sales_details,
        purchases_details_path=purchases_details,
        output_path=output,
        deduplicate_by_document=deduplicate_by_document,
        exclude_anomalous_files=exclude_anomalous_files,
    )
    typer.echo(f"Reporte de auditoría generado: {report_path}")


@audit_app.command("sri")
def audit_sri(
    headers_csv: Path = typer.Option(
        Path("compras_2025_cabeceras.csv"),
        "--headers-csv",
        help="CSV de cabeceras SRI generado desde data/pdf_sri.",
    ),
    details_csv: Path = typer.Option(
        Path("compras_2025_detalles.csv"),
        "--details-csv",
        help="CSV de detalles SRI generado desde data/pdf_sri.",
    ),
    output_prefix: Path = typer.Option(
        Path("sri_auditoria"),
        "--output-prefix",
        help="Prefijo para los CSV de salida.",
    ),
) -> None:
    """Genera un reporte de auditoría SRI desde los XML de compras."""
    report_paths = save_sri_audit_reports(
        headers_csv=headers_csv,
        details_csv=details_csv,
        output_prefix=output_prefix,
    )
    for label, path in report_paths.items():
        typer.echo(f"{label}: {path}")


if __name__ == "__main__":
    logger.info("Iniciando CLI")
    app()
