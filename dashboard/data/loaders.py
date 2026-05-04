from __future__ import annotations

from pathlib import Path

import pandas as pd


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def build_sku(df: pd.DataFrame) -> pd.Series:
    codigo = df["codigo_principal"].fillna("").astype(str).str.strip().str.upper()
    descripcion = df["descripcion"].fillna("").astype(str).str.strip().str.upper()
    return codigo.where(codigo != "", descripcion)


def load_headers_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    required = {
        "source_file",
        "estado",
        "numero_autorizacion",
        "fecha_autorizacion",
        "ambiente_autorizacion",
        "clave_acceso",
        "ruc_emisor",
        "cod_doc",
        "estab",
        "pto_emi",
        "secuencial",
        "fecha_emision",
        "identificacion_comprador",
        "razon_social_comprador",
        "total_sin_impuestos",
        "importe_total",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en {path.name}: {sorted(missing)}")

    prepared = df.copy()
    prepared["fecha"] = pd.to_datetime(prepared["fecha_emision"], format="%d/%m/%Y", errors="coerce")
    prepared["importe_total"] = pd.to_numeric(prepared["importe_total"], errors="coerce").fillna(0.0)
    prepared["total_sin_impuestos"] = pd.to_numeric(
        prepared["total_sin_impuestos"], errors="coerce"
    ).fillna(0.0)
    prepared["clave_acceso"] = prepared["clave_acceso"].astype(str)
    prepared["source_file"] = prepared["source_file"].astype(str)
    prepared["duplicado"] = prepared.duplicated(subset=["clave_acceso"], keep=False)
    prepared["veces_clave"] = prepared.groupby("clave_acceso")["source_file"].transform("size")
    prepared["anio_mes"] = prepared["fecha"].dt.to_period("M").astype(str)
    prepared["archivo_anomalo"] = prepared["source_file"].str.contains(r"\([^)]*$", regex=True)
    return prepared


def load_details_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    required = {"fecha_emision", "codigo_principal", "descripcion", "cantidad", "precio_total_sin_impuesto"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en {path.name}: {sorted(missing)}")

    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha_emision"], format="%d/%m/%Y", errors="coerce")
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(0.0)
    df["precio_total_sin_impuesto"] = pd.to_numeric(df["precio_total_sin_impuesto"], errors="coerce").fillna(0.0)
    df["sku"] = build_sku(df)
    df["descripcion_norm"] = df["descripcion"].map(normalize_text)
    df["es_linea_gratis"] = df["precio_total_sin_impuesto"] <= 0.000001
    return df
