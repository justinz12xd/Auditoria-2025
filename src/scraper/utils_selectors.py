"""Selectores del portal d2fac.

IMPORTANTE:
Se incluyen los selectores confirmados para login, navegación, modal de
reporte, fechas y descarga XML.
"""

# Login confirmado para https://www.d2fac.com/sistema/
USERNAME_SELECTOR = 'input[type="text"]'
PASSWORD_SELECTOR = 'input[type="password"]'
LOGIN_BUTTON_ROLE_NAME = "INGRESAR"

# Navegación posterior al login: Dashboard -> COMPROBANTES -> Reporte
COMPROBANTES_TEXT_SELECTOR = "text=COMPROBANTES"
COMPROBANTES_IONIC_FALLBACK_SELECTOR = 'ion-col:has-text("COMPROBANTES")'
REPORT_BUTTON_TEXT_SELECTOR = "text=Reporte"
REPORT_BUTTON_ROLE_NAME = "Reporte"

# Modal Reporte de Facturación
REPORT_MODAL_TITLE_SELECTOR = "text=Reporte de Facturación"
DATE_INPUTS_SELECTOR = "input.mat-input-element"
XML_DOWNLOAD_BUTTON_SELECTOR = "text=Descargar archivos XML"
