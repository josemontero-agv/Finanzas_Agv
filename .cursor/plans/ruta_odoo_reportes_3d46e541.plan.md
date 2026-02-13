---
name: Ruta Odoo Reportes
overview: Definir una estrategia clara para reportes financieros en Odoo (consulta directa vs ETL/OLAP), y establecer un método repetible para descubrir modelos/campos correctos antes de construir reportes.
todos:
  - id: decision-framework
    content: Definir y documentar el criterio API directa vs ETL para tus reportes financieros prioritarios.
    status: pending
  - id: model-discovery-playbook
    content: Crear un playbook fijo para identificar modelos/campos Odoo correctos usando fields_get + search_read + validación de relaciones.
    status: pending
  - id: report-data-contract
    content: Construir contrato de datos del primer reporte crítico (letras/cxc) con fórmulas, filtros y validación contra Odoo.
    status: pending
  - id: olap-minimum-design
    content: Diseñar esquema analítico mínimo e incrementalidad para los reportes que no deben depender de consultas transaccionales directas.
    status: pending
  - id: todo-1770931973671-bfckqtb60
    content: ""
    status: pending
isProject: false
---

# Plan para reportes financieros en Odoo

## 1. Definir criterio de arquitectura (API directa vs ETL/OLAP)

- Usar un marco de decisión con 5 variables: volumen de datos, frecuencia del reporte, latencia permitida, complejidad de métricas y trazabilidad histórica.
- Recomendación práctica:
  - API/XML-RPC directa para reportes operativos de bajo/medio volumen y necesidad casi en tiempo real.
  - ETL a OLAP para cierres, comparativos históricos, KPIs complejos, alto volumen y requerimientos de performance/consistencia.
- En tu caso, arrancar con enfoque híbrido: operativo en directo + analítico en ETL.

## 2. Estandarizar exploración de modelos y campos Odoo

- Formalizar un flujo de descubrimiento antes de tocar cualquier reporte:
  - `fields_get` para inventario de campos y tipos.
  - `search_read` con muestra pequeña para validar datos reales.
  - Validación de relaciones Many2one/One2many y estados (`selection`).
- Reutilizar lo que ya tienes:
  - [C:/Users/jmontero/Desktop/GitHub Proyectos_AGV/Finanzas_Agv/scripts/investigation/modulo_letras_explicacion_3.py](C:/Users/jmontero/Desktop/GitHub Proyectos_AGV/Finanzas_Agv/scripts/investigation/modulo_letras_explicacion_3.py)
  - [C:/Users/jmontero/Desktop/GitHub Proyectos_AGV/Finanzas_Agv/app/core/odoo.py](C:/Users/jmontero/Desktop/GitHub Proyectos_AGV/Finanzas_Agv/app/core/odoo.py)
- Salida esperada: “diccionario funcional de datos” por reporte (modelo, campo técnico, etiqueta negocio, tipo, reglas de cálculo).

## 3. Diseñar contrato de datos para reportes

- Para cada reporte financiero, definir:
  - Métrica exacta (fórmula contable).
  - Fuente primaria en Odoo (`model.field`).
  - Filtros de negocio (estado, fechas, tipo de documento, compañía, moneda).
  - Validaciones cruzadas contra reportes de Odoo UI.
- Aplicarlo primero al caso de letras/facturas para cerrar el ciclo completo con un caso real.

## 4. Consolidar capa analítica (si aplica)

- Basado en scripts existentes ETL, consolidar modelo estrella mínimo (hechos + dimensiones) para CxC:
  - Referencia existente: [C:/Users/jmontero/Desktop/GitHub Proyectos_AGV/Finanzas_Agv/scripts/etl/etl_sync_threading.py](C:/Users/jmontero/Desktop/GitHub Proyectos_AGV/Finanzas_Agv/scripts/etl/etl_sync_threading.py)
- Definir incrementalidad y control de calidad:
  - Cargas por fecha/ID.
  - Conteos de control (origen vs destino).
  - Registro de errores y reintentos.

## 5. Ruta de aprendizaje aplicada (sin teoría suelta)

- Semana 1: ORM de Odoo, modelos, dominios y tipos relacionales.
- Semana 2: XML-RPC y patrón de extracción robusta (paginación, límites, validaciones).
- Semana 3: Diseño de métricas financieras y pruebas de reconciliación.
- Semana 4: ETL incremental y modelado OLAP mínimo para tus reportes más usados.
- Resultado: pasar de “explorar campos manualmente” a “pipeline repetible y auditado”.

