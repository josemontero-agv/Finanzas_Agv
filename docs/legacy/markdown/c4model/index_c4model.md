# 🏗️ Arquitectura del Sistema (Vista C4)

!!! success "Para Gerencia y Stakeholders"
    Esta página presenta la arquitectura del sistema usando **lenguaje no técnico**. No necesitas conocimientos de programación para entenderla.

---

## 📖 ¿Qué es el Modelo C4?

El modelo C4 es una forma visual de explicar cómo está construido un sistema de software. Tiene 4 niveles de detalle (de mayor a menor abstracción):

1. **Contexto (C1)** ← *Estás aquí* - Vista panorámica para ejecutivos
2. **Contenedores (C2)** - Tecnologías principales (para arquitectos)
3. **Componentes (C3)** - Módulos internos (para desarrolladores)
4. **Código (C4)** - Clases y métodos (para programadores)

---

## 🌍 Nivel 1: Vista de Contexto (C1)

### ¿Qué muestra este diagrama?

- **Personas:** Quiénes usan el sistema
- **Sistema Central:** Nuestra aplicación Finanzas AGV
- **Sistemas Externos:** Otras plataformas con las que nos conectamos
- **Relaciones:** Cómo fluye la información entre ellos

### Diagrama de Contexto

!!! info "Ideal para No Técnicos"
    Este diagrama es perfecto para presentaciones ejecutivas, ya que muestra **QUÉ** hace el sistema sin explicar **CÓMO** lo hace internamente.

```structurizr
workspace "Finanzas AGV" "Sistema de gestión financiera y cobranzas." {

    model {
        user = person "Usuario Financiero" "Personal de finanzas, cobranzas y tesorería."
        admin = person "Administrador" "Administrador del sistema y TI."

        enterprise "Agrovet Market" {
            financeSystem = softwareSystem "Sistema Finanzas AGV" "Permite la gestión de cobranzas, tesorería, detracciones y reportes." {
                description "Sistema central de finanzas que integra datos de ERP y facilita la toma de decisiones."
            }

            erp = softwareSystem "ERP Odoo" "Sistema ERP central de la empresa." "External System"
            emailSystem = softwareSystem "Servidor de Correo" "Envía notificaciones y estados de cuenta." "External System"
            sunat = softwareSystem "SUNAT / OSE" "Plataforma de facturación electrónica y validación." "External System"
        }

        # Relaciones
        user -> financeSystem "Visualiza reportes, gestiona cobranzas y tesorería"
        admin -> financeSystem "Configura usuarios y parámetros"
        
        financeSystem -> erp "Extrae facturas, pagos y clientes" "XML-RPC (actual) / PostgreSQL (recomendado)"
        financeSystem -> emailSystem "Envía correos a clientes" "SMTP"
        financeSystem -> sunat "Consulta validez de comprobantes" "API"
    }

    views {
        systemContext financeSystem "Contexto" {
            include *
            autoLayout
        }
        
        styles {
            element "Software System" {
                background #714B67
                color #ffffff
            }
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "External System" {
                background #999999
                color #ffffff
            }
        }
    }
}
```

---

## 📊 Descripción de Elementos (en Lenguaje Simple)

| Elemento | ¿Qué hace? | ¿Por qué es importante? |
| :--- | :--- | :--- |
| **👤 Usuario Financiero** | Accede al sistema para consultar cuentas, generar reportes y gestionar cobranzas | Son los usuarios finales que toman decisiones financieras |
| **👨‍💼 Administrador** | Configura permisos, usuarios y parámetros del sistema | Garantiza seguridad y buen funcionamiento |
| **💼 Sistema Finanzas AGV** | Centraliza información financiera y ofrece dashboards en tiempo real | Reemplaza procesos manuales y hojas de cálculo dispersas |
| **🏢 ERP Odoo** | Sistema principal de la empresa que tiene facturas, pagos y datos maestros | Es la "fuente de verdad" de donde obtenemos los datos |
| **📧 Servidor de Correo** | Envía automáticamente estados de cuenta y recordatorios a clientes | Automatiza comunicación que antes se hacía manualmente |
| **🏛️ SUNAT** | Plataforma gubernamental para validar documentos tributarios | Asegura cumplimiento legal y evita sanciones |

---

## 🔄 Flujo de Información (Ejemplo Práctico)

### Caso de Uso: Consultar Facturas Vencidas

1. **Usuario Financiero** ingresa al sistema Finanzas AGV
2. El sistema **consulta al ERP Odoo** todas las facturas pendientes
3. El sistema **calcula automáticamente** cuáles están vencidas (por días)
4. El usuario **visualiza el reporte** filtrado por antigüedad
5. Opcionalmente, el sistema **envía correos** automáticos a clientes morosos vía Servidor de Correo
6. Si es necesario, el sistema **valida con SUNAT** que los comprobantes sean legítimos

---

## 🎯 Beneficios de Esta Vista

### Para Gerencia:
- ✅ Entender alcance del sistema sin detalles técnicos
- ✅ Identificar dependencias con otros sistemas (Odoo, SUNAT)
- ✅ Justificar inversiones en integraciones

### Para Stakeholders:
- ✅ Visualizar rápidamente "quién hace qué"
- ✅ Comprender riesgos (si Odoo falla, Finanzas AGV no funciona)
- ✅ Validar que el sistema cumple las necesidades del negocio

### Para TI:
- ✅ Comunicar arquitectura a áreas no técnicas
- ✅ Identificar puntos de integración para mantenimiento
- ✅ Planificar contingencias ante fallas de sistemas externos

---

## 📚 Siguientes Niveles (Para Personal Técnico)

Si necesitas más detalles sobre la implementación:

- **Nivel 2 (Contenedores):** Tecnologías usadas (Python, Flask, React, etc.)
- **Nivel 3 (Componentes):** Módulos internos (servicios, rutas, modelos)
- **Nivel 4 (Código):** Clases y funciones específicas

> **Nota:** Los niveles 2-4 están documentados en secciones técnicas y requieren conocimiento de programación.

---

## 🔄 Arquitectura Futura (Recomendada)

### Mejoras Propuestas

El análisis arquitectónico recomienda las siguientes mejoras:

1. **Base de Datos Local (PostgreSQL Read Replica)**
   - Consultas 50-100x más rápidas que XML-RPC
   - Índices personalizados para reportes
   - Escalabilidad horizontal

2. **Celery + Redis**
   - Tareas asíncronas (ETL, exportaciones)
   - Reportes programados
   - Mejor experiencia de usuario

3. **Mantener Monolito Modular**
   - Estructura actual es suficiente
   - Fácil migrar a microservicios después si es necesario

> **Ver:** [Análisis Arquitectónico Completo](../mejoras-stack-arquitectura/analisis-arquitectonico-completo.md) para detalles técnicos.

---

## 🔗 Referencias

- [Resumen Ejecutivo](../resumen-ejecutivo.md) - Visión general sin diagramas
- [Documentación Completa](../PROYECTO_COMPLETO.md) - Detalles técnicos del proyecto
- [Análisis Arquitectónico](../mejoras-stack-arquitectura/analisis-arquitectonico-completo.md) - Recomendaciones de stack y mejoras
- [Structurizr DSL](workspace.dsl) - Código fuente del diagrama (para desarrolladores)
- [C4 Letras](letras.md) - Vistas y hallazgos específicos del módulo de Letras

