# ADR-003: Estrategia de Envío Masivo de Correos con Constancias Bancarias

**ID:** ADR-003  
**Título:** Automatización de Envío de Comprobantes de Pago con Adjuntos Bancarios  
**Estado:** Propuesto  
**Fecha:** 2025-10-13  

## Contexto

El área de Tesorería necesita enviar comprobantes de pago a proveedores de forma masiva y automatizada:

1. **Situación Actual (según reunión Oct 13):**
   - Juana (TI) ya envió un modelo de plantilla para envío automático de correos con detalles de factura
   - El sistema actual adjunta el **recibo de pago de ODU**
   - Los usuarios necesitan adjuntar la **constancia de pago del banco** (no el recibo de ODU)

2. **Problema Identificado:**
   - Las constancias de pago bancarias están en archivos separados (PDF, imagen, etc.)
   - No hay forma de adjuntarlas masivamente al momento de registrar pagos en ODU
   - El proceso manual de envío al final del día consume tiempo y es propenso a errores

3. **Solicitud de Usuarios (Angie Gomero, Marilia Tinoco):**
   - Opción para adjuntar masivamente las constancias de pago al registrar pagos en ODU
   - Envío automático a proveedores al final del día con las constancias correctas

## Decisión

Se eligió la opción: **Pendiente de análisis técnico detallado.**

Opciones en evaluación:
1. **Extensión de ODU** - Agregar campo de adjunto en registro de pago
2. **Sistema Intermedio** - Plataforma externa que reciba PDFs bancarios y los vincule con pagos de ODO
3. **Integración Bancaria Directa** - Obtener constancias directamente desde APIs de bancos (Interbank, BBVA)

## Consecuencias

### Positivas (esperadas):
- ✅ Reducción de tiempo operativo en Tesorería (estimado: 2-3 horas/día)
- ✅ Eliminación de errores de envío manual
- ✅ Mejor comunicación con proveedores (comprobante bancario oficial)
- ✅ Trazabilidad completa del proceso de pago

### Negativas/Riesgos:
- ❌ Complejidad técnica si se requiere integración con múltiples bancos
- ❌ Posible costo de APIs bancarias (a validar)
- ❌ Mantenimiento adicional de sistema de adjuntos

## Alternativas Consideradas

| Opción | Ventajas | Desventajas | Estado |
| :--- | :--- | :--- | :--- |
| **Modificar módulo ODU** | Integración total | Requiere certificación ODU, complejidad alta | En evaluación |
| **Sistema externo de adjuntos** | Desarrollo propio, flexible | Requiere desarrollo adicional | En evaluación |
| **API bancaria directa** | Automatización completa | Costo de APIs, disponibilidad incierta | Pendiente de consulta |
| **Portal web de carga manual mejorada** | Fácil de implementar | Sigue siendo semi-manual | Solución temporal posible |

## Tareas Pendientes

- [ ] Consultar con Teodoro sobre capacidad de TI para modificar módulo ODU
- [ ] Investigar APIs de Interbank y BBVA para descarga automática de comprobantes
- [ ] Validar con Angie y Marilia el flujo esperado (mockups/wireframes)
- [ ] Estimar costo de desarrollo vs. costo de APIs bancarias
- [ ] Definir formato estándar de almacenamiento de constancias (servidor, cloud, etc.)

## Historial

- **2025-10-13** - Solicitud inicial en reunión de levante de información (Angie, Marilia).
- **2025-11-25** - Creación de ADR para documentar la necesidad y opciones.

## Referencias

- [RB-102: Envío de Correos](../runbooks/rb-102-email-failure.md)
- [Reporte de Estado de Proyectos](../reporte-estado-proyectos.md)

