# ✅ CHECKLIST DE REMEDIACIÓN - FINANZAS AGV
## Plan de Implementación para Development Team

**Versión:** 2.0 (Actualización Mensual)  
**Fecha original:** 26 Mayo 2026  
**Fecha actualización:** 25 Junio 2026  
**Estado general:** 🔴 CRÍTICO — 0/6 items críticos completados tras 30 días  
**Próxima revisión:** 25 Julio 2026

---

## 📊 Estado de Implementación — Resumen Ejecutivo

| Categoría | Items | Completados | Pendientes | Estado |
|-----------|-------|-------------|------------|--------|
| 🔴 CRÍTICOS | 6 | 0 | 6 | ❌ Sin avance |
| 🔴 ALTOS | 6 | 0 | 6 | ❌ Sin avance |
| 🟡 MEDIOS | 8 | 0 | 8 | ❌ Sin avance |
| 🟢 BAJOS | 5 | 0 | 5 | ❌ Sin avance |
| ✅ MEJORAS ARQUITECTÓNICAS | 6 | 6 | 0 | ✅ Completado |
| 🚨 NUEVOS (Junio 2026) | 4 | 0 | 4 | ❌ Pendiente |
| **TOTAL SEGURIDAD** | **25** | **0** | **25** | **0% completado** |

---

## 🔴 SEMANA 1: VULNERABILIDADES CRÍTICAS (30+ DÍAS PENDIENTES)

### ❌ TASK 1.0: NUEVO — Eliminar Auth Bypass en OdooRepository
**Prioridad:** 🔴 CRÍTICA (Introducida en Junio 2026)  
**Esfuerzo:** 30 minutos  
**Responsable:** Backend Developer  
**Status:** ❌ Pendiente (nueva vulnerabilidad detectada en auditoría Junio)

**Problema detectado:**
El método `authenticate_user()` en `app/core/odoo.py` tiene un fallback inseguro que permite autenticarse con las credenciales del servicio si Odoo no está disponible.

**Checklist:**
- [ ] Abrir `app/core/odoo.py`
- [ ] Localizar `authenticate_user()` — línea ~118
- [ ] Eliminar el bloque `except` que hace fallback con `self.username/self.password`
- [ ] Reemplazar con fail-safe (retornar `False` si Odoo no disponible)
- [ ] Añadir logging estructurado en lugar de `print()`

```python
# CÓDIGO A REEMPLAZAR (app/core/odoo.py:L145-150)
# ELIMINAR ESTO:
except Exception as exc:
    print(f"[ERROR] Error en autenticación contra Odoo: {exc}")
    if username == self.username and password == self.password:
        print("[OK] Autenticación exitosa usando credenciales del repositorio")
        return True
    return False

# REEMPLAZAR CON:
except Exception as exc:
    import logging
    logger = logging.getLogger(__name__)
    logger.error("Error de conexión a Odoo durante autenticación: tipo=%s", type(exc).__name__)
    return False  # fail-safe: sin autenticación si Odoo no disponible
```

---

### ❌ TASK 1.1: Implementar JWT Real (Token Validation)
**Prioridad:** 🔴 CRÍTICA  
**Esfuerzo:** 4 horas  
**Responsable:** Backend Lead  
**Status:** ❌ Sin iniciar — **MÁS DE 30 DÍAS PENDIENTE**

**Evidencia de no resolución:** `app/auth/routes.py:L96` — `'token': 'dummy_token_12345'` sin cambios.

**Checklist:**
- [ ] Instalar Flask-JWT-Extended
  ```bash
  pip install Flask-JWT-Extended==4.7.1
  # Anclar en requirements.txt como: Flask-JWT-Extended==4.7.1
  ```
- [ ] Configurar JWT en `app/__init__.py`
  ```python
  from flask_jwt_extended import JWTManager
  jwt = JWTManager()
  app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
  app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
  jwt.init_app(app)
  ```
- [ ] Actualizar `app/auth/routes.py` — endpoint `/login`
  - [ ] Consultar grupos/roles del usuario en Odoo durante el login
  - [ ] Generar `access_token = create_access_token(identity=username, additional_claims={'email': user_email, 'roles': roles})`
  - [ ] Devolver `access_token` en lugar de `'dummy_token_12345'`
- [ ] Actualizar `app/auth/security.py`
  - [ ] Reemplazar `require_login` con `@jwt_required()` de Flask-JWT-Extended
  - [ ] Crear `get_current_user()` wrapper
- [ ] Actualizar todos los endpoints que usan `@require_login`
- [ ] Probar con pytest

---

### ❌ TASK 1.2: DEBUG=False en Producción
**Prioridad:** 🔴 CRÍTICA  
**Esfuerzo:** 15 minutos  
**Responsable:** Backend Developer (cualquiera)  
**Status:** ❌ Sin iniciar — **MÁS DE 30 DÍAS PENDIENTE**

**Checklist:**
- [ ] Editar `config.py:L188`
  ```python
  class ProductionConfig(Config):
      DEBUG = False  # ← cambiar de True a False
  ```
- [ ] Editar `run.py:L66`
  ```python
  elif environment == 'production':
      app.run(host='0.0.0.0', port=5000, debug=False)  # ← False
  ```
- [ ] Verificar con `python run.py production` que NO muestra el debugger de Werkzeug

---

### ❌ TASK 1.3: Implementar Rate Limiting en /login
**Prioridad:** 🔴 ALTA  
**Esfuerzo:** 1 hora  
**Responsable:** Backend Developer  
**Status:** ❌ Sin iniciar — **MÁS DE 30 DÍAS PENDIENTE**

**Checklist:**
- [ ] Instalar Flask-Limiter
  ```bash
  pip install Flask-Limiter==3.9.0
  ```
- [ ] Configurar en `app/__init__.py`
  ```python
  from flask_limiter import Limiter
  from flask_limiter.util import get_remote_address
  limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["500/day"])
  ```
- [ ] Aplicar límite en `app/auth/routes.py`
  ```python
  from app import limiter
  
  @auth_bp.route('/login', methods=['POST'])
  @limiter.limit("10/minute;50/hour")
  def login(): ...
  ```
- [ ] Añadir respuesta 429 apropiada en el error handler

---

### ❌ TASK 1.4: Security Headers (after_request)
**Prioridad:** 🔴 ALTA  
**Esfuerzo:** 1 hora  
**Responsable:** Backend Developer  
**Status:** ❌ Sin iniciar — **MÁS DE 30 DÍAS PENDIENTE**

**Checklist:**
- [ ] Añadir en `app/__init__.py` después de registrar blueprints:
  ```python
  @app.after_request
  def add_security_headers(response):
      response.headers['X-Content-Type-Options'] = 'nosniff'
      response.headers['X-Frame-Options'] = 'DENY'
      response.headers['X-XSS-Protection'] = '1; mode=block'
      response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
      response.headers['Permissions-Policy'] = 'geolocation=(), microphone=()'
      # Solo en HTTPS (producción):
      if not app.debug:
          response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains'
          response.headers['Content-Security-Policy'] = (
              "default-src 'self'; "
              "script-src 'self' 'unsafe-inline'; "
              "style-src 'self' 'unsafe-inline';"
          )
      return response
  ```

---

### ❌ TASK 1.5: Actualizar requests (CVE activo)
**Prioridad:** 🔴 ALTA  
**Esfuerzo:** 10 minutos  
**Responsable:** Backend Developer  
**Status:** ❌ Sin iniciar

**Checklist:**
- [ ] Actualizar en `requirements.txt`
  ```
  requests==2.32.3  # era 2.31.0 — CVE-2024-35195
  ```
- [ ] Ejecutar `pip install -r requirements.txt`
- [ ] Verificar que no hay breaking changes en el código (API es compatible)

---

## 🔴 SEMANA 2: VULNERABILIDADES ALTAS

### ❌ TASK 2.1: Protección CSRF
**Prioridad:** 🔴 ALTA  
**Esfuerzo:** 2 horas  
**Status:** ❌ Sin iniciar — **30+ DÍAS PENDIENTE**

**Checklist:**
- [ ] Instalar Flask-WTF
  ```bash
  pip install Flask-WTF==1.2.2
  ```
- [ ] Configurar `CSRFProtect` en `app/__init__.py`
  ```python
  from flask_wtf.csrf import CSRFProtect
  csrf = CSRFProtect()
  csrf.init_app(app)
  ```
- [ ] Excluir endpoints de API JSON que usan tokens Bearer (si se implementa JWT):
  ```python
  @csrf.exempt
  @auth_bp.route('/login', methods=['POST'])
  ```
- [ ] Configurar el frontend para enviar el token CSRF en formularios

---

### ❌ TASK 2.2: Implementar RBAC Básico
**Prioridad:** 🔴 ALTA  
**Esfuerzo:** 12 horas  
**Status:** ❌ Sin iniciar — **30+ DÍAS PENDIENTE**

**Checklist:**
- [ ] Definir roles del sistema:
  - `admin` — acceso completo
  - `collections` — solo módulo cobranzas
  - `treasury` — solo módulo tesorería
  - `letters` — solo módulo letras
- [ ] Consultar grupos del usuario en Odoo durante el login
- [ ] Almacenar roles en el JWT (claim `roles`) o en la sesión Flask
- [ ] Crear decorador `require_role` en `app/auth/security.py`:
  ```python
  def require_role(*roles):
      def decorator(view_func):
          @wraps(view_func)
          def wrapper(*args, **kwargs):
              user_roles = session.get('roles', [])
              if not any(r in user_roles for r in roles):
                  return jsonify({'message': 'Acceso no autorizado'}), 403
              return view_func(*args, **kwargs)
          return wrapper
      return decorator
  ```
- [ ] Aplicar `@require_role` en todos los blueprints por módulo

---

### ❌ TASK 2.3: Logging Estructurado
**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** 4 horas  
**Status:** ❌ Sin iniciar

**Checklist:**
- [ ] Configurar `logging` en `app/__init__.py` con formato JSON
- [ ] Reemplazar todos los `print()` en `app/core/odoo.py` con `logger.info/error`
- [ ] Añadir audit log para eventos de seguridad (login, logout, acceso denegado)
- [ ] Nunca loggear contraseñas ni tokens completos

---

### ❌ TASK 2.4: Fix Cache Cross-Session
**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** 2 horas  
**Status:** ❌ Sin iniciar (nueva vulnerabilidad detectada en Junio 2026)

**Checklist:**
- [ ] Modificar `app/collections/routes.py` — incluir usuario en la cache key
- [ ] Modificar `app/letters/routes.py` — mismo fix
- [ ] Remover el decorador `@cache.cached` de los endpoints e implementar cache manual con user-specific key

---

### ❌ TASK 2.5: Límite Máximo en Exportaciones
**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** 1 hora  
**Status:** ❌ Sin iniciar (nueva vulnerabilidad detectada en Junio 2026)

**Checklist:**
- [ ] Agregar en `config.py`: `MAX_EXPORT_LIMIT = 10000`
- [ ] Aplicar en `app/collections/routes.py:L54` y `app/exports/routes.py:L52`:
  ```python
  MAX_LIMIT = current_app.config.get('MAX_EXPORT_LIMIT', 10000)
  limit_raw = request.args.get('limit', type=int, default=0)
  limit = min(limit_raw, MAX_LIMIT) if limit_raw > 0 else MAX_LIMIT
  ```

---

## 🟡 SEMANA 3-4: HARDENING Y CALIDAD

### ❌ TASK 3.1: Refactorizar config.py (Eliminar Duplicación)
**Esfuerzo:** 3 horas  
**Status:** ❌ Sin iniciar

- [ ] Extraer método `_load_common_env(cls, app)` en clase base `Config`
- [ ] `DevelopmentConfig` y `ProductionConfig` solo definen `DEBUG` y llaman al método base
- [ ] Reducir ~80 líneas duplicadas a ~10

---

### ❌ TASK 3.2: Anclar Versiones en requirements.txt
**Esfuerzo:** 30 minutos  
**Status:** ❌ Sin iniciar

- [ ] Reemplazar `polars>=1.41.0` → `polars==1.41.0`
- [ ] Reemplazar `XlsxWriter>=3.2.9` → `XlsxWriter==3.2.9`
- [ ] Actualizar `gunicorn` a 23.0.0
- [ ] Actualizar `celery` a 5.4.0

---

### ❌ TASK 3.3: pip-audit en CI/CD
**Esfuerzo:** 2 horas  
**Status:** ❌ Sin iniciar

- [ ] Instalar `pip-audit`: `pip install pip-audit`
- [ ] Agregar a pipeline CI: `pip-audit --requirement requirements.txt`
- [ ] Configurar para fallar build si hay CVEs críticos

---

### ❌ TASK 3.4: Eliminar CORS self-origin
**Esfuerzo:** 15 minutos  
**Status:** ❌ Sin iniciar

- [ ] En `app/__init__.py:L44`, remover `http://localhost:5000` de `cors_origins`
  ```python
  # ANTES:
  cors_origins = ["http://localhost:3000", "http://localhost:5000"]
  # DESPUÉS:
  cors_origins = ["http://localhost:3000"]
  ```

---

## ✅ MEJORAS ARQUITECTÓNICAS COMPLETADAS (Junio 2026)

| # | Mejora | Archivo | Completado |
|---|--------|---------|-----------|
| A1 | UID caching thread-safe | app/core/odoo.py | ✅ Jun 2026 |
| A2 | call_parallel() ThreadPoolExecutor | app/core/odoo.py | ✅ Jun 2026 |
| A3 | _read_in_batches helpers | app/collections/services.py | ✅ Jun 2026 |
| A4 | RESTRICT_TO_LETTERS_ONLY middleware | app/__init__.py | ✅ Jun 2026 |
| A5 | _apply_session_settings() cross-site | config.py | ✅ Jun 2026 |
| A6 | _build_trace_invoice_map() | app/collections/services.py | ✅ Jun 2026 |

---

## 📅 Cronograma Actualizado

```
JULIO 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Semana 1 (Jul 1-7):
  Lun:  🚨 Fix auth bypass (30 min) + DEBUG=False (15 min) ← MÍNIMO HOY
  Mar:  JWT Real - Backend (4 hrs)
  Mie:  JWT Real - Frontend integration (4 hrs)
  Jue:  Rate Limiting + Security Headers (2 hrs)
  Vie:  Actualizar requests + QA (2 hrs)
  ─────────────────────────────────────────────────────
  Total: ~13 horas | 1 Backend Dev

Semana 2 (Jul 8-14):
  CSRF Protection          | 2 hrs
  RBAC Básico              | 12 hrs
  Logging Estructurado     | 4 hrs
  ─────────────────────────────────────────────────────
  Total: ~18 horas | 1-2 Developers

Semana 3-4 (Jul 15-28):
  Fix cache cross-session  | 2 hrs
  Límite máximo exports    | 1 hr
  Refactorizar config.py   | 3 hrs
  Anclar dependencias      | 30 min
  pip-audit CI/CD          | 2 hrs
  ─────────────────────────────────────────────────────
  Total: ~9 horas | 1 Developer

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL JULIO: ~40 horas | Meta: Score Seguridad 75+/100
```

---

## ⚠️ NOTA IMPORTANTE — RETRASO DE 30 DÍAS

Las **5 vulnerabilidades críticas originales** identificadas el 26 de Mayo de 2026 siguen sin resolverse. Adicionalmente, se ha **introducido una nueva vulnerabilidad crítica** (auth bypass) en el código nuevo.

**Recomendación urgente:** Los items marcados como `← MÍNIMO HOY` en el cronograma son cambios de 30-60 minutos que pueden ejecutarse inmediatamente y tienen impacto de seguridad crítico. No requieren diseño ni planning adicional.

---

**Actualizado por:** Auditoría de Seguridad — Jun 25, 2026  
**Próxima revisión del checklist:** Jul 25, 2026
