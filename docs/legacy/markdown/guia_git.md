# Guía para Contribuir a la Documentación

## 📝 Estructura de la Documentación

Nuestra documentación sigue el principio **Docs as Code** y está organizada en:

```
docs/
├── adrs/          # Registros de Decisiones Arquitectónicas
├── c4model/       # Modelos de arquitectura (Structurizr DSL)
├── runbooks/      # Procedimientos operacionales
└── *.md           # Documentación general del proyecto
```

## ✍️ Cómo Agregar un ADR

1. Copia la plantilla: `docs/adrs/template.md`
2. Renombra siguiendo el patrón: `XXXX-nombre-descriptivo.md`
3. Completa las secciones:
   - **Contexto:** ¿Qué problema resolvemos?
   - **Decisión:** ¿Qué elegimos y por qué?
   - **Consecuencias:** ¿Qué impacto tendrá?

### Ejemplo de ADR

```markdown
# ADR-002: Adopción de React para Frontend

**Estado:** Propuesto
**Fecha:** 2025-11-20

## Contexto
El frontend actual con Jinja2 tiene problemas de mantenibilidad...

## Decisión
Migrar a React con Redux Toolkit porque...

## Consecuencias
- Positivas: Mejor UX, componentes reutilizables
- Negativas: Curva de aprendizaje inicial
```

## 🏗️ Actualizar el Modelo C4

El archivo `docs/c4model/workspace.dsl` define nuestra arquitectura.

### Agregar un nuevo sistema externo

```dsl
newSystem = softwareSystem "Sistema Nuevo" "Descripción" "External System"
financeSystem -> newSystem "Interacción" "Protocolo"
```

## 🔧 Crear un Runbook

Los runbooks son procedimientos paso a paso. Usa este formato:

```markdown
# RB-XXX: Título del Procedimiento

## 🎯 Objetivo
Qué se logra con este runbook.

## 📋 Prerrequisitos
- [ ] Item 1
- [ ] Item 2

## 👣 Pasos
1. Paso detallado...
2. Comando: `example command`

## 🔙 Plan de Rollback
Qué hacer si algo falla.
```

## 🤖 CI/CD y Validaciones

Cada Pull Request ejecuta automáticamente:

1. **Lint de Markdown:** Verifica formato consistente.
2. **Validación DSL:** Asegura que el modelo C4 sea válido.
3. **Link Checker:** Detecta enlaces rotos.
4. **Referencias Cruzadas:** Valida trazabilidad entre ADRs, C4 y Runbooks.

### ⚠️ Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `markdownlint MD013` | Línea muy larga | Divide en múltiples líneas |
| `Structurizr validation failed` | Sintaxis DSL incorrecta | Revisa la [documentación oficial](https://docs.structurizr.com/) |
| `Broken link` | Referencia a archivo inexistente | Verifica la ruta relativa |

## 🚀 Vista Previa Local

Para ver la documentación antes de hacer commit:

```bash
mkdocs serve
```

Abre `http://127.0.0.1:8000` en tu navegador.

## 📚 Referencias

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Structurizr DSL](https://github.com/structurizr/dsl)
- [ADR Guidelines](https://adr.github.io/)

