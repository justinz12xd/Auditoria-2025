from pathlib import Path
import html
import xml.etree.ElementTree as ET

import pandas as pd
from loguru import logger

from src.config import PROCESSED_DIR, RAW_DIR

PRODUCT_TAGS = {"descripcion", "producto", "nombreproducto", "nombre", "detalle"}
QUANTITY_TAGS = {"cantidad", "qty", "quantity"}
UNIT_PRICE_TAGS = {"preciounitario", "precio_unitario", "precio", "valorunitario"}
DETAIL_CONTAINER_TAGS = {"detalle", "item", "producto", "linea", "line"}

HEADER_COLUMNS = [
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
]

DETAIL_COLUMNS = [
    "source_file",
    "clave_acceso",
    "numero_autorizacion",
    "fecha_emision",
    "codigo_principal",
    "codigo_auxiliar",
    "descripcion",
    "cantidad",
    "precio_unitario",
    "descuento",
    "precio_total_sin_impuesto",
    "impuesto_valor_total",
    "es_gratis",
]


def _clean_tag(tag: str) -> str:
    """Remueve namespace y normaliza un tag XML."""
    return tag.split("}", 1)[-1].replace("-", "_").lower()


def _to_float(value: str | None) -> float:
    if value is None:
        return 0.0
    cleaned = value.strip().replace(",", ".")
    return float(cleaned) if cleaned else 0.0


def _resolve_input_path(path: Path | str) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    if path.exists():
        return path

    raw_candidate = RAW_DIR / path
    if raw_candidate.exists():
        return raw_candidate

    return raw_candidate


def _find_text(element: ET.Element, candidate_tags: set[str]) -> str | None:
    for child in element.iter():
        if _clean_tag(child.tag) in candidate_tags and child.text:
            return child.text.strip()
    return None


def _find_child(element: ET.Element, candidate_tags: set[str]) -> ET.Element | None:
    for child in element.iter():
        if _clean_tag(child.tag) in candidate_tags:
            return child
    return None


def _find_direct_text(element: ET.Element, tag_name: str) -> str | None:
    for child in element:
        if _clean_tag(child.tag) == tag_name and child.text:
            return child.text.strip()
    return None


def _sum_tax_values(detail_element: ET.Element) -> float:
    total = 0.0
    for node in detail_element.iter():
        if _clean_tag(node.tag) == "impuesto":
            value = _find_text(node, {"valor"})
            total += _to_float(value)
    return total


def parse_invoices_xml(xml_path: Path | str) -> pd.DataFrame:
    """Parsea facturas XML y devuelve líneas de productos en un DataFrame.

    El parser es tolerante a namespaces y nombres comunes de campos. Si el XML
    real usa nombres distintos, ampliar las constantes *_TAGS de este módulo.
    """
    xml_path = _resolve_input_path(xml_path)

    logger.info("Parseando XML: {}", xml_path)
    tree = ET.parse(xml_path)
    root = tree.getroot()

    rows: list[dict[str, object]] = []
    for element in root.iter():
        tag = _clean_tag(element.tag)
        if tag not in DETAIL_CONTAINER_TAGS:
            continue

        product_name = _find_text(element, PRODUCT_TAGS)
        quantity_raw = _find_text(element, QUANTITY_TAGS)
        unit_price_raw = _find_text(element, UNIT_PRICE_TAGS)

        if not product_name or quantity_raw is None or unit_price_raw is None:
            continue

        quantity = _to_float(quantity_raw)
        unit_price = _to_float(unit_price_raw)
        rows.append(
            {
                "nombre_producto": product_name,
                "cantidad": quantity,
                "precio_unitario": unit_price,
                "es_gratis": unit_price == 0,
            }
        )

    df = pd.DataFrame(
        rows,
        columns=["nombre_producto", "cantidad", "precio_unitario", "es_gratis"],
    )
    logger.info("Facturas/productos extraídos: {}", len(df))
    return df


def parse_sri_authorization_xml(xml_path: Path | str) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Parsea un XML SRI con raíz <autorizacion> y retorna cabecera + detalles."""
    xml_path = _resolve_input_path(xml_path)
    tree = ET.parse(xml_path)
    root = tree.getroot()

    if _clean_tag(root.tag) != "autorizacion":
        raise ValueError(f"El archivo no tiene raíz <autorizacion>: {xml_path}")

    estado = _find_direct_text(root, "estado") or ""
    numero_autorizacion = _find_direct_text(root, "numeroautorizacion") or ""
    fecha_autorizacion = _find_direct_text(root, "fechaautorizacion") or ""
    ambiente_autorizacion = _find_direct_text(root, "ambiente") or ""
    comprobante_escaped = _find_direct_text(root, "comprobante") or ""

    if not comprobante_escaped:
        header = {
            "source_file": xml_path.name,
            "estado": estado,
            "numero_autorizacion": numero_autorizacion,
            "fecha_autorizacion": fecha_autorizacion,
            "ambiente_autorizacion": ambiente_autorizacion,
            "clave_acceso": "",
            "ruc_emisor": "",
            "cod_doc": "",
            "estab": "",
            "pto_emi": "",
            "secuencial": "",
            "fecha_emision": "",
            "identificacion_comprador": "",
            "razon_social_comprador": "",
            "total_sin_impuestos": 0.0,
            "importe_total": 0.0,
        }
        return header, []

    comprobante_xml = html.unescape(comprobante_escaped).strip()
    comprobante_root = ET.fromstring(comprobante_xml)

    info_tributaria = _find_child(comprobante_root, {"infotributaria"})
    info_factura = _find_child(comprobante_root, {"infofactura"})

    clave_acceso = _find_text(info_tributaria, {"claveacceso"}) if info_tributaria is not None else ""
    ruc_emisor = _find_text(info_tributaria, {"ruc"}) if info_tributaria is not None else ""
    cod_doc = _find_text(info_tributaria, {"coddoc"}) if info_tributaria is not None else ""
    estab = _find_text(info_tributaria, {"estab"}) if info_tributaria is not None else ""
    pto_emi = _find_text(info_tributaria, {"ptoemi"}) if info_tributaria is not None else ""
    secuencial = _find_text(info_tributaria, {"secuencial"}) if info_tributaria is not None else ""

    fecha_emision = _find_text(info_factura, {"fechaemision"}) if info_factura is not None else ""
    identificacion_comprador = (
        _find_text(info_factura, {"identificacioncomprador"}) if info_factura is not None else ""
    )
    razon_social_comprador = (
        _find_text(info_factura, {"razonsocialcomprador"}) if info_factura is not None else ""
    )
    total_sin_impuestos = _to_float(_find_text(info_factura, {"totalsinimpuestos"})) if info_factura is not None else 0.0
    importe_total = _to_float(_find_text(info_factura, {"importetotal"})) if info_factura is not None else 0.0

    header = {
        "source_file": xml_path.name,
        "estado": estado,
        "numero_autorizacion": numero_autorizacion,
        "fecha_autorizacion": fecha_autorizacion,
        "ambiente_autorizacion": ambiente_autorizacion,
        "clave_acceso": clave_acceso or "",
        "ruc_emisor": ruc_emisor or "",
        "cod_doc": cod_doc or "",
        "estab": estab or "",
        "pto_emi": pto_emi or "",
        "secuencial": secuencial or "",
        "fecha_emision": fecha_emision or "",
        "identificacion_comprador": identificacion_comprador or "",
        "razon_social_comprador": razon_social_comprador or "",
        "total_sin_impuestos": total_sin_impuestos,
        "importe_total": importe_total,
    }

    details: list[dict[str, object]] = []
    for node in comprobante_root.iter():
        if _clean_tag(node.tag) != "detalle":
            continue

        cantidad = _to_float(_find_text(node, {"cantidad"}))
        precio_unitario = _to_float(_find_text(node, {"preciounitario"}))
        descuento = _to_float(_find_text(node, {"descuento"}))
        precio_total_sin_impuesto = _to_float(_find_text(node, {"preciototalsinimpuesto"}))

        details.append(
            {
                "source_file": xml_path.name,
                "clave_acceso": clave_acceso or "",
                "numero_autorizacion": numero_autorizacion,
                "fecha_emision": fecha_emision or "",
                "codigo_principal": _find_text(node, {"codigoprincipal"}) or "",
                "codigo_auxiliar": _find_text(node, {"codigoauxiliar"}) or "",
                "descripcion": _find_text(node, {"descripcion"}) or "",
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "descuento": descuento,
                "precio_total_sin_impuesto": precio_total_sin_impuesto,
                "impuesto_valor_total": _sum_tax_values(node),
                "es_gratis": precio_unitario == 0,
            }
        )

    return header, details


def parse_sri_authorization_dir(xml_dir: Path | str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parsea un directorio de XMLs SRI y retorna DataFrames de cabeceras + detalles."""
    xml_dir = _resolve_input_path(xml_dir)

    if not xml_dir.exists() or not xml_dir.is_dir():
        raise FileNotFoundError(f"Directorio no encontrado: {xml_dir}")

    headers: list[dict[str, object]] = []
    details: list[dict[str, object]] = []

    xml_files = sorted(xml_dir.glob("*.xml"))
    logger.info("Procesando {} archivos XML en {}", len(xml_files), xml_dir)

    for xml_file in xml_files:
        try:
            header, detail_rows = parse_sri_authorization_xml(xml_file)
            headers.append(header)
            details.extend(detail_rows)
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo procesar {}: {}", xml_file.name, exc)

    headers_df = pd.DataFrame(headers, columns=HEADER_COLUMNS)
    details_df = pd.DataFrame(details, columns=DETAIL_COLUMNS)
    logger.info("Cabeceras extraídas: {} | Detalles extraídos: {}", len(headers_df), len(details_df))
    return headers_df, details_df


def save_sri_audit_csvs(
    xml_dir: Path | str,
    headers_output: Path | str = PROCESSED_DIR / "facturas_2025_cabeceras.csv",
    details_output: Path | str = PROCESSED_DIR / "facturas_2025_detalles.csv",
) -> tuple[Path, Path]:
    """Guarda CSVs normalizados de cabeceras y detalles para auditoría."""
    headers_output = Path(headers_output)
    if not headers_output.is_absolute():
        headers_output = PROCESSED_DIR / headers_output

    details_output = Path(details_output)
    if not details_output.is_absolute():
        details_output = PROCESSED_DIR / details_output

    headers_output.parent.mkdir(parents=True, exist_ok=True)
    details_output.parent.mkdir(parents=True, exist_ok=True)

    headers_df, details_df = parse_sri_authorization_dir(xml_dir)
    headers_df.to_csv(headers_output, index=False)
    details_df.to_csv(details_output, index=False)
    logger.info("CSV cabeceras guardado en {}", headers_output)
    logger.info("CSV detalles guardado en {}", details_output)
    return headers_output, details_output


def save_invoices_csv(
    xml_path: Path | str,
    output_path: Path | str = PROCESSED_DIR / "facturas_2025.csv",
) -> Path:
    output_path = Path(output_path)
    if not output_path.is_absolute():
        output_path = PROCESSED_DIR / output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = parse_invoices_xml(xml_path)
    df.to_csv(output_path, index=False)
    logger.info("CSV guardado en {}", output_path)
    return output_path
