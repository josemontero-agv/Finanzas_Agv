# Análisis de Arquitectura e Ingeniería de Datos (Enfoque CAP)

**Fecha:** 05 de Diciembre, 2024
**Proyecto:** Finanzas AGV
**Marco Teórico:** Teorema CAP (Brewer)

## 1. Análisis Teórico: El Teorema CAP en Finanzas AGV

El sistema se compone de dos nodos principales conectados por una red (XML-RPC):
1.  **Nodo A:** Aplicación Flask (Reportes/Frontend).
2.  **Nodo B:** ERP Odoo (Fuente de Datos).

### 1.1 Estado Actual: Intento Fallido de CA
Actualmente, el sistema opera con un acoplamiento síncrono.
*   **Consistencia (C):** Alta. Cada vez que se carga la página, se ven los datos "en vivo" de Odoo.
*   **Disponibilidad (A):** Baja/Condicional. Si Odoo tarda 30 segundos en responder un `search_read`, la App Flask se bloquea (Timeout).
*   **Tolerancia a Partición (P):** Nula. Si la conexión a Odoo cae, el reporte no se puede generar.

> **Conclusión:** Al priorizar la Consistencia absoluta sin Tolerancia a Particiones, estamos sacrificando gravemente la Disponibilidad y la experiencia de usuario.

### 1.2 Estado Deseado: Modelo AP (Disponibilidad + Tolerancia a Partición)
Para una herramienta de Business Intelligence (BI) y Reportes, el objetivo debe ser **AP**.
*   **Disponibilidad (A):** El reporte debe cargar en < 1 segundo, independientemente del estado de Odoo.
*   **Tolerancia a Partición (P):** Si el enlace con Odoo se rompe, la aplicación debe seguir funcionando con la última data conocida.
*   **Sacrificio -> Consistencia Eventual:** Aceptamos que los datos pueden tener un retraso ("lag") de X minutos respecto al tiempo real, lo cual es estándar en ingeniería de datos para analítica (OLAP).

---

## 2. Estrategia de Implementación: De OLTP a OLAP con Supabase

Para lograr un sistema **AP**, necesitamos introducir un **almacén intermedio (ODS - Operational Data Store)** que actúe como buffer. En este caso, utilizaremos **Supabase** (PostgreSQL gestionado) para aprovechar su escalabilidad y facilidad de uso.

### 2.1 Arquitectura Propuesta

```mermaid
graph LR
    subgraph Source [Sistema OLTP - Consistencia]
        Odoo[(ERP Odoo)]
    end

    subgraph Pipeline [Capa de Ingeniería de Datos - Tolerancia P]
        ETL[Worker ETL / Celery]
    end

    subgraph Target [Sistema OLAP - Disponibilidad]
        Supabase[(Supabase PostgreSQL)]
        Redis[(Caché Rápida)]
        App[Flask App]
    end

    Odoo -->|Sync Asíncrono (Eventual)| ETL
    ETL -->|Write| Supabase
    Supabase -->|Read Fast| App
```

### 2.2 Componentes Clave

#### A. Almacenamiento Cloud (Supabase)
*   **Tecnología:** Supabase (PostgreSQL).
*   **Función:** Almacena una copia sincronizada de las tablas `account.move`, `res.partner`, etc.
*   **Justificación CAP:** Permite que Flask consulte datos a alta velocidad (Disponibilidad total) desacoplándose de la carga operativa de Odoo. Al estar en la nube, facilita el acceso desde cualquier despliegue.

#### B. Capa ETL (El Mecanismo de Consistencia Eventual)
*   **Tecnología:** Celery + Pandas.
*   **Estrategia:**
    1.  **Snapshot Inicial:** Descarga completa de datos históricos hacia Supabase.
    2.  **Incremental Sync:** Tarea programada que busca registros en Odoo donde `write_date > ultimo_sync` y actualiza Supabase.
*   **Justificación:** Desacopla la lectura de la escritura. Transforma los datos crudos de Odoo en tablas optimizadas para reportes.

#### C. Caché de Alta Velocidad (Redis)
*   **Tecnología:** Redis.
*   **Función:** Almacenar resultados de querys costosos o sesiones de usuario, y actuar como Broker para Celery.
*   **Justificación:** Reduce la latencia al mínimo para datos calientes.

---

## 3. Hoja de Ruta Técnica

### Fase 1: Infraestructura Base y Asincronía
1.  **Integración Redis & Celery:** Configurar el broker de mensajes.
2.  **Conexión Supabase:** Configurar cliente (`supabase-py` o `SQLAlchemy`) en Flask.
3.  **Background Tasks:** Mover procesos pesados (Excel, Emails) a Celery.

### Fase 2: Pipeline ETL
1.  **Esquema en Supabase:** Definir tablas espejo de Odoo (`raw_invoices`, `raw_partners`).
2.  **Script de Sincronización:** Crear tareas de Celery que extraigan de Odoo y carguen en Supabase (Upsert).
3.  **Switch de Lectura:** Modificar `TreasuryService` para leer de Supabase en lugar de Odoo.

---

## 4. Conclusión

Esta arquitectura **AP** soportada por **Supabase** transforma la aplicación de un simple "visor de Odoo" a una plataforma de **Finanzas y Datos** robusta, capaz de escalar y ofrecer tiempos de respuesta inmediatos sin estresar el ERP principal.
