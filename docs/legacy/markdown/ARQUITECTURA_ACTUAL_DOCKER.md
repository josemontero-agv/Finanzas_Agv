# 🏗️ Arquitectura del Proyecto (Docker + Celery + ETL)

**Estado:** Implementado
**Fecha de Actualización:** 05 de Diciembre 2024

## 1. Visión General

El proyecto ha evolucionado a una **Arquitectura Orientada a Servicios** orquestada mediante Docker. Esto permite desacoplar la aplicación web de los procesos pesados de sincronización de datos, garantizando alta disponibilidad y consistencia eventual.

### Diagrama de Componentes

```mermaid
graph TD
    User[Usuario / Navegador] -->|HTTP/80| Nginx[Gunicorn (Web Container)]
    
    subgraph Docker Host
        direction TB
        
        subgraph Servicios Web
            Nginx -->|Flask App| App[Aplicación Flask]
        end
        
        subgraph Servicios de Datos
            Redis[(Redis Cache & Broker)]
        end
        
        subgraph Servicios Background
            Worker[Celery Worker]
            Beat[Celery Beat (Scheduler)]
        end
    end
    
    subgraph Fuentes Externas
        Odoo[(ERP Odoo)]
        Supabase[(Supabase PostgreSQL)]
    end

    %% Flujos
    App -->|Lee/Escribe| Redis
    App -->|Consulta| Supabase
    App -->|Consulta (Legacy)| Odoo
    
    Worker -->|Escucha Tareas| Redis
    Worker -->|ETL: Extrae| Odoo
    Worker -->|ETL: Carga| Supabase
    
    Beat -->|Programa Tareas| Redis
```

---

## 2. Servicios (Contenedores)

La infraestructura se define en `docker-compose.yml` y consta de los siguientes servicios:

### A. Web (`web`)
*   **Función:** Servidor HTTP principal.
*   **Tecnología:** Flask ejecutado sobre Gunicorn.
*   **Puerto:** 5000 (Host).
*   **Responsabilidad:**
    *   Servir interfaz de usuario (HTML/Jinja2).
    *   Exponer API REST.
    *   Autenticación y autorización.
    *   Encolar tareas pesadas hacia Redis.

### B. Worker (`worker`)
*   **Función:** Procesamiento de tareas en segundo plano.
*   **Tecnología:** Celery.
*   **Responsabilidad:**
    *   Ejecutar ETLs (`etl_sync_threading.py`).
    *   Sincronización masiva Odoo -> Supabase.
    *   Generación de reportes pesados (Excel).
    *   Envío de correos masivos.

### C. Broker & Cache (`redis`)
*   **Función:** Intermediario de mensajes y caché en memoria.
*   **Tecnología:** Redis 7 (Alpine).
*   **Responsabilidad:**
    *   **Broker:** Recibe tareas de `web` y las entrega a `worker`.
    *   **Backend:** Almacena el estado/resultado de las tareas.
    *   **Cache:** Almacena respuestas de API frecuentes (Flask-Caching).

---

## 3. Flujo de Datos: Estrategia AP (Available & Partition-tolerant)

El sistema implementa una estrategia para maximizar la disponibilidad:

1.  **Lectura Rápida (App):** La aplicación web lee datos pre-procesados desde **Supabase** (PostgreSQL optimizado para lectura) o Caché. Esto evita esperar los tiempos de respuesta de Odoo.
2.  **Escritura Asíncrona (ETL):** 
    *   Celery Worker ejecuta scripts de extracción periódicos.
    *   Se conecta a Odoo vía XML-RPC.
    *   Transforma los datos.
    *   Realiza `UPSERT` (Insertar o Actualizar) en Supabase.

---

## 4. Estructura de Archivos Clave

```
Finanzas_Agv/
├── Dockerfile              # Definición de imagen para Web y Worker
├── docker-compose.yml      # Orquestación de servicios
├── app/
│   ├── tasks.py            # Definición de Tareas Celery (ETLs)
│   ├── __init__.py         # Registro de Celery y Blueprints
│   └── core/
│       └── celery_utils.py # Configuración base de Celery
├── scripts/
│   └── etl/
│       └── etl_sync_threading.py # Lógica pura del ETL
└── config.py               # Configuración de entornos (Redis, Odoo, DB)
```

## 5. Comandos Operativos

### Iniciar Infraestructura
```bash
docker-compose up --build
```

### Ver Logs
```bash
docker-compose logs -f
```

### Entrar al contenedor Web
```bash
docker-compose exec web bash
```

### Forzar ejecución de ETL manual (desde Python shell en contenedor)
```python
from app.tasks import task_run_etl_sync
task_run_etl_sync.delay()
```

