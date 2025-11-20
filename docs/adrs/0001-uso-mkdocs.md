# ADR-001: Uso de MkDocs para Documentación

**ID:** ADR-001
**Título:** Adopción de MkDocs como generador de sitio estático para documentación
**Estado:** Aceptado
**Fecha:** 2025-11-20

## Contexto
El proyecto necesita una forma centralizada y accesible de mantener la documentación técnica y funcional. Los documentos Markdown dispersos son difíciles de navegar para usuarios no técnicos.

## Decisión
Se eligió **MkDocs** con el tema **Material for MkDocs**.

*   **Porque:**
    *   Permite tratar la documentación como código (Docs as Code).
    *   Genera un sitio estático rápido y fácil de desplegar.
    *   Tiene excelente soporte para búsqueda y responsividad móvil.
    *   La comunidad y plugins son extensos.

## Consecuencias
*   **Positivas:**
    *   Centralización de la información.
    *   Búsqueda rápida para todos los stakeholders.
    *   Separación clara entre contenido (Markdown) y presentación.
*   **Negativas:**
    *   Requiere un paso de compilación (build) para ver el resultado final.

