# ADR-002: Plataforma Externa para Reportería

**ID:** ADR-002  
**Título:** Uso de Plataforma Externa para Reportería en lugar de Desarrollo en ODU  
**Estado:** Aceptado  
**Fecha:** 2025-11-14  

## Contexto

El equipo de Tesorería y Créditos y Cobranzas requiere reportería especializada (Cuenta 12 y Cuenta 42) que ODU no proporciona de forma óptima:

1. **Limitaciones de ODU:**
   - Los reportes nativos no permiten exportación específica y automatizada
   - Falta de campos críticos (estado "rendido/no rendido", pedido por orden de compra)
   - No permite cortes por fecha flexibles
   - Las cabeceras no son personalizables según necesidades del usuario

2. **Restricciones Organizacionales:**
   - El área de Sistemas (Juana, TI) no tiene capacidad suficiente para desarrollar módulos ODU personalizados
   - José Montero no es desarrollador certificado de ODU
   - Los usuarios necesitan resultados en el corto plazo (entrega comprometida: viernes siguiente)

3. **Experiencia Previa:**
   - Los usuarios extrañan la funcionalidad de "query" que tenían en SAP
   - Necesitan replicar en reportería de cuentas por pagar lo que ya funciona en cuentas por cobrar

## Decisión

Se eligió la opción: **Construir una plataforma web externa (Flask + Python) que extraiga datos de ODU vía API y genere reportes personalizados.**

Porque:
- Permite desarrollo ágil sin depender de certificaciones de ODU
- Costo accesible ($20-$50 mensuales de hosting + $20 de IA de desarrollo)
- Escalabilidad: se puede agregar funcionalidades sin modificar el core de ODU
- Uso de IA para acelerar el desarrollo (aprobado por Jancarlo Pariasca)
- Ena, Juana y Teodoro están al tanto y aprueban esta estrategia

## Consecuencias

### Positivas:
- ✅ **Velocidad de desarrollo:** Reportes de Cta 12 y 42 listos en 2-3 semanas
- ✅ **Flexibilidad:** Campos personalizados según necesidad del usuario (moneda, estado rendido, OC)
- ✅ **Costo-beneficio:** Inversión baja vs. contratar desarrollo ODU externo
- ✅ **Experiencia de usuario:** Interfaz moderna, filtros en tiempo real, exportación a Excel
- ✅ **Independencia:** No afecta la estabilidad de ODU en producción
- ✅ **Reutilización:** Código base sirve para otros reportes (internacional, dashboards)

### Negativas/Riesgos:
- ❌ **Dependencia de API:** Si ODU cambia su API, hay que adaptar la integración (mitigado con RB-101)
- ❌ **Datos no en tiempo real absoluto:** Hay un pequeño delay en la sincronización (aceptable para usuarios)
- ❌ **Mantenimiento adicional:** Se suma una aplicación más al stack tecnológico
- ❌ **Doble fuente de verdad:** ODU sigue siendo el master, pero los reportes están en plataforma externa (documentado en C4)

### Estrategia de Mitigación:
1. Documentar la integración en [RB-101: Conexión Odoo](../runbooks/rb-101-odoo-connection.md)
2. Implementar sincronización automática cada X horas (configurable)
3. Incluir timestamp de última actualización en reportes
4. Planificar migración a PostgreSQL Read Replica en el futuro (ver [Análisis Arquitectónico](../mejoras-stack-arquitectura/analisis-arquitectonico-completo.md))

## Alternativas Consideradas

| Opción | Ventajas | Desventajas | ¿Por qué se descartó? |
| :--- | :--- | :--- | :--- |
| Desarrollo de módulo ODU nativo | Integración total, datos en tiempo real | Requiere certificación, costo alto, tiempo largo | No hay recursos internos con capacidad |
| Contratar desarrollador ODU externo | Solución profesional | Costo elevado ($3k-$5k), tiempo de entrega largo | Presupuesto no aprobado, urgencia de resultados |
| Usar reportes ODU actuales con Excel manual | Sin costo adicional | Proceso manual diario, propenso a errores, no escalable | No resuelve el problema de fondo (frustración de usuarios) |
| Google Sheets + AppScript | Gratis, familiar para usuarios | Lento con grandes volúmenes, difícil de mantener | No profesional, problemas de performance |

## Historial

- **2025-11-14** - José Montero - Creación inicial tras reunión con Jancarlo, Marilia y Kattya.
- **2025-11-14** - Aprobación verbal de Jancarlo Pariasca (Gerencia Finanzas).
- **2025-11-25** - Documentación formal en ADR.

## Referencias

- [RB-101: Conexión Odoo](../runbooks/rb-101-odoo-connection.md)
- [Análisis Arquitectónico Completo](../mejoras-stack-arquitectura/analisis-arquitectonico-completo.md)
- [Reporte de Estado de Proyectos](../reporte-estado-proyectos.md)

