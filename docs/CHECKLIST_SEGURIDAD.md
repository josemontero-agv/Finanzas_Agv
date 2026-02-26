# Checklist de Seguridad - Finanzas AGV

Estándar de revisión para garantizar que la aplicación cumpla requisitos mínimos de seguridad antes de despliegue y en auditorías (jefatura de proyectos, QA).

---

## 1. Autenticación y control de acceso

| #   | Revisión | Estado |
| --- | -------- | ------ |
| 1.1 | **Backend**: Todas las rutas de negocio (letras, cobranzas, exportaciones) exigen sesión con `@require_login`; sin sesión devuelven 401. | ☐ |
| 1.2 | **Guard central en frontend**: Una sola capa (ej. AppShell) valida sesión antes de mostrar Sidebar o contenido; las páginas protegidas no se renderizan hasta que la sesión sea válida. | ☐ |
| 1.3 | **Sin destello de contenido**: Al ir por URL a una ruta protegida sin sesión no se muestra ni un instante el contenido (ni Sidebar ni datos); solo pantalla de “Validando sesión…” y luego redirección a login. | ☐ |
| 1.4 | **Cerrar sesión en toda la app**: El botón “Cerrar sesión” está en un componente compartido (Sidebar/layout), visible en todos los módulos. | ☐ |
| 1.5 | **Ruta raíz**: `/` redirige a `/login` (o a una pantalla que exige autenticación). | ☐ |
| 1.6 | **APIs sensibles**: Export (Excel, PDF) y reportes usan el mismo mecanismo de autenticación que el resto de la API. | ☐ |

---

## 2. URLs y rutas

| #   | Revisión | Estado |
| --- | -------- | ------ |
| 2.1 | **Rutas de desarrollo en producción**: Módulos o URLs solo de desarrollo están deshabilitados o devuelven 403 en producción (ej. `RESTRICT_TO_LETTERS_ONLY` o lista de prefijos permitidos). | ☐ |
| 2.2 | **URL directa sin sesión**: Acceder a una URL protegida (ej. `/letters`, `/collections`) sin sesión termina en redirección a login sin mostrar datos ni layout protegido. | ☐ |
| 2.3 | **Solo health público**: Únicamente endpoints explícitamente públicos (ej. `/api/health`) son accesibles sin autenticación. | ☐ |

---

## 3. Sesión y cookies

| #   | Revisión | Estado |
| --- | -------- | ------ |
| 3.1 | **Cookie de sesión**: Nombre específico (ej. `finanzas_agv_session`), no el valor por defecto de Flask. | ☐ |
| 3.2 | **Producción**: `SESSION_COOKIE_SECURE=True` y `SameSite` adecuado al dominio (ej. `None` si el frontend está en otro origen). | ☐ |
| 3.3 | **Cierre de sesión**: El logout limpia la sesión en backend (`session.clear()`) y el frontend redirige a `/login`. | ☐ |

---

## 4. Secretos y configuración

| #   | Revisión | Estado |
| --- | -------- | ------ |
| 4.1 | **`.env` en `.gitignore`**: Archivos con credenciales (`.env`, `.env.desarrollo`, `.env.produccion`) no se suben al repositorio. | ☐ |
| 4.2 | **Sin secretos en código**: No hay contraseñas, API keys ni tokens hardcodeados en el código fuente. | ☐ |
| 4.3 | **Variables de entorno**: Uso de `os.getenv()` o equivalente para Odoo, Supabase, mail, etc. | ☐ |

---

## 5. API y datos

| #   | Revisión | Estado |
| --- | -------- | ------ |
| 5.1 | **401 cuando no hay sesión**: Los endpoints protegidos devuelven 401 (y mensaje claro) si no hay sesión válida. | ☐ |
| 5.2 | **Interceptor 401 en frontend**: Las peticiones al backend que devuelven 401 (salvo la de login) disparan redirección a `/login` de forma centralizada (ej. interceptor de Axios) para manejar sesión expirada. | ☐ |
| 5.3 | **CORS**: Origen permitido configurado según entorno (URL del frontend en producción). | ☐ |
| 5.4 | **Errores en producción**: No se exponen stack traces ni rutas internas al usuario; los logs sí pueden tener detalle. | ☐ |

---

## 6. Módulos y blueprints

| #   | Revisión | Estado |
| --- | -------- | ------ |
| 6.1 | **Inventario de rutas**: Existe lista de blueprints y rutas; cada ruta de negocio está marcada como protegida o pública. | ☐ |
| 6.2 | **Nuevos módulos**: Al agregar un blueprint (treasury, detractions, etc.) se aplica `@require_login` por defecto y se documentan excepciones. | ☐ |

---

## Uso del checklist

- **Antes de ir a producción**: Completar todas las casillas y corregir los ítems no cumplidos.
- **En reuniones de seguridad/QA**: Usar como referencia para demostrar qué se revisa y qué está cubierto.
- **Después de agregar funcionalidad**: Revisar al menos las secciones 1 y 6.

---

## Referencia rápida en este proyecto

- **Backend – Auth**: `app/auth/security.py` — decorador `require_login`. Letras, Cobranzas y Exports usan `@require_login` en todas sus rutas sensibles.
- **Frontend – Guard central**: `components/app-shell.tsx` — valida sesión con `authApi.getUserInfo()` antes de renderizar Sidebar y contenido; sin sesión solo se muestra “Validando sesión…” y se redirige a `/login`. No hay destello de contenido protegido.
- **Frontend – 401 global**: `lib/api.ts` — interceptor de `flaskApi` que ante respuesta 401 (excepto a `auth/login`) hace `window.location.replace('/login')`.
- **Cerrar sesión**: Sidebar incluye el botón “Cerrar sesión” (visible en Letras y Cobranzas).
