# Plan de Cierre — Auditoría de Promociones 2025

## Objetivo

Cerrar la auditoría 2025 para cuantificar y sustentar la fuga de ingreso por productos promocionales recibidos en compra pero no monetizados en venta.

## Estado actual (base documental)

- Brecha estimada actual: **USD 856.93**
- Ingreso esperado promociones: **USD 1,367.70**
- Ingreso monetizado promociones: **USD 510.77**
- Documentos SRI compras: **87**
- Documentos únicos: **72**
- Documentos duplicados: **30** (15 grupos)
- Archivos anómalos: **2**

## Alcance de cierre

1. Depuración de calidad de datos (duplicados y anomalías)
2. Validación metodológica-contable de monetización
3. Informe ejecutivo final con plan de acción

## Matriz de cierre (Evidencia → Riesgo → Acción)

| Evidencia | Riesgo | Acción de cierre |
|---|---|---|
| Brecha promo estimada USD 856.93 | Monto cuestionable por estimación | Documentar y aprobar regla de monetización (ventas cubren primero unidades pagadas, luego promociones) |
| 30 documentos duplicados, 15 grupos | Sobreestimación o sesgo en compras | Deduplicar por `clave_acceso` y regenerar datasets finales |
| 2 archivos anómalos | Trazabilidad incompleta | Corregir nomenclatura/formato y reparsear |
| Alta concentración de brecha en pocos SKU | Falta de priorización operativa | Atacar top SKU por impacto económico |

## Priorización por impacto (Top brecha)

1. SKU 500005 — ANTHEMIS TALCO 120GR — **USD 184.38**
2. SKU 400044 — PILOPEPTAN CHAMPÚ WOMAN — **USD 182.10**
3. SKU 500008 — LOCIÓN ANTITRANSPIRANTE 100ML — **USD 84.98**
4. SKU 500009 — LOCIÓN ANTITRANSPIRANTE 200ML — **USD 82.12**
5. SKU 500001 — 5-FLUOROURACILO 5% 30G — **USD 77.24**

## Plan operativo de cierre

### Fase 1 — Depuración y recálculo (Día 1)

- [ ] Resolver duplicados por `clave_acceso`
- [ ] Resolver/etiquetar archivos anómalos
- [ ] Regenerar:
  - `compras_2025_cabeceras.csv`
  - `compras_2025_detalles.csv`
  - `auditoria_promociones_2025.csv`
  - `sri_auditoria_*.csv`
- [ ] Recalcular brecha consolidada post-depuración

**Entregable:** base limpia y trazable.

### Fase 2 — Validación metodológica (Día 2)

- [ ] Revisar con responsable contable/comercial la regla de monetización promo
- [ ] Validar muestra de SKU top (al menos 10 SKU)
- [ ] Ajustar método si aplica y recalcular

**Entregable:** metodología validada y defendible.

### Fase 3 — Cierre ejecutivo (Día 3)

- [ ] Emitir informe final (1–2 páginas)
- [ ] Definir acciones correctivas por proceso (compra, facturación, control interno)
- [ ] Definir monitoreo mensual con KPI de fuga promo

**Entregable:** informe final + plan de acción.

## Criterios de aceptación de cierre

- Dataset deduplicado y reproducible
- Método de cálculo documentado y aprobado
- Brecha final cuantificada (USD y %)
- Top SKU con responsables y medidas correctivas
- Seguimiento mensual definido
