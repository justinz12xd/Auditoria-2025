from pathlib import Path

import pandas as pd
from loguru import logger

from src.config import PROCESSED_DIR


def _resolve_processed_path(path: Path | str) -> Path:
    path = Path(path)
    if not path.is_absolute():
        path = PROCESSED_DIR / path
    return path


def _normalize_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def _build_sku(row: pd.Series) -> str:
    sku = _normalize_text(row.get("codigo_principal", ""))
    if sku:
        return sku
    return _normalize_text(row.get("descripcion", ""))


def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = {
        "codigo_principal",
        "descripcion",
        "cantidad",
        "precio_unitario",
        "descuento",
        "precio_total_sin_impuesto",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"CSV no contiene columnas requeridas: {sorted(missing)}")

    prepared = df.copy()
    prepared["sku"] = prepared.apply(_build_sku, axis=1)
    prepared["descripcion_norm"] = prepared["descripcion"].map(_normalize_text)

    for col in ["cantidad", "precio_unitario", "descuento", "precio_total_sin_impuesto"]:
        prepared[col] = pd.to_numeric(prepared[col], errors="coerce").fillna(0.0)

    prepared["es_linea_gratis"] = prepared["precio_total_sin_impuesto"] <= 0.000001
    return prepared


def _clean_purchases_df(
    purchases_df: pd.DataFrame,
    *,
    deduplicate_by_document: bool = True,
    exclude_anomalous_files: bool = True,
) -> tuple[pd.DataFrame, dict[str, float]]:
    if purchases_df.empty:
        return purchases_df.copy(), {
            "lineas_entrada": 0.0,
            "lineas_salida": 0.0,
            "lineas_removidas_anomalias": 0.0,
            "lineas_removidas_duplicados": 0.0,
        }

    cleaned = purchases_df.copy()
    before = len(cleaned)

    removed_anomalies = 0
    if exclude_anomalous_files and "source_file" in cleaned.columns:
        anomaly_mask = cleaned["source_file"].astype(str).str.contains(r"\([^)]*$", regex=True)
        removed_anomalies = int(anomaly_mask.sum())
        cleaned = cleaned.loc[~anomaly_mask].copy()

    removed_duplicates = 0
    if deduplicate_by_document:
        dedup_cols = [
            "clave_acceso",
            "codigo_principal",
            "descripcion_norm",
            "cantidad",
            "precio_unitario",
            "descuento",
            "precio_total_sin_impuesto",
        ]
        existing_cols = [c for c in dedup_cols if c in cleaned.columns]
        if existing_cols:
            before_dedup = len(cleaned)
            cleaned = cleaned.drop_duplicates(subset=existing_cols, keep="first").copy()
            removed_duplicates = before_dedup - len(cleaned)

    metrics = {
        "lineas_entrada": float(before),
        "lineas_salida": float(len(cleaned)),
        "lineas_removidas_anomalias": float(removed_anomalies),
        "lineas_removidas_duplicados": float(removed_duplicates),
    }
    return cleaned, metrics


def compute_promo_audit_df(sales_df: pd.DataFrame, purchases_df: pd.DataFrame) -> pd.DataFrame:
    if sales_df.empty and purchases_df.empty:
        return pd.DataFrame()

    purchases_group = (
        purchases_df.groupby("sku", dropna=False)
        .agg(
            descripcion_compra=("descripcion_norm", "first"),
            unidades_compradas_pagadas=("cantidad", lambda s: float(s[~purchases_df.loc[s.index, "es_linea_gratis"]].sum())),
            unidades_promocion_obtenidas=("cantidad", lambda s: float(s[purchases_df.loc[s.index, "es_linea_gratis"]].sum())),
            unidades_totales_compradas=("cantidad", "sum"),
            costo_total_comprado=(
                "cantidad",
                lambda s: float((s * purchases_df.loc[s.index, "precio_unitario"]).sum()),
            ),
            costo_total_pagado=(
                "cantidad",
                lambda s: float(
                    (s[~purchases_df.loc[s.index, "es_linea_gratis"]] * purchases_df.loc[s.index, "precio_unitario"]).sum()
                ),
            ),
        )
        .reset_index()
    )

    sales_group = (
        sales_df.groupby("sku", dropna=False)
        .agg(
            descripcion_venta=("descripcion_norm", "first"),
            unidades_vendidas=("cantidad", "sum"),
            subtotal_vendido=("precio_total_sin_impuesto", "sum"),
        )
        .reset_index()
    )
    sales_group["precio_promedio_venta"] = sales_group.apply(
        lambda row: (row["subtotal_vendido"] / row["unidades_vendidas"]) if row["unidades_vendidas"] > 0 else 0.0,
        axis=1,
    )

    report = purchases_group.merge(sales_group, on="sku", how="outer")
    report["descripcion"] = report["descripcion_venta"].fillna(report["descripcion_compra"])

    for col in [
        "unidades_compradas_pagadas",
        "unidades_promocion_obtenidas",
        "unidades_vendidas",
        "subtotal_vendido",
        "precio_promedio_venta",
        "unidades_totales_compradas",
        "costo_total_comprado",
        "costo_total_pagado",
    ]:
        report[col] = pd.to_numeric(report[col], errors="coerce").fillna(0.0)

    report["costo_unitario_referencia"] = report.apply(
        lambda row: (row["costo_total_pagado"] / row["unidades_compradas_pagadas"])
        if row["unidades_compradas_pagadas"] > 0
        else ((row["costo_total_comprado"] / row["unidades_totales_compradas"]) if row["unidades_totales_compradas"] > 0 else 0.0),
        axis=1,
    )
    report["unidades_promo_monetizadas"] = (
        (report["unidades_vendidas"] - report["unidades_compradas_pagadas"]).clip(lower=0.0)
    )
    report["unidades_promo_monetizadas"] = report[["unidades_promo_monetizadas", "unidades_promocion_obtenidas"]].min(axis=1)
    report["unidades_promo_no_monetizadas"] = (
        report["unidades_promocion_obtenidas"] - report["unidades_promo_monetizadas"]
    ).clip(lower=0.0)
    report["ingreso_esperado_promos"] = report["unidades_promocion_obtenidas"] * report["precio_promedio_venta"]
    report["ingreso_estimado_promos_monetizados"] = report["unidades_promo_monetizadas"] * report["precio_promedio_venta"]
    report["brecha_ingreso_promos"] = report["ingreso_esperado_promos"] - report["ingreso_estimado_promos_monetizados"]
    report["perdida_promos_no_monetizadas_costo"] = (
        report["unidades_promo_no_monetizadas"] * report["costo_unitario_referencia"]
    )
    report["ingreso_no_cobrado_potencial"] = report["unidades_promo_no_monetizadas"] * report["precio_promedio_venta"]
    report["margen_unitario_estimado"] = (
        report["precio_promedio_venta"] - report["costo_unitario_referencia"]
    ).clip(lower=0.0)
    report["ganancia_no_realizada_promos"] = (
        report["unidades_promo_no_monetizadas"] * report["margen_unitario_estimado"]
    )
    report["impacto_total_no_monetizadas"] = (
        report["perdida_promos_no_monetizadas_costo"] + report["ganancia_no_realizada_promos"]
    )
    report["balance_unidades_2025"] = report["unidades_totales_compradas"] - report["unidades_vendidas"]
    report["stock_teorico_cierre_2025"] = report["balance_unidades_2025"].clip(lower=0.0)
    report["deficit_unidades_vs_entradas_2025"] = (-report["balance_unidades_2025"]).clip(lower=0.0)
    report["%_promos_no_monetizadas"] = report.apply(
        lambda row: (row["unidades_promo_no_monetizadas"] / row["unidades_promocion_obtenidas"] * 100)
        if row["unidades_promocion_obtenidas"] > 0
        else 0.0,
        axis=1,
    )

    return report


def run_promo_audit(
    sales_details_path: Path | str,
    purchases_details_path: Path | str,
    output_path: Path | str,
    *,
    deduplicate_by_document: bool = True,
    exclude_anomalous_files: bool = True,
) -> Path:
    """Genera auditoría de promociones por SKU cruzando compras vs ventas.

    Supuesto principal: cuando en compras existe línea gratis (subtotal 0), esas
    unidades deben eventualmente venderse para capturar utilidad.
    """

    sales_details_path = _resolve_processed_path(sales_details_path)
    purchases_details_path = _resolve_processed_path(purchases_details_path)
    output_path = _resolve_processed_path(output_path)

    if not sales_details_path.exists():
        raise FileNotFoundError(f"No existe CSV de ventas: {sales_details_path}")
    if not purchases_details_path.exists():
        raise FileNotFoundError(f"No existe CSV de compras: {purchases_details_path}")

    logger.info("Leyendo ventas desde {}", sales_details_path)
    sales_df = _prepare_df(pd.read_csv(sales_details_path))
    logger.info("Leyendo compras desde {}", purchases_details_path)
    purchases_df = _prepare_df(pd.read_csv(purchases_details_path))
    purchases_df, cleaning_metrics = _clean_purchases_df(
        purchases_df,
        deduplicate_by_document=deduplicate_by_document,
        exclude_anomalous_files=exclude_anomalous_files,
    )

    report = compute_promo_audit_df(sales_df, purchases_df)

    report = report[
        [
            "sku",
            "descripcion",
            "unidades_compradas_pagadas",
            "unidades_promocion_obtenidas",
            "unidades_vendidas",
            "precio_promedio_venta",
            "costo_unitario_referencia",
            "margen_unitario_estimado",
            "unidades_promo_monetizadas",
            "unidades_promo_no_monetizadas",
            "stock_teorico_cierre_2025",
            "deficit_unidades_vs_entradas_2025",
            "%_promos_no_monetizadas",
            "ingreso_esperado_promos",
            "ingreso_estimado_promos_monetizados",
            "brecha_ingreso_promos",
            "perdida_promos_no_monetizadas_costo",
            "ganancia_no_realizada_promos",
            "impacto_total_no_monetizadas",
            "ingreso_no_cobrado_potencial",
        ]
    ].sort_values(by="brecha_ingreso_promos", ascending=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(output_path, index=False)

    closure_summary = pd.DataFrame(
        [
            {
                **cleaning_metrics,
                "skus_con_promos": float((report["unidades_promocion_obtenidas"] > 0).sum()),
                "skus_con_promos_no_monetizadas": float((report["unidades_promo_no_monetizadas"] > 0).sum()),
                "brecha_ingreso_promos_total": float(report["brecha_ingreso_promos"].sum()),
                "perdida_promos_no_monetizadas_costo_total": float(
                    report["perdida_promos_no_monetizadas_costo"].sum()
                ),
                "ganancia_no_realizada_promos_total": float(report["ganancia_no_realizada_promos"].sum()),
                "impacto_total_no_monetizadas": float(report["impacto_total_no_monetizadas"].sum()),
                "ingreso_no_cobrado_potencial_total": float(report["ingreso_no_cobrado_potencial"].sum()),
                "stock_teorico_cierre_2025_total_unidades": float(report["stock_teorico_cierre_2025"].sum()),
                "deficit_unidades_vs_entradas_2025_total": float(report["deficit_unidades_vs_entradas_2025"].sum()),
                "ingreso_esperado_promos_total": float(report["ingreso_esperado_promos"].sum()),
                "ingreso_estimado_promos_monetizados_total": float(
                    report["ingreso_estimado_promos_monetizados"].sum()
                ),
            }
        ]
    )
    closure_summary_path = output_path.with_name(f"{output_path.stem}_cierre_resumen.csv")
    closure_summary.to_csv(closure_summary_path, index=False)

    logger.info("Reporte de auditoría guardado en {}", output_path)
    logger.info("Resumen de cierre guardado en {}", closure_summary_path)
    return output_path
