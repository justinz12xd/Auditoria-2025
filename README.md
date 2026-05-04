# Sistema de scraping administrativo

Arquitectura base para automatización, scraping, extracción, procesamiento y almacenamiento de datos administrativos.

## Alcance actual

Por ahora **solo** se implementa el módulo de scraping para:

- `https://www.d2fac.com/sistema/`

El scraper inicia sesión, navega a **COMPROBANTES → Reporte**, escribe manualmente las fechas `2025-01-01` y `2025-12-31`, descarga el ZIP con archivos XML y lo guarda en `data/raw/reporte_2025.zip`.

No se implementa scraping de SRI ni de otras plataformas todavía.

## Estructura

```text
project/
├── cli.py
├── src/
│   ├── scraper/
│   │   ├── d2fac_scraper.py
│   │   ├── utils_selectors.py
│   │   └── utils_browser.py
│   ├── parser/
│   │   └── xml_parser.py
│   ├── database/
│   │   ├── models.py
│   │   └── db.py
│   ├── cli.py
│   └── config.py
├── data/
│   ├── raw/
│   └── processed/
├── dashboard/
├── .env.example
├── requirements.txt
└── README.md
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Edita `.env` con tus credenciales reales:

```env
D2_USER=tu_usuario
D2_PASS=tu_password
```

## Configurar selectores

Los selectores están centralizados en:

```text
src/scraper/utils_selectors.py
```

El flujo de login, navegación, modal, fechas y descarga ya tiene selectores confirmados:

```python
USERNAME_SELECTOR = 'input[type="text"]'
PASSWORD_SELECTOR = 'input[type="password"]'
LOGIN_BUTTON_ROLE_NAME = "INGRESAR"
COMPROBANTES_TEXT_SELECTOR = "text=COMPROBANTES"
COMPROBANTES_IONIC_FALLBACK_SELECTOR = 'ion-col:has-text("COMPROBANTES")'
REPORT_BUTTON_TEXT_SELECTOR = "text=Reporte"
REPORT_BUTTON_ROLE_NAME = "Reporte"
REPORT_MODAL_TITLE_SELECTOR = "text=Reporte de Facturación"
DATE_INPUTS_SELECTOR = "input.mat-input-element"
XML_DOWNLOAD_BUTTON_SELECTOR = "text=Descargar archivos XML"
```

El scraper espera los elementos antes de hacer click porque d2fac usa Angular/Ionic y renderiza dinámicamente.

## Correr el scraper

Desde la raíz del proyecto:

```bash
python -m cli scrape d2fac
```

Salida esperada:

```text
data/raw/reporte_2025.zip
```

También puedes indicar una ruta de salida:

```bash
python -m cli scrape d2fac --output data/raw/reporte_2025.zip
```

## Procesar XML a CSV

Cuando tengas un XML individual extraído del ZIP, puedes procesarlo con:

```bash
python -m cli parse xml facturas_2025.xml
```

Esto lee `data/raw/facturas_2025.xml` o una ruta absoluta y genera:

```text
data/processed/facturas_2025.csv
```

El parser extrae:

- `nombre_producto`
- `cantidad`
- `precio_unitario`
- `es_gratis` cuando `precio_unitario == 0`

### Procesar lote SRI (auditoría)

Para XMLs con estructura SRI (`<autorizacion>` + `<comprobante>` escapado) usa:

```bash
python -m cli parse xml-dir data/xml_facturas_1302177611001_2025-01-01_2025-12-31
```

Esto genera dos archivos en `data/processed/`:

- `facturas_2025_cabeceras.csv`
- `facturas_2025_detalles.csv`

Campos principales de cabecera:

- `estado`
- `numero_autorizacion`
- `fecha_autorizacion`
- `clave_acceso`
- `fecha_emision`
- `importe_total`

Campos principales de detalle:

- `codigo_principal`
- `descripcion`
- `cantidad`
- `precio_unitario`
- `precio_total_sin_impuesto`
- `impuesto_valor_total`
- `es_gratis`

### Procesar compras SRI (proveedores)

Si tienes XML de compras/proveedores (por ejemplo en `data/pdf_sri/`):

```bash
python -m cli parse compras-dir data/pdf_sri
```

Esto genera:

- `data/processed/compras_2025_cabeceras.csv`
- `data/processed/compras_2025_detalles.csv`

### Generar reporte SRI

Para crear un resumen de auditoría desde las compras procesadas:

```bash
python -m cli audit sri
```

Esto genera:

- `data/processed/sri_auditoria_resumen.csv`
- `data/processed/sri_auditoria_documentos.csv`
- `data/processed/sri_auditoria_mensual.csv`
- `data/processed/sri_auditoria_duplicados.csv`
- `data/processed/sri_auditoria_productos.csv`

## Auditoría de promociones

Con ventas y compras ya procesadas, ejecuta:

```bash
python -m cli audit promos
```

Salida:

- `data/processed/auditoria_promociones_2025.csv`

El reporte incluye por SKU:

- unidades compradas pagadas
- unidades promocionales obtenidas (líneas de compra con subtotal 0)
- unidades vendidas
- unidades promo monetizadas (estimadas)
- unidades promo no monetizadas (estimadas)
- ingreso esperado de promociones vs ingreso estimado monetizado
- brecha de ingreso por promociones

> Nota metodológica: la monetización de promos se estima asumiendo que las ventas
> cubren primero unidades pagadas y luego promociones.

## Base de datos

Se deja una estructura inicial con SQLAlchemy:

- `src/database/db.py`: conexión y sesiones.
- `src/database/models.py`: modelo inicial `InvoiceProduct`.

La variable `DATABASE_URL` se configura en `.env`.

## Dashboard

Se incluye dashboard interactivo con Streamlit en:

- `dashboard/app.py`

### Ejecutar dashboard

1. Procesa ventas, compras y auditoría:

```bash
python -m cli parse xml-dir data/xml_facturas_1302177611001_2025-01-01_2025-12-31
python -m cli parse compras-dir data/pdf_sri
python -m cli audit sri
python -m cli audit promos
```

2. Ejecuta la app:

```bash
streamlit run dashboard/app.py
```

En la barra lateral puedes cambiar entre dos vistas:

- **Compras SRI**: resúmenes de `data/pdf_sri`, duplicados, tendencia mensual, productos y documentos
- **Promociones**: análisis cruzado de ventas vs compras para estimar brecha promocional

Filtros disponibles en ambas vistas:

- rango de fechas
- producto (solo en Promociones)
- promociones (todos / con promociones / con brecha / sin brecha, solo en Promociones)

La tabla de detalle usa **st_aggrid** cuando está disponible para filtros/ordenamiento por columna y mejor análisis interactivo.

KPIs principales:

- documentos autorizados, duplicados, importe total, compradores únicos y archivos anómalos en la vista SRI
- brecha total de ingreso promocional
- unidades promo obtenidas
- unidades promo no monetizadas
- % de promos no monetizadas

## Agregar nuevos scrapers después

Para agregar una nueva plataforma en el futuro:

1. Crear un nuevo archivo en `src/scraper/`, por ejemplo `nuevo_portal_scraper.py`.
2. Crear o ampliar selectores en un archivo dedicado o en `utils_selectors.py`.
3. Reutilizar `utils_browser.py` para inicializar Playwright.
4. Agregar un comando en `src/cli.py`, por ejemplo:

```python
@scrape_app.command("nuevo-portal")
def scrape_nuevo_portal():
    ...
```

Mantener cada portal aislado para que los cambios de un scraper no rompan los demás.
