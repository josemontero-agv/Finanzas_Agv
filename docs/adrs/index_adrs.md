# Decisiones Arquitectónicas (ADRs)

Los Registros de Decisiones Arquitectónicas (Architecture Decision Records - ADRs) documentan las decisiones importantes que afectan la estructura, tecnologías y patrones del sistema.

## ¿Por qué usamos ADRs?

- **Trazabilidad:** Mantener historial de las decisiones técnicas y su contexto.
- **Onboarding:** Nuevos miembros del equipo comprenden el "por qué" detrás del código.
- **Inmutabilidad:** Los ADRs no se eliminan; si una decisión cambia, se crea un nuevo ADR que reemplaza al anterior.

## 📚 Índice de ADRs

| ID | Estado | Título | Fecha |
| :--- | :--- | :--- | :--- |
| [ADR-001](0001-uso-mkdocs.md) | ✅ Aceptado | Uso de MkDocs para Documentación | 2025-11-20 |

---

## 🛠️ Cómo Crear un ADR

1. Usa la [plantilla](template.md) como base.
2. Asigna el siguiente número secuencial disponible.
3. Completa las secciones: Contexto, Decisión, Consecuencias.
4. Abre un Pull Request y vincula el ADR con el componente C4 afectado.

## Estados de un ADR

- **Propuesto:** En discusión, pendiente de aprobación.
- **Aceptado:** Decisión aprobada e implementada.
- **Rechazado:** Descartado sin implementar.
- **Reemplazado:** Superseded por un ADR más reciente (indicar cuál).

---

> **Nota:** Para más detalles sobre cómo escribir ADRs, consulta la [Guía de Contribución](../CONTRIBUTING.md).

