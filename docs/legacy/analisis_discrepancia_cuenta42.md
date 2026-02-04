# Análisis de Discrepancia - Reporte Cuenta 42

## Problema Identificado

Según la imagen proporcionada de Odoo, el reporte de "LETRAS POR PAGAR EXTERIOR" (cuenta 423003) al 31 de enero de 2025 muestra:

- **Debe**: S/ 20,759.15
- **Haber**: S/ 1,863,379.70
- **Saldo**: S/ -1,842,620.55 (Haber - Debe)

En la página web, solo se mostraba el "Pendiente al corte" pero no los totales de Débito, Haber y Saldo.

## Cambios Implementados

### 1. Indicador de Carga Interactivo ✅

Se agregó un overlay de carga con animación que aparece mientras se cargan los datos:

```html
<div x-show="loading" class="fixed inset-0 bg-gray-900 bg-opacity-50 z-50 flex items-center justify-center">
    <div class="bg-white rounded-lg shadow-xl p-8 flex flex-col items-center">
        <div class="animate-spin rounded-full h-16 w-16 border-b-4 border-primary"></div>
        <p class="text-lg font-semibold text-gray-700">Cargando datos...</p>
        <p class="text-sm text-gray-500 mt-2">Por favor espere</p>
    </div>
</div>
```

### 2. Mejora Visual del Resumen ✅

Se mejoró la visualización del resumen con:
- Colores distintivos para cada métrica
- Bordes más visibles
- Fondos de colores suaves
- Tamaños de fuente más grandes
- Contador de registros visible

### 3. Logs de Debug ✅

Se agregaron logs en la consola del navegador para facilitar la depuración:

```javascript
console.log('[DEBUG] Parámetros de consulta:', Object.fromEntries(params));
console.log('[DEBUG] Respuesta del servidor:', response.data);
console.log('[DEBUG] Total de registros:', this.allData.length);
console.log('[DEBUG] Resumen:', this.summary);
```

Y en el backend:

```python
print(f"[DEBUG RESUMEN] Total registros: {overall['count']}")
print(f"[DEBUG RESUMEN] Débito: {overall['debit']:.2f}")
print(f"[DEBUG RESUMEN] Haber: {overall['credit']:.2f}")
print(f"[DEBUG RESUMEN] Saldo: {overall['saldo']:.2f}")
```

### 4. Visibilidad Condicional ✅

Los campos "Pendiente al corte" y "Pagado después del corte" ahora solo se muestran cuando hay una fecha de corte seleccionada:

```html
<div x-show="filters.date_cutoff">
    <p class="text-sm text-orange-700 font-medium">Pendiente al corte</p>
    <p class="text-2xl font-bold text-orange-900" x-text="formatNumberWithCommas(summary.overall.pending_cutoff || 0)"></p>
</div>
```

## Posibles Causas de Discrepancia

### 1. Filtros Diferentes

**Odoo muestra**: Solo cuenta 423003 (LETRAS POR PAGAR EXTERIOR)
**Tu página web**: Cuentas 421, 422, 423, 424 (todas las subcuentas)

**Solución**: Ajusta el filtro de cuentas en la página web para que coincida con el de Odoo:
```javascript
account_codes_text: '423003'  // En lugar de '421,422,423,424'
```

### 2. Inclusión de Registros Conciliados

En el código, cuando hay `date_cutoff`, se fuerza `include_reconciled = True`:

```python
if date_cutoff:
    # En corte histórico incluir conciliados para cuadrar con el mayor
    include_reconciled = True
```

Esto es correcto para reportes históricos, pero verifica que Odoo también incluya los registros conciliados.

### 3. Tipos de Documento

El filtro actual incluye:
```python
('move_id.move_type', 'in', ['in_invoice', 'in_refund', 'entry', 'in_receipt', 'in_payment'])
```

Verifica que Odoo esté usando los mismos tipos de documento.

### 4. Estado de las Facturas

Solo se incluyen facturas en estado 'posted':
```python
('parent_state', '=', 'posted')
```

Verifica que Odoo no esté incluyendo borradores o canceladas.

## Cómo Verificar

### Paso 1: Revisar los Logs del Servidor

Cuando ejecutes la consulta, revisa los logs del servidor Flask para ver:
```
[DEBUG RESUMEN] Total registros: X
[DEBUG RESUMEN] Débito: X.XX
[DEBUG RESUMEN] Haber: X.XX
[DEBUG RESUMEN] Saldo: X.XX
[DEBUG RESUMEN] Cuentas encontradas: 421 (X), 422 (X), 423 (X), 424 (X)
```

### Paso 2: Revisar la Consola del Navegador

Abre las herramientas de desarrollo (F12) y ve a la pestaña "Console". Verás:
```
[DEBUG] Parámetros de consulta: {date_cutoff: "2025-01-31", account_codes: "421,422,423,424", ...}
[DEBUG] Respuesta del servidor: {success: true, data: [...], summary: {...}}
[DEBUG] Total de registros: X
[DEBUG] Resumen: {overall: {...}, by_account: [...]}
```

### Paso 3: Comparar Filtros

En Odoo, verifica exactamente qué filtros están aplicados:
- ¿Qué cuentas están incluidas?
- ¿Incluye registros conciliados?
- ¿Qué tipos de documento están incluidos?
- ¿Qué rango de fechas está usando?

### Paso 4: Ejecutar Script de Prueba

Ejecuta el script `test_treasury_summary.py` para ver un análisis detallado:

```bash
python test_treasury_summary.py
```

Esto te mostrará:
- Total de registros obtenidos
- Resumen general (Débito, Haber, Saldo)
- Resumen por cuenta
- Comparación con los valores esperados de Odoo
- Diferencias calculadas

## Recomendaciones

### 1. Filtro Específico para Cuenta 423003

Si quieres replicar exactamente el reporte de Odoo, usa:

```javascript
filters: {
    date_cutoff: '2025-01-31',
    account_codes_text: '423003',  // Solo esta cuenta
    limit: '10000',
    include_reconciled: true
}
```

### 2. Verificar Moneda

Asegúrate de que estés sumando solo los valores en soles (PEN). Si hay facturas en dólares, podrían estar afectando el cálculo.

### 3. Verificar Período Contable

Verifica que el período contable esté cerrado correctamente en Odoo al 31 de enero.

### 4. Comparar Línea por Línea

Exporta ambos reportes (Odoo y tu página web) a Excel y compara línea por línea para identificar qué registros están presentes en uno pero no en el otro.

## Próximos Pasos

1. ✅ Indicador de carga implementado
2. ✅ Mejora visual del resumen
3. ✅ Logs de debug agregados
4. 🔄 Ejecutar consulta con fecha de corte 31/01/2025
5. 🔄 Revisar logs y comparar con Odoo
6. 🔄 Ajustar filtros si es necesario
7. 🔄 Verificar que los cálculos coincidan

## Contacto

Si necesitas más ayuda, proporciona:
- Los logs del servidor
- Los logs de la consola del navegador
- Una captura de pantalla del resumen por cuenta
- Los filtros exactos que estás usando en Odoo

