---
name: cuadre-letras-423
overview: Alinear reporte CxP (Cuenta 42) con letras 4230002/4230003 incluyendo estados to_accept/portfolio y validar saldos al corte
todos:
  - id: dominio-letras
    content: Incluir move_type letras y cuentas 4230002/3 en dominio CxP
    status: completed
  - id: boe-campos
    content: Exponer l10n_latam_boe_number en filas/resumen/export
    status: completed
  - id: calculo-historico
    content: Revisar residual histórico/saldo para letras con dif. cambio
    status: completed
  - id: prueba-corte
    content: Probar corte enero cuentas 4230002/3 y validar saldos
    status: pending
---

# Plan Cuadre letras 4230002/4230003

1) **Dominios y filtros**

- Actualizar dominio CxP para incluir `move_type` de letras (e.g. `entry`, `in_invoice`, `in_refund`, `in_receipt`, `in_payment`, `to_accept`, `portfolio` si aplica) y asegurar inclusión de cuentas 4230002/4230003.
- Verificar que en corte histórico se incluyan conciliados y se considere `l10n_latam_boe_number`.

2) **Procesamiento y cálculo histórico**

- Incluir en filas (Cuenta 42) el `l10n_latam_boe_number` para rastrear letras en UI y export.
- Revisar cálculo de `amount_residual_historical` para letras con dif. cambio: residual actual + pagos post-corte; validar que saldo (Débito-Haber) refleje mayor.

3) **Resumen y export Excel**

- Añadir columnas de BOE y saldo en export de CxP (Cuenta 42) si falta.
- Validar resumen por cuenta muestre saldo correcto de 4230002/4230003.

4) **Prueba focalizada**

- Consultar corte enero con cuenta 4230002 y 4230003; verificar Débito/Haber/Saldo vs Excel (ejemplo: -2,245,411.34 con ajuste 21,920.72).