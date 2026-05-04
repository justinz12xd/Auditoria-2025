from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from src.config import PROCESSED_DIR

DEFAULT_HEADERS_CSV = PROCESSED_DIR / "compras_2025_cabeceras.csv"
DEFAULT_DETAILS_CSV = PROCESSED_DIR / "compras_2025_detalles.csv"
DEFAULT_OUTPUT_PREFIX = PROCESSED_DIR / "sri_auditoria"


def _load_csv(path: Path | str) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _prepare_headers(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    prepared = df.copy()
    prepared["source_file"] = prepared["source_file"].astype(str)
    prepared["clave_acceso"] = prepared["clave_acceso"].astype(str)
    prepared["estado"] = prepared["estado"].astype(str)
    prepared["ruc_emisor"] = prepared["ruc_emisor"].astype(str)
    prepared["identificacion_comprador"] = prepared["identificacion_comprador"].astype(str)
    prepared["razon_social_comprador"] = prepared["razon_social_comprador"].astype(str)
    prepared["fecha_emision_dt"] = pd.to_datetime(
        prepared["fecha_emision"], format="%d/%m/%Y", errors="coerce"
    )
    prepared["importe_total"] = pd.to_numeric(prepared["importe_total"], errors="coerce").fillna(0.0)
    prepared["total_sin_impuestos"] = pd.to_numeric(
        prepared["total_sin_impuestos"], errors="coerce"
    ).fillna(0.0)
    prepared["duplicado"] = prepared.duplicated(subset=["clave_acceso"], keep=False)
    prepared["veces_clave"] = prepared.groupby("clave_acceso")["source_file"].transform("size")
    prepared["anio_mes"] = prepared["fecha_emision_dt"].dt.to_period("M").astype(str)
    prepared["archivo_anomalo"] = prepared["source_file"].str.contains(r"\([^)]*$", regex=True)
    return prepared


def _prepare_details(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    prepared = df.copy()
    prepared["source_file"] = prepared["source_file"].astype(str)
    prepared["clave_acceso"] = prepared["clave_acceso"].astype(str)
    prepared["descripcion"] = prepared["descripcion"].fillna("").astype(str).str.strip()
    prepared["descripcion_norm"] = prepared["descripcion"].str.upper()
    prepared["fecha_emision_dt"] = pd.to_datetime(
        prepared["fecha_emision"], format="%d/%m/%Y", errors="coerce"
    )
    prepared["cantidad"] = pd.to_numeric(prepared["cantidad"], errors="coerce").fillna(0.0)
    prepared["precio_unitario"] = pd.to_numeric(prepared["precio_unitario"], errors="coerce").fillna(0.0)
    prepared["descuento"] = pd.to_numeric(prepared["descuento"], errors="coerce").fillna(0.0)
    prepared["precio_total_sin_impuesto"] = pd.to_numeric(
        prepared["precio_total_sin_impuesto"], errors="coerce"
    ).fillna(0.0)
    prepared["impuesto_valor_total"] = pd.to_numeric(
        prepared["impuesto_valor_total"], errors="coerce"
    ).fillna(0.0)
    prepared["es_gratis"] = prepared["precio_total_sin_impuesto"] <= 0.000001
    prepared["sku"] = prepared["codigo_principal"].fillna("").astype(str).str.strip()
    prepared.loc[prepared["sku"] == "", "sku"] = prepared["descripcion_norm"]
    prepared["anio_mes"] = prepared["fecha_emision_dt"].dt.to_period("M").astype(str)
    return prepared


def build_summary(headers_df: pd.DataFrame, details_df: pd.DataFrame | None = None) -> dict[str, Any]:
    headers = _prepare_headers(headers_df)
    details = _prepare_details(details_df) if details_df is not None else pd.DataFrame()

    if headers.empty:
        return {
            "total_documentos": 0,
            "documentos_unicos": 0,
            "documentos_duplicados": 0,
            "grupos_duplicados": 0,
            "documentos_autorizados": 0,
            "importe_total": 0.0,
            "fecha_inicio": "",
            "fecha_fin": "",
            "emisores_unicos": 0,
            "compradores_unicos": 0,
            "archivos_anomalos": 0,
            "total_lineas": 0,
            "lineas_gratis": 0,
            "productos_unicos": 0,
            "unidades_totales": 0.0,
        }

    duplicate_mask = headers["duplicado"]
    fecha_min = headers["fecha_emision_dt"].min()
    fecha_max = headers["fecha_emision_dt"].max()

    summary: dict[str, Any] = {
        "total_documentos": int(len(headers)),
        "documentos_unicos": int(headers["clave_acceso"].nunique()),
        "documentos_duplicados": int(duplicate_mask.sum()),
        "grupos_duplicados": int(headers.loc[duplicate_mask, "clave_acceso"].nunique()),
        "documentos_autorizados": int((headers["estado"] == "AUTORIZADO").sum()),
        "importe_total": float(headers["importe_total"].sum()),
        "fecha_inicio": fecha_min.date().isoformat() if pd.notna(fecha_min) else "",
        "fecha_fin": fecha_max.date().isoformat() if pd.notna(fecha_max) else "",
        "emisores_unicos": int(headers["ruc_emisor"].nunique()),
        "compradores_unicos": int(headers["identificacion_comprador"].nunique()),
        "archivos_anomalos": int(headers["archivo_anomalo"].sum()),
        "total_lineas": 0,
        "lineas_gratis": 0,
        "productos_unicos": 0,
        "unidades_totales": 0.0,
    }

    if not details.empty:
        summary["total_lineas"] = int(len(details))
        summary["lineas_gratis"] = int(details["es_gratis"].sum())
        summary["productos_unicos"] = int(details["sku"].nunique())
        summary["unidades_totales"] = float(details["cantidad"].sum())

    return summary


def build_document_report(headers_df: pd.DataFrame) -> pd.DataFrame:
    headers = _prepare_headers(headers_df)
    if headers.empty:
        return pd.DataFrame(
            columns=[
                "source_file",
                "clave_acceso",
                "fecha_emision",
                "estado",
                "importe_total",
                "duplicado",
                "veces_clave",
                "archivo_anomalo",
                "anio_mes",
            ]
        )

    report = headers[
        [
            "source_file",
            "clave_acceso",
            "fecha_emision",
            "estado",
            "importe_total",
            "duplicado",
            "veces_clave",
            "archivo_anomalo",
            "anio_mes",
            "identificacion_comprador",
            "razon_social_comprador",
        ]
    ].copy()
    return report.sort_values(["fecha_emision", "source_file"])


def build_monthly_report(headers_df: pd.DataFrame) -> pd.DataFrame:
    headers = _prepare_headers(headers_df)
    if headers.empty:
        return pd.DataFrame(
            columns=[
                "anio_mes",
                "documentos",
                "documentos_unicos",
                "documentos_duplicados",
                "importe_total",
            ]
        )

    monthly = (
        headers.groupby("anio_mes", dropna=False)
        .agg(
            documentos=("source_file", "count"),
            documentos_unicos=("clave_acceso", "nunique"),
            documentos_duplicados=("duplicado", "sum"),
            importe_total=("importe_total", "sum"),
        )
        .reset_index()
    )
    return monthly.sort_values("anio_mes")


def build_duplicate_report(headers_df: pd.DataFrame) -> pd.DataFrame:
    headers = _prepare_headers(headers_df)
    if headers.empty:
        return pd.DataFrame(
            columns=[
                "clave_acceso",
                "veces_clave",
                "fecha_emision_min",
                "fecha_emision_max",
                "importe_total",
                "archivos",
            ]
        )

    dup = headers[headers["duplicado"]].copy()
    if dup.empty:
        return pd.DataFrame(
            columns=[
                "clave_acceso",
                "veces_clave",
                "fecha_emision_min",
                "fecha_emision_max",
                "importe_total",
                "archivos",
            ]
        )

    grouped = (
        dup.groupby("clave_acceso", dropna=False)
        .agg(
            veces_clave=("source_file", "size"),
            fecha_emision_min=("fecha_emision_dt", lambda s: s.min().date().isoformat() if s.notna().any() else ""),
            fecha_emision_max=("fecha_emision_dt", lambda s: s.max().date().isoformat() if s.notna().any() else ""),
            importe_total=("importe_total", "first"),
            archivos=("source_file", lambda s: ", ".join(sorted(dict.fromkeys(s.astype(str))))),
        )
        .reset_index()
    )
    return grouped.sort_values(["veces_clave", "clave_acceso"], ascending=[False, True])


def build_product_report(details_df: pd.DataFrame) -> pd.DataFrame:
    details = _prepare_details(details_df)
    if details.empty:
        return pd.DataFrame(
            columns=[
                "sku",
                "descripcion",
                "lineas",
                "unidades",
                "unidades_gratis",
                "importe_total",
            ]
        )

    report = (
        details.groupby("sku", dropna=False)
        .agg(
            descripcion=("descripcion", "first"),
            lineas=("source_file", "size"),
            unidades=("cantidad", "sum"),
            unidades_gratis=("cantidad", lambda s: float(details.loc[s.index, "cantidad"][details.loc[s.index, "es_gratis"]].sum())),
            importe_total=("precio_total_sin_impuesto", "sum"),
        )
        .reset_index()
    )
    return report.sort_values(["unidades", "importe_total"], ascending=[False, False])


def save_sri_audit_reports(
    headers_csv: Path | str = DEFAULT_HEADERS_CSV,
    details_csv: Path | str = DEFAULT_DETAILS_CSV,
    output_prefix: Path | str = DEFAULT_OUTPUT_PREFIX,
) -> dict[str, Path]:
    headers_csv = Path(headers_csv)
    if not headers_csv.is_absolute():
        headers_csv = PROCESSED_DIR / headers_csv
    details_csv = Path(details_csv)
    if not details_csv.is_absolute():
        details_csv = PROCESSED_DIR / details_csv
    output_prefix = Path(output_prefix)
    if not output_prefix.is_absolute():
        output_prefix = PROCESSED_DIR / output_prefix

    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    headers_df = _load_csv(headers_csv)
    details_df = _load_csv(details_csv)
    if headers_df.empty:
        raise FileNotFoundError(f"No se encontró el CSV de cabeceras: {headers_csv}")

    summary = build_summary(headers_df, details_df)
    document_report = build_document_report(headers_df)
    monthly_report = build_monthly_report(headers_df)
    duplicate_report = build_duplicate_report(headers_df)
    product_report = build_product_report(details_df)

    summary_path = output_prefix.with_name(f"{output_prefix.name}_resumen.csv")
    documents_path = output_prefix.with_name(f"{output_prefix.name}_documentos.csv")
    monthly_path = output_prefix.with_name(f"{output_prefix.name}_mensual.csv")
    duplicates_path = output_prefix.with_name(f"{output_prefix.name}_duplicados.csv")
    products_path = output_prefix.with_name(f"{output_prefix.name}_productos.csv")

    pd.DataFrame([summary]).to_csv(summary_path, index=False)
    document_report.to_csv(documents_path, index=False)
    monthly_report.to_csv(monthly_path, index=False)
    duplicate_report.to_csv(duplicates_path, index=False)
    product_report.to_csv(products_path, index=False)

    logger.info("Reporte SRI guardado en {}", summary_path)
    logger.info("Documentos SRI guardados en {}", documents_path)
    logger.info("Reporte mensual SRI guardado en {}", monthly_path)
    logger.info("Duplicados SRI guardados en {}", duplicates_path)
    logger.info("Productos SRI guardados en {}", products_path)

    return {
        "summary": summary_path,
        "documents": documents_path,
        "monthly": monthly_path,
        "duplicates": duplicates_path,
        "products": products_path,
    }
