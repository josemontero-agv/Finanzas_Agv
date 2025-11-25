# Reporte de Estado de Proyectos y Requerimientos

!!! success "Para Gerencia de Sistemas y Jefatura"
    Este documento consolida la información completa de los proyectos en desarrollo para facilitar la toma de decisiones y seguimiento ejecutivo.

Este documento detalla:
- ✅ **Proyectos que estoy viendo**
- 📊 **Estado de los proyectos**
- 📝 **Historias de usuario**
- 👥 **Usuarios solicitantes**

---

## 📋 Índice de Navegación Rápida

- [1. Proyectos que Estoy Viendo](#1-proyectos-que-estoy-viendo)
- [2. Estado de los Proyectos](#2-estado-de-los-proyectos)
- [3. Historias de Usuario](#3-historias-de-usuario)
- [4. Usuarios Solicitantes](#4-usuarios-solicitantes)
- [5. Historial de Reuniones](#5-historial-de-reuniones)
- [6. Documentación Relacionada](#6-documentacion-relacionada)

---

## 1. Proyectos que Estoy Viendo

### 🎯 Resumen Ejecutivo de Áreas

| Área | Proyectos Activos | En Desarrollo | Pendientes | Completados |
| :--- | :---: | :---: | :---: | :---: |
| **Créditos y Cobranzas - Nacional** | 7 | 2 | 2 | 1 |
| **Créditos y Cobranzas - Internacional** | 2 | 0 | 2 | 0 |
| **Tesorería** | 4 | 0 | 3 | 1 |
| **TOTAL** | **13** | **2** | **7** | **2** |

### 📂 Listado Detallado por Área

#### Créditos y Cobranzas - Nacional
1. Hacer planilla de letras más rápida para envío al banco
2. Enviar correos de letras por recuperar
3. Enviar correos de letras en banco
4. Enviar estados de cuenta en PDF para los clientes
5. Reporte de cuenta 12
6. Reporte Nacional
7. Dashboard Nacional

#### Créditos y Cobranzas - Internacional
1. Reporte Internacional
2. Dashboard Internacional

#### Tesorería
1. Reporte de cuenta 42
2. Automatización de envío de comprobantes
3. Constancia de Detracción
4. Envío de comprobantes de manera masiva a los proveedores

---

## 2. Estado de los Proyectos

### Créditos y Cobranzas

#### Nacional

| Proyecto / Tarea | Estado | Detalle |
| :--- | :--- | :--- |
| **Hacer planilla de letras más rápida para envío al banco** | Pendiente | Diferente que enviar correos de letras del banco. Aún no realizado. |
| **Enviar correos de letras por recuperar** | 🟡 En desarrollo | |
| **Enviar correos de letras en banco** | 🟡 En desarrollo | |
| **Enviar estados de cuenta en PDF para los clientes** | 🔴 No iniciado | Aún no realizado. |
| **Reporte de cuenta 12** | 🟢 Realizado | Realizado pero falta revisión por gerencia. |
| **Reporte Nacional** | ⚪ Sin info | |
| **Dashboard Nacional** | ⚪ Sin info | |

#### Internacional

| Proyecto / Tarea | Estado | Detalle |
| :--- | :--- | :--- |
| **Reporte Internacional** | 🔴 No iniciado | Aún no. |
| **Dashboard Internacional** | 🔴 No iniciado | Aún no. |

### Tesorería

| Proyecto / Tarea | Estado | Detalle |
| :--- | :--- | :--- |
| **Reporte de cuenta 42** | 🟢 Realizado | Realizado pero falta revisar. |
| **Automatización de envío de comprobantes** | ⚪ Pendiente | |
| **Constancia de Detracción** | ⚪ Pendiente | |
| **Envío de comprobantes de manera masiva a los proveedores** | ⚪ Pendiente | |

---

## 3. Historias de Usuario

!!! info "Historias de Usuario Identificadas"
    Las siguientes historias de usuario fueron derivadas de las frustraciones y necesidades expresadas en las reuniones de levante de información (Octubre - Noviembre 2025).

### 📊 A. Reporte y Visualización (ODU y Externo)

| Tema | Problema o Frustración del Usuario | Necesidad Implícita (Historia de Usuario) |
| :--- | :--- | :--- |
| **Reportes en Tiempo Real** | Los reportes actuales se generan de forma manual y diaria, lo que consume tiempo y puede generar información desactualizada o incompleta (José Montero, Angie Gomero). | **Como usuario de Tesorería**, quiero un sistema de reportes en tiempo real que me permita filtrar la información por proveedor y banco, y ver saldos con/sin retención, para eliminar la necesidad de generar reportes manuales diarios. |
| **Reportería de Cuentas por Pagar** | La reportería de Cuentas por Pagar en ODU no es óptima y no permite la exportación de datos de manera específica y automatizada (Marilia Tinoco, Angie Gomero). Extrañan "query" de SAP. | **Como analista de Cuentas por Pagar**, quiero una mejora en la reportería que replique la funcionalidad de un "query" de SAP para facilitar la exportación de datos y obtener informes específicos y automatizados. |
| **Campos de Reporte Faltantes** | Los reportes de ODU carecen de campos críticos como el número de pedido por orden de compra y el estado de la factura ("rendido" o "no rendido") (Marilia Tinoco, Esperanza Alhuay). | **Como analista de Tesorería**, quiero que los reportes incluyan el número de pedido por orden de compra y el estado "rendido" o "no rendido" de la factura para tener una trazabilidad completa y precisa en mis análisis. |

### 🏦 B. Datos y Conciliación Bancaria

| Tema | Problema o Frustración del Usuario | Necesidad Implícita (Historia de Usuario) |
| :--- | :--- | :--- |
| **Conciliación Bancaria** | La conciliación automática en ODU a veces extrae información irrelevante y la falta de un número de operación bancaria dificulta la conciliación precisa (Angie Gomero). | **Como usuario de Tesorería**, quiero que la conciliación bancaria automática se realice utilizando el número de operación bancaria (o un número interno) para garantizar la precisión y eliminar información irrelevante. |
| **Datos Bancarios de Proveedores** | Los números de cuenta de proveedores en ODU a menudo están incompletos o incorrectos, requiriendo ingreso manual (José Montero, Esperanza Alhuay, Marilia Tinoco). | **Como Tesorería**, quiero un proceso que asegure que todos los proveedores activos tengan sus números de cuenta bancaria registrados correctamente en ODU para evitar la recolección manual. |
| **Datos Bancarios Internacionales** | ODU carece de campos para datos bancarios internacionales completos (Swift, dirección, etc.), forzando a buscar en proformas adjuntas (Esperanza Alhuay). | **Como usuario de Tesorería Internacional**, quiero campos en ODU para registrar los datos bancarios internacionales completos de los proveedores para que la información esté centralizada. |

### 📧 C. Automatización de Pagos

| Tema | Problema o Frustración del Usuario | Necesidad Implícita (Historia de Usuario) |
| :--- | :--- | :--- |
| **Comprobantes de Pago** | El sistema automático adjunta el recibo de pago de ODU, pero se necesita la constancia de pago del banco (Marilia Tinoco, Angie Gomero). | **Como usuario de Tesorería**, quiero que la automatización de correos adjunte la constancia de pago del banco en lugar del recibo de ODU, con opción para adjuntar masivamente. |
| **Referencia de Pago Incorrecta** | ODU a veces extrae el número de orden de compra en lugar del número de factura para la referencia de pago en correos, confundiendo a proveedores (Esperanza Alhuay). | **Como usuario de Tesorería**, quiero que el correo automático de pago muestre consistentemente el número de factura como referencia para asegurar una comunicación clara. |

---

## 4. Usuarios Solicitantes

!!! note "Stakeholders y Usuarios Finales"
    Personas que han solicitado funcionalidades y participado en el levante de información.

### 👥 Por Área de Negocio

#### Tesorería
| Usuario | Rol / Área | Solicitudes Principales |
| :--- | :--- | :--- |
| **Angie Gomero** | Tesorería | Reportes en tiempo real, conciliación bancaria automática, envío masivo de comprobantes |
| **Marilia Tinoco** | Tesorería / Cuentas por Pagar | Mejora de reportería (query SAP), automatización de correos, campos de reporte faltantes |
| **Esperanza Victoria Alhuay Perez** | Tesorería Internacional | Datos bancarios internacionales, referencia de factura correcta en pagos |
| **Melissa Román** | Tesorería | Gestión de números de cuenta de proveedores |

#### Gerencia y Aprobadores
| Usuario | Rol / Área | Participación |
| :--- | :--- | :--- |
| **Jancarlo Pariasca Cuba** | Gerencia Finanzas | Aprobación de proyectos, seguimiento de avances |
| **Kattya Barcena** | Finanzas | Validación de reportes de cuentas por pagar |
| **Teodoro Balarezo** | Jefe de Proyectos | Coordinación técnica y mapeo de procesos |
| **Andre Aliaga** | Sistemas / Análisis | Mapeo de flujos internacionales |

### 📊 Matriz de Necesidades por Usuario

| Usuario | Reportes | Automatización | Datos Bancarios | Conciliación |
| :--- | :---: | :---: | :---: | :---: |
| Angie Gomero | ✅ | ✅ | ✅ | ✅ |
| Marilia Tinoco | ✅ | ✅ | ✅ | - |
| Esperanza Alhuay | ✅ | ✅ | ✅ (Internac.) | - |
| Melissa Román | - | - | ✅ | - |

---

## 5. Historial de Reuniones Relevantes

### 📅 Cronología de Levante de Información

| Fecha | Tema | Participantes | Resultados Clave |
| :--- | :--- | :--- | :--- |
| **13 Oct 2025** | Levante de Información y Procesos - Tesorería | Angie Gomero, Marilia Tinoco, Esperanza Alhuay, José Montero, Melissa Román | Identificación de 8 problemas críticos en reportería y conciliación |
| **21 Oct 2025** | Análisis de procesos - Tesorería - Internacional | Melissa Román, Angie Gomero, Teodoro Balarezo, Marilia Tinoco, Andre Aliaga, Esperanza Alhuay, José Montero | Mapeo del flujo internacional, identificación de mejoras en ODU para bancos internacionales |
| **14 Nov 2025** | PROYECTO FINANZAS-CTA 12 Y 42-AVANCE | Jancarlo Pariasca, Marilia Tinoco, Kattya Barcena, José Montero | Presentación de avances, aprobación de suscripción IA, compromiso de entrega para viernes siguiente |

### 🎯 Temas Discutidos

1. **Reportería en Tiempo Real** (Oct 13, Nov 14)
2. **Números de Cuenta Bancaria de Proveedores** (Oct 13, Oct 21, Nov 14)
3. **Automatización de Envío de Comprobantes** (Oct 13)
4. **Mejoras en Conciliación Bancaria** (Oct 13)
5. **Campos Bancarios Internacionales en ODU** (Oct 21)
6. **Problema de Referencia de Factura vs Orden de Compra** (Oct 21)
7. **Estado "Rendido/No Rendido" en Reportes** (Oct 13)
8. **Cortes por Fecha en Reportes** (Nov 14)

---

## 6. Documentación Relacionada

### 📚 Contexto Arquitectónico y Técnico

- **[Vista C4 - Arquitectura del Sistema](c4model/index_c4model.md)** - Diagrama de contexto para entender las integraciones (Odoo, correos, SUNAT)
- **[Resumen Ejecutivo](resumen-ejecutivo.md)** - Visión general del proyecto para stakeholders
- **[Estructura del Proyecto](ESTRUCTURA_PROYECTO.md)** - Organización del código y módulos

### 🔧 Decisiones Arquitectónicas (ADRs)

| ID | Decisión | Relación con Proyectos |
| :--- | :--- | :--- |
| [ADR-001](adrs/0001-uso-mkdocs.md) | Uso de MkDocs para documentación | Base para esta documentación viva |
| *ADR-002* (Pendiente) | Plataforma externa para reportería (vs. desarrollo en ODU) | Relacionado con Reportes de Cta 12 y 42 |
| *ADR-003* (Pendiente) | Estrategia de envío masivo de correos | Relacionado con automatización de comprobantes |

### 🛠️ Runbooks Operacionales

| ID | Runbook | Aplicación |
| :--- | :--- | :--- |
| [RB-001](runbooks/rb-001-deploy-prod.md) | Despliegue en Producción | Proceso para liberar reportes de Cta 12 y 42 |
| [RB-002](runbooks/rb-002-db-management.md) | Gestión de Base de Datos | Backup antes de migraciones masivas de datos bancarios |
| [RB-101](runbooks/rb-101-odoo-connection.md) | Conexión Odoo | Troubleshooting de integración con ERP |
| [RB-102](runbooks/rb-102-email-failure.md) | Fallas en Envío de Correos | Relacionado con envío automático de comprobantes |

### 📊 Análisis y Mejoras

- **[Análisis Arquitectónico Completo](mejoras-stack-arquitectura/analisis-arquitectonico-completo.md)** - Recomendaciones de stack tecnológico
- **[Plan de Corrección de Performance](arquitectura/plan-correccion-performance.md)** - Optimización de consultas a Odoo
- **[Bitácora del Proyecto](BITACORA.md)** - Historial detallado de cambios y decisiones

---

## 📞 Contacto y Soporte

**Responsable del Proyecto:** José Montero  
**Jefe de Proyectos:** Teodoro Balarezo  
**Aprobador:** Jancarlo Pariasca Cuba (Gerencia Finanzas)

---

**Última Actualización:** 25 de Noviembre de 2025