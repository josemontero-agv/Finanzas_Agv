# 🐳 Guía Completa: Instalación de Docker y Ejecución del Proyecto

Esta guía te llevará paso a paso para instalar Docker en Windows, arrancar tu aplicación con todos los servicios (incluyendo Redis y Celery) y verificar que todo funcione.

---

## 🛠️ Paso 1: Instalar Docker Desktop en Windows

Docker te permitirá correr Redis, tu Base de Datos y tu Aplicación sin instalar nada complicado directamente en tu Windows.

1.  **Descargar:** Ve a [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) y descarga el instalador para Windows.
2.  **Instalar:** Ejecuta el archivo descargado (`Docker Desktop Installer.exe`).
    *   Asegúrate de marcar la opción **"Use WSL 2 instead of Hyper-V"** (recomendado).
3.  **Reiniciar:** Es probable que te pida reiniciar tu computadora. Hazlo.
4.  **Verificar:** Al reiniciar, abre Docker Desktop. Si te pide instalar el kernel de Linux WSL2, sigue el enlace que te da o [descárgalo aquí](https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi).
5.  **Listo:** Cuando veas la ventana de Docker con el estado en **verde (Engine running)** en la esquina inferior izquierda, ya tienes Docker listo.

---

## 🚀 Paso 2: Arrancar el Proyecto (La Magia)

Ya he configurado todo por ti. He creado un archivo llamado `docker-compose.yml` que le dice a Docker exactamente qué descargar y cómo conectar todo.

Solo tienes que abrir tu terminal (PowerShell) en la carpeta del proyecto y ejecutar **un solo comando**:

```powershell
docker-compose up --build
```

### ¿Qué hace este comando?
1.  **Descarga Redis:** No tienes que instalarlo manual. Docker baja la versión correcta.
2.  **Construye tu App:** Lee el archivo `Dockerfile`, instala Python y tus librerías.
3.  **Levanta 3 Servicios:**
    *   `web`: Tu aplicación Flask (en puerto 5000).
    *   `redis`: El cerebro de la mensajería.
    *   `worker`: El obrero de Celery que hará los ETLs.

Verás muchas letras pasando en la consola. Espera a que veas mensajes diciendo que el servidor está corriendo.

---

## ✅ Paso 3: Verificar que todo funciona

### 1. Ver la Web App
Abre tu navegador y entra a: [http://localhost:5000](http://localhost:5000)
Deberías ver la respuesta JSON de tu API o la pantalla de login si vas a `/login`.

### 2. Verificar Redis
No necesitas "abrir" Redis. Si el comando anterior no dio error, Redis ya está funcionando en segundo plano dentro de Docker. La aplicación se conecta a él automáticamente a través de la red interna de Docker.

### 3. Verificar Celery Worker
En la consola donde corriste el comando, busca líneas que digan `celery@... ready`. Eso significa que el worker está listo para recibir tareas.

---

## 🔄 Comandos Útiles para el Día a Día

| Acción | Comando |
| :--- | :--- |
| **Arrancar todo** | `docker-compose up` |
| **Arrancar en segundo plano** (para seguir usando la terminal) | `docker-compose up -d` |
| **Ver logs** (si lo corriste en segundo plano) | `docker-compose logs -f` |
| **Detener todo** | `docker-compose down` |
| **Reconstruir** (si instalaste nuevas librerías) | `docker-compose up --build` |

---

## 📂 Archivos que he creado para ti

No necesitas tocar nada, pero es bueno que sepas qué hice:
*   **`Dockerfile`**: Las instrucciones para crear el entorno Python.
*   **`docker-compose.yml`**: El mapa de arquitectura (Redis + Web + Worker).
*   **`app/tasks.py`**: El puente entre Celery y tus scripts ETL.

¡Listo! Con esto ya tienes un entorno de Ingeniería de Datos profesional corriendo en tu máquina local.

