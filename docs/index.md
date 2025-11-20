# Documentación Finanzas AGV

Bienvenido a la documentación centralizada del proyecto **Finanzas AGV**. Aquí encontrarás toda la información relevante sobre la arquitectura, guías de uso, decisiones técnicas y procedimientos operacionales del proyecto.

!!! info "Docs as Code"
    Esta documentación sigue el principio **Docs as Code**: todo está versionado en Git, validado automáticamente por CI/CD y desplegado continuamente en GitHub Pages.

## 🗂️ Estructura de la Documentación

### 📊 Para Gerencia y Stakeholders
¿Eres gerente o stakeholder? Comienza aquí:
- **[📈 Resumen Ejecutivo](resumen-ejecutivo.md)**: Visión general del sistema sin tecnicismos
- **[🏗️ Arquitectura del Sistema (Vista C1)](c4model/index_c4model.md)**: Diagrama visual del contexto del sistema

---

### 📂 Proyecto
Información de alto nivel sobre el proyecto.
- **[Visión General](PROYECTO_COMPLETO.md)**: Descripción completa del alcance y objetivos.
- **[Estructura](ESTRUCTURA_PROYECTO.md)**: Organización del código y módulos.
- **[Bitácora](BITACORA.md)**: Registro histórico de cambios y decisiones.

### 📋 Decisiones (ADRs)
Registros de decisiones arquitectónicas importantes.
- **[Índice de ADRs](adrs/index_adrs.md)**: Todas las decisiones técnicas documentadas.
- **[Plantilla](adrs/template.md)**: Para crear nuevos ADRs.

### 🔧 Operaciones (Runbooks)
Procedimientos paso a paso para tareas operacionales.
- **[RB-001: Despliegue en Producción](runbooks/rb-001-deploy-prod.md)**
- **[RB-002: Gestión de Base de Datos](runbooks/rb-002-db-management.md)**
- **[RB-101: Conexión Odoo](runbooks/rb-101-odoo-connection.md)**
- **[RB-102: Envío de Correos](runbooks/rb-102-email-failure.md)**

### 🚀 Guías
Instrucciones para desplegar y utilizar el sistema.
- **[Inicio Rápido](INICIO_RAPIDO_COMPLETO.md)**: Guía paso a paso para levantar el entorno.
- **[Instrucciones](INSTRUCCIONES_INICIO_RAPIDO.md)**: Detalles operativos básicos.
- **[Contribuir](CONTRIBUTING.md)**: Cómo agregar o mejorar documentación.

### 🛠️ Técnico
Documentación específica para desarrolladores.
- **[Cambios Login](CAMBIOS_LOGIN.md)**: Detalles sobre la implementación de autenticación.
- **[Mejoras UI/UX](MEJORAS_UI_UX.md)**: Plan y registro de mejoras en la interfaz.

---

## 🤖 Automatización y Calidad

Cada cambio en la documentación pasa por:

- ✅ **Linting de Markdown**: Formato consistente.
- ✅ **Validación de Structurizr DSL**: Arquitectura válida.
- ✅ **Link Checker**: Sin enlaces rotos.
- ✅ **Referencias Cruzadas**: Trazabilidad garantizada entre ADRs, C4 y Runbooks.

El sitio se despliega automáticamente en GitHub Pages tras cada merge a `main`.

---

> **Para Contribuidores:** Lee la [Guía de Contribución](CONTRIBUTING.md) antes de editar la documentación.

