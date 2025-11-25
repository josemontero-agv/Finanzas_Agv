# RB-103: Generación y Actualización de Reportes Cuenta 12 y 42

**ID:** RB-103  
**Última Actualización:** 2025-11-25  
**Responsable:** José Montero  

## 🎯 Objetivo

Generar y actualizar los reportes de Cuenta 12 (Cuentas por Cobrar) y Cuenta 42 (Cuentas por Pagar) desde la plataforma externa de reportería.

## 📋 Prerrequisitos

- [ ] Acceso a la plataforma de reportería (URL: `https://finanzas.agrovetmarket.com`)
- [ ] Conexión estable con ODU (validar con [RB-101](rb-101-odoo-connection.md))
- [ ] Credenciales de usuario con rol de Finanzas/Tesorería

## 👣 Pasos de Ejecución

### 1. Verificar Conexión con ODU

```bash
# En el servidor de la aplicación
cd /opt/finanzas-agv
source venv/bin/activate
python diagnostic_odoo.py
```

**Salida esperada:**
```
✅ Conexión con ODU exitosa
✅ Permisos de lectura en account.move: OK
✅ Permisos de lectura en account.payment: OK
```

> ⚠️ **Si falla:** Consultar [RB-101: Conexión Odoo](rb-101-odoo-connection.md)

### 2. Acceder al Reporte de Cuenta 12 (Cuentas por Cobrar)

1. Ir a: `https://finanzas.agrovetmarket.com/collections/report-account12`
2. Aplicar filtros necesarios:
   - **Fecha desde:** [fecha_inicio]
   - **Fecha hasta:** [fecha_fin]
   - **Estado:** Pendiente / Pagado / Todos
   - **Moneda:** PEN / USD / Todos

3. Verificar columnas esperadas:
   - Número de Factura
   - Cliente
   - Fecha de Emisión
   - Fecha de Vencimiento
   - Moneda Original (USD/PEN)
   - Monto Original
   - Equivalente en Soles (si aplica)
   - Estado
   - Días de Atraso

### 3. Acceder al Reporte de Cuenta 42 (Cuentas por Pagar)

1. Ir a: `https://finanzas.agrovetmarket.com/treasury/report-account42`
2. Aplicar filtros necesarios:
   - **Fecha desde:** [fecha_inicio]
   - **Fecha hasta:** [fecha_fin]
   - **Proveedor:** [nombre_proveedor] o Todos
   - **Banco:** Interbank / BBVA / BCP / Todos
   - **Moneda:** PEN / USD / Todos

3. Verificar columnas esperadas (según solicitud de Marilia Tinoco):
   - Número de Factura
   - Proveedor
   - Número de Cuenta Bancaria
   - Banco
   - Fecha de Pago
   - Moneda Original
   - Monto Original
   - Equivalente en Soles (si aplica)
   - Estado de Retención
   - **Pedido por Orden de Compra** (solicitado Oct 13)
   - **Estado "Rendido/No Rendido"** (solicitado Oct 13)

### 4. Exportar Reporte a Excel

1. Hacer clic en el botón **"Exportar a Excel"**
2. Esperar descarga del archivo `.xlsx`
3. Verificar que el archivo contenga:
   - Todas las columnas visibles en pantalla
   - Formato correcto de fechas (YYYY-MM-DD)
   - Montos con 2 decimales

### 5. Validar Datos con ODU (Spot Check)

Para validar que los datos coinciden con ODU:

```python
# En el servidor o localmente con acceso a ODU
from app.core.odoo import OdooConnection

odoo = OdooConnection()
odoo.connect()

# Validar una factura específica
invoice = odoo.search_read('account.move', [('name', '=', 'FACTURA-001')], ['amount_total', 'state'])
print(invoice)
```

**Validaciones recomendadas:**
- [ ] Monto total coincide con ODU (±0.01 por redondeo)
- [ ] Estado coincide (draft/posted/paid)
- [ ] Fecha de emisión es correcta

## 🔍 Troubleshooting

### Problema: Reporte no carga datos

**Síntomas:**
- La tabla aparece vacía
- Mensaje "No se encontraron registros"

**Solución:**
1. Verificar filtros de fecha (ampliar rango)
2. Revisar logs del servidor:
   ```bash
   tail -f /var/log/finanzas-agv/app.log
   ```
3. Verificar conexión ODU (RB-101)

### Problema: Datos desactualizados

**Síntomas:**
- Pagos recientes no aparecen en el reporte
- El timestamp de última actualización es antiguo

**Solución:**
1. Forzar actualización desde ODU:
   ```bash
   cd /opt/finanzas-agv
   python -c "from app.core.odoo import OdooConnection; OdooConnection().sync_data()"
   ```
2. Limpiar caché del navegador (Ctrl + Shift + R)

### Problema: Columna faltante (ej. "Estado Rendido")

**Síntomas:**
- Usuarios reportan que falta una columna esperada

**Solución:**
1. Verificar si el campo existe en ODU:
   ```python
   odoo.search_read('purchase.order', [], limit=1)  # Ver todos los campos disponibles
   ```
2. Si el campo no existe, documentar en [ADR-002](../adrs/0002-plataforma-externa-reporteria.md)
3. Consultar con Marilia/Angie sobre campo alternativo

## 📊 KPIs de Monitoreo

| Métrica | Valor Esperado | ¿Qué hacer si falla? |
| :--- | :--- | :--- |
| **Tiempo de carga** | < 5 segundos | Optimizar query, revisar índices |
| **Precisión de datos** | 100% coincidencia con ODU | Revisar sincronización |
| **Disponibilidad** | 99.5% uptime | Escalar con infraestructura |

## 📅 Tareas Recurrentes

- **Diaria:** Verificar que el reporte de Cta 42 esté actualizado (Angie/Marilia)
- **Semanal:** Validar spot check de 5 facturas aleatorias vs. ODU
- **Mensual:** Revisar feedback de usuarios y solicitar mejoras

## 🔗 Referencias

- [ADR-002: Plataforma Externa para Reportería](../adrs/0002-plataforma-externa-reporteria.md)
- [RB-101: Conexión Odoo](rb-101-odoo-connection.md)
- [Código Fuente - Servicio de Cobranzas](../../app/collections/services.py)
- [Código Fuente - Servicio de Tesorería](../../app/treasury/services.py)
- [Reporte de Estado de Proyectos](../reporte-estado-proyectos.md)

## 📞 Contacto

**Si el runbook no resuelve el problema:**
- **Responsable Técnico:** José Montero
- **Usuarios Clave:** Marilia Tinoco, Angie Gomero, Kattya Barcena
- **Escalamiento:** Teodoro Balarezo (Jefe de Proyectos)

