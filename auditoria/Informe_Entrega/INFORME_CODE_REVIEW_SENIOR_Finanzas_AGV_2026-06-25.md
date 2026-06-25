# Code Review Arquitectónico — Finanzas AGV (Architectural Code Review — Finanzas AGV)
## Análisis Senior: SOLID, Seguridad, Rendimiento, Mantenibilidad — **ACTUALIZACIÓN MENSUAL**

> 📅 **Fecha de auditoría (Audit date)**: 25/06/2026  
> 📅 **Auditoría anterior (Previous audit)**: 26/05/2026  
> 📊 **Progreso general (Overall progress)**: 42/100 _(anterior: 35/100 — mejora +7 pts en arquitectura, vulnerabilidades críticas persisten)_  
> ✅ **Mejoras detectadas (Improvements detected)**:
> - `OdooRepository` refactorizado con caché de UID thread-safe y paralelismo (`call_parallel`).
> - `CollectionsService` ampliado con helpers de batch reading robustos.
> - `RESTRICT_TO_LETTERS_ONLY` middleware como defensa en profundidad (nuevo control).
> - Mejor gestión de sesiones en `config.py` (cross-site, SameSite configurable).
> 🔴 **Crítico pendiente (Still critical)**:
> - `dummy_token_12345` persiste — JWT real **no implementado** tras >30 días.
> - `ProductionConfig.DEBUG = True` + `run.py debug=True` en producción — **sin cambio**.
> - Sin Rate Limiting, sin CSRF, sin RBAC — **ninguno implementado**.
> 🚨 **Nueva vulnerabilidad detectada (New vulnerability)**:
> - Auth bypass via service credentials fallback en `OdooRepository.authenticate_user()` (`app/core/odoo.py:L147-150`).
> 🔄 **Próxima fase (Next phase)**: Implementación urgente de JWT + DEBUG=False + Rate Limiting

---

## Resumen Ejecutivo (Executive Summary)

**Puntuación General (Overall Score): 42/100** _(anterior: 35/100)_

| Área (Area) | Puntuación Anterior | Puntuación Actual | Δ | Estado | Prioridad |
|-------------|---------------------|--------------------|---|--------|-----------|
| Principios SOLID | 4/10 | 5/10 | ⬆️ +1 | ⚠️ | Alta |
| Seguridad OWASP | 2/10 | 2/10 | = | 🔴 | **CRÍTICA** |
| Rendimiento | 5/10 | 7/10 | ⬆️ +2 | ✅ | Media |
| Mantenibilidad | 4/10 | 5/10 | ⬆️ +1 | ⚠️ | Media |
| Arquitectura | 6/10 | 7/10 | ⬆️ +1 | ✅ | Media |

### ✅ Mejoras Implementadas desde Mayo 2026

| # | Mejora | Archivo | Impacto |
|---|--------|---------|---------|
| 1 | UID caching thread-safe con `threading.Lock()` | `app/core/odoo.py:L40-71` | Rendimiento ↑ |
| 2 | `call_parallel()` con `ThreadPoolExecutor` | `app/core/odoo.py:L262-320` | Rendimiento ↑↑ |
| 3 | Helpers `_chunked`, `_read_in_batches`, `_search_read_in_batches` | `app/collections/services.py:L55-84` | Robustez ↑ |
| 4 | `RESTRICT_TO_LETTERS_ONLY` middleware (defensa en profundidad) | `app/__init__.py:L119-157` | Seguridad ↑ |
| 5 | `_apply_session_settings()` con soporte cross-site configurable | `config.py:L82-106` | Sesiones ↑ |
| 6 | `_build_trace_invoice_map()` con lógica de traza fuerte/fallback | `app/collections/services.py:L97-` | Negocio ↑ |

### 🔴 Issues Críticos Persistentes (>30 días sin resolver)

1. **🔴 CRÍTICO: Dummy Token — JWT Real NO implementado**
   - Evidencia: `app/auth/routes.py:L96` — `'token': 'dummy_token_12345'`
   - **Estado: SIN CAMBIO desde 26/05/2026**
   - Impacto: Cualquier cliente puede capturar el token y suplantar identidad.

2. **🔴 CRÍTICO: DEBUG=True en ProductionConfig**
   - Evidencia: `config.py:L188` + `run.py:L66` (bloque `elif environment == 'production'`)
   - **Estado: SIN CAMBIO desde 26/05/2026**
   - Impacto: Stacktraces completos expuestos, rutas internas visibles, debugger activo.

3. **🔴 CRÍTICO: Sin RBAC — un solo nivel de autorización**
   - Evidencia: `app/auth/security.py:L10-23` — solo verifica `session.get('logged_in')`, sin roles.
   - **Estado: SIN CAMBIO desde 26/05/2026**
   - Impacto: Todo usuario autenticado accede a todos los módulos.

4. **🔴 ALTO: Sin Rate Limiting en /login**
   - `requirements.txt` — Flask-Limiter **no está instalado**
   - **Estado: SIN CAMBIO desde 26/05/2026**
   - Impacto: Ataques de fuerza bruta sin mitigación.

5. **🔴 ALTO: Sin protección CSRF**
   - `requirements.txt` — Flask-WTF **no está instalado**
   - **Estado: SIN CAMBIO desde 26/05/2026**
   - Impacto: Endpoints POST vulnerables a cross-site request forgery.

### 🚨 Nueva Vulnerabilidad Detectada (Introducida en este ciclo)

**AUTH BYPASS via Service Credentials Fallback** (`app/core/odoo.py:L147-150`)

```python
# VULNERABLE - app/core/odoo.py:L145-150
except Exception as exc:
    print(f"[ERROR] Error en autenticación contra Odoo: {exc}")
    # Fallback: verificar si coincide con las credenciales del repositorio
    if username == self.username and password == self.password:
        print("[OK] Autenticación exitosa usando credenciales del repositorio")
        return True
```

**Riesgo**: Si Odoo está temporalmente no disponible (timeout, mantenimiento), el sistema permite autenticarse con las credenciales del servicio (las del `.env`). Esto significa:
- Las credenciales `ODOO_USER`/`ODOO_PASSWORD` pueden usarse como login de usuario.
- Un atacante con acceso al `.env.produccion` puede loguearse en la app con esas credenciales.
- La disponibilidad de Odoo se convierte en un factor de seguridad.

---

## 1️⃣ Principios SOLID — 5/10 (⬆️ anterior: 4/10)

### 1.1 Single Responsibility Principle (SRP) — 5/10

**Mejora**: `OdooRepository` ahora tiene responsabilidades más claras: conexión, autenticación, acceso a datos y paralelismo. La separación es correcta.

**Persiste**: `app/collections/routes.py` sigue mezclando parseo de parámetros, lógica de negocio y construcción de respuesta. El endpoint `report_account12` (L29-567) es demasiado extenso.

**Ejemplo de mejora implementada (OdooRepository):**
```python
# app/core/odoo.py - Buena separación de métodos
def _connect(self):          # Responsabilidad: establecer conexión
def authenticate_user(self): # Responsabilidad: auth de usuario
def execute_kw(self):        # Responsabilidad: wrapper genérico
def call_parallel(self):     # Responsabilidad: paralelismo
```

**Ejemplo que viola SRP (aún presente):**
```python
# app/collections/routes.py:L29-567 — un solo endpoint hace demasiado
@collections_bp.route('/report/account12', methods=['GET'])
@require_login
@cache.cached(timeout=300, query_string=True)
def report_account12():
    # Parsea 12+ parámetros de query string
    # Instancia servicios
    # Llama a 2 paths diferentes (summary_only vs full)
    # Construye respuesta compleja
    # Maneja múltiples excepciones
    # ... ~200 líneas de lógica mezclada
```

### 1.2 Open/Closed Principle (OCP) — 5/10

**Mejora**: `CollectionsService` puede extenderse sin modificar métodos base gracias a los helpers internos (`_chunked`, `_read_in_batches`).

**Persiste**: `config.py` usa clases que heredan de `Config` pero con duplicación masiva de código entre `DevelopmentConfig` y `ProductionConfig`. El 80% de `init_app()` es idéntico.

```python
# config.py — DevelopmentConfig.init_app() vs ProductionConfig.init_app()
# Ambas clases repiten ~40 líneas idénticas de carga de variables de entorno
# Violación DRY + OCP: cualquier nuevo var requiere modificar AMBAS clases
```

**Recomendación:**
```python
class Config:
    @classmethod
    def _load_common_env(cls, app):
        """Cargar variables comunes de entorno — un solo lugar."""
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', cls._default_secret())
        app.config['ODOO_URL'] = os.getenv('ODOO_URL')
        # ... resto de vars comunes

class ProductionConfig(Config):
    DEBUG = False  # ← única diferencia real
    @classmethod
    def init_app(cls, app):
        load_dotenv('.env.produccion', override=True)
        cls._load_common_env(app)  # reutilizar
        cls._apply_session_settings(app, secure_default=True, samesite_default='None')
```

### 1.3 Liskov Substitution Principle (LSP) — 6/10

Cumple parcialmente. `OdooRepository` puede sustituirse con mocks en tests (con `ODOO_URL=http://localhost:8069` en `TestingConfig`).

### 1.4 Interface Segregation Principle (ISP) — 5/10

`OdooRepository` expone 8 métodos públicos. Para servicios que solo necesitan `search_read`, se inyecta más interfaz de la necesaria.

### 1.5 Dependency Inversion Principle (DIP) — 5/10

**Mejora**: Los servicios reciben `odoo_repository` como dependencia inyectada en el constructor.

**Persiste**: Las rutas crean instancias directamente con `_get_odoo_repository()` — acoplamiento a la implementación concreta.

```python
# app/collections/routes.py:L17-26 — crear instancia concreta en la ruta
# Debería inyectarse o usarse un factory registrado en el contexto de app
def _get_odoo_repository():
    return OdooRepository(
        url=current_app.config['ODOO_URL'], ...  # hardcoded implementation
    )
```

---

## 2️⃣ Seguridad OWASP — 2/10 (= sin cambio)

### A01:2021 — Broken Access Control 🔴 CRÍTICO (SIN CAMBIO)

**Problemas persistentes:**

1. **Sin RBAC**: `require_login` solo verifica autenticación, no autorización por rol.
   ```python
   # app/auth/security.py:L10-23 — SOLO verifica logged_in, sin roles
   def require_login(view_func):
       if not session.get('logged_in'):
           return 401
       return view_func(*args, **kwargs)  # sin verificar rol/permiso
   ```

2. **Cache cross-session risk** (`app/collections/routes.py:L30-32`):
   ```python
   @require_login              # ← Ejecuta PRIMERO (decorator más externo)
   @cache.cached(timeout=300, query_string=True)  # ← puede cachear por parámetros
   def report_account12():
   ```
   Con `simple` cache (no Redis), el caché es global y no está vinculado a la sesión del usuario. Un usuario A puede recibir datos cacheados del usuario B si hacen la misma consulta.

### A07:2021 — Identification and Authentication Failures 🔴 CRÍTICO

**Problema 1 — Dummy Token (persiste):**
```python
# app/auth/routes.py:L96 — TOKEN FALSO — NO CAMBIADO EN 30 DÍAS
return jsonify({
    'success': True,
    'token': 'dummy_token_12345',  # ← CRÍTICO: token predecible, sin expiración
```

**Problema 2 — AUTH BYPASS (nuevo):**
```python
# app/core/odoo.py:L147-150
except Exception as exc:
    if username == self.username and password == self.password:
        return True  # ← permite auth con credenciales del servicio si Odoo falla
```

**Problema 3 — Sin Rate Limiting:**
- No hay `Flask-Limiter` instalado ni configurado.
- El endpoint `/api/v1/auth/login` puede recibir miles de intentos por segundo.

### A05:2021 — Security Misconfiguration 🔴 CRÍTICO (SIN CAMBIO)

```python
# config.py:L188 — ProductionConfig con DEBUG=True
class ProductionConfig(Config):
    DEBUG = True   # ← CRÍTICO: NUNCA debe ser True en producción

# run.py:L64-68 — debug=True explícito en bloque de producción
elif environment == 'production':
    app.run(host='0.0.0.0', port=5000, debug=True)  # ← CRÍTICO
```

**Sin security headers** — no hay `after_request` que añada:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `Strict-Transport-Security`
- `Referrer-Policy`

### A04:2021 — Insecure Design 🟡 MEDIO

**Sin límite máximo en exportaciones:**
```python
# app/collections/routes.py:L54 y app/exports/routes.py:L52
limit = request.args.get('limit', type=int, default=0)
# limit=0 → Odoo interpreta como "sin límite" → puede traer millones de registros
# No hay límite máximo definido → vector de DoS
```

**Información interna expuesta en errores:**
```python
# app/auth/routes.py:L113-115
except Exception as e:
    return jsonify({'message': f'Error al conectar con Odoo: {str(e)}'}), 500
# Expone: URL de Odoo, tipo de error, detalles de infraestructura
```

---

## 3️⃣ Rendimiento — 7/10 (⬆️ anterior: 5/10)

### Mejoras implementadas (notables)

**1. ThreadPoolExecutor para llamadas paralelas:**
```python
# app/core/odoo.py:L262-320 — EXCELENTE mejora de rendimiento
def call_parallel(self, calls: List[dict]) -> list:
    max_workers = min(len(calls), 8)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_execute, i, c): i for i, c in enumerate(calls)}
```
Impacto: Reduce tiempo de reportes multi-modelo de N×T a ≈T (paralelo).

**2. Batch reading para evitar timeouts XML-RPC:**
```python
# app/collections/services.py:L55-84
def _read_in_batches(self, model, ids, fields, batch_size=500):
    for batch in self._chunked(ids, batch_size):
        results.extend(self.repository.read(model, batch, fields) or [])
```
Impacto: Evita timeouts con grandes volúmenes de datos (>500 registros).

**3. UID caching con invalidación inteligente:**
```python
# app/core/odoo.py:L83-95
if self.uid:
    try:
        self.models.execute_kw(...)  # Verifica que el UID sigue válido
        return
    except Exception:
        self.uid = None  # Invalida y re-autentica
```

### Problemas de rendimiento que persisten

**1. Flask `simple` cache no es thread-safe en alta concurrencia:**
```python
# app/__init__.py:L77 — fallback a simple cache
app.config['CACHE_TYPE'] = 'simple'  # Problema en multi-worker gunicorn
```

**2. Instanciación de OdooRepository en cada request:**
```python
# app/collections/routes.py:L57 — nueva instancia por request
odoo_repo = _get_odoo_repository()  # conecta a Odoo en cada petición
```
Con el caché de UID, esto mejora, pero sigue creando el objeto `ServerProxy` por request.

---

## 4️⃣ Mantenibilidad — 5/10 (⬆️ anterior: 4/10)

### Mejoras detectadas

- **Docstrings completos** en `OdooRepository` (parámetros, retornos, ejemplos).
- **Type hints** consistentes en `OdooRepository` (`Dict`, `List`, `Optional`).
- **`_has_value()` y `_m2o_id()`** — helpers internos bien nombrados en `CollectionsService`.

### Problemas de mantenibilidad que persisten

**1. Duplicación en config.py:**
```python
# DevelopmentConfig.init_app() y ProductionConfig.init_app() comparten ~40 líneas idénticas
# Si se agrega un nuevo parámetro, debe agregarse en AMBOS lugares
```

**2. Print statements como logging:**
```python
# app/core/odoo.py:L92,102,104,109 — usando print() en lugar de logging
print(f"[OK] Conexión a Odoo establecida. UID={self.uid}")
print(f"[ERROR] Error en la conexión a Odoo: {exc}")
# Problema: no hay nivel de log, no hay archivo de log, no hay timestamps
```

**3. TODO comments sin ticket:**
```python
# app/auth/routes.py:L96
'token': 'dummy_token_12345',  # En producción: generar JWT real
# Este TODO lleva >30 días sin resolverse
```

---

## 5️⃣ Arquitectura — 7/10 (⬆️ anterior: 6/10)

### Fortalezas arquitectónicas

```
✅ Separación por capas: routes → services → repository → Odoo
✅ Factory pattern para la app Flask (create_app)
✅ Blueprint structure escalable (7 blueprints)
✅ OdooRepository con patrón Repository bien implementado
✅ RESTRICT_TO_LETTERS_ONLY como feature flag de módulos
✅ Celery para tareas asíncronas
✅ Flask-Caching con soporte Redis/simple
✅ Supabase como capa de persistencia paralela
```

### Problemas arquitectónicos detectados

**1. CORS incluye el origen propio de la API:**
```python
# app/__init__.py:L44 — localhost:5000 es la MISMA API
cors_origins = ["http://localhost:3000", "http://localhost:5000"]
# La API no debería estar en su propia lista de CORS origins
```

**2. Módulo de emails sin implementación:**
```python
# app/emails/routes.py:L36 — endpoints que retornan 501
return jsonify({'message': 'Funcionalidad pendiente de implementación'}), 501
# El módulo está registrado como blueprint activo pero no funciona
```

**3. Falta de abstracción de caché:**
```python
# Las rutas usan @cache.cached directamente, sin abstraer el key
# No hay invalidación de caché cuando los datos cambian
# No hay caché por usuario (todos comparten el mismo caché)
```

---

## 📊 Comparativa Mayo vs Junio 2026

| Indicador | Mayo 2026 | Junio 2026 | Cambio |
|-----------|-----------|------------|--------|
| Score General | 35/100 | 42/100 | ⬆️ +7 |
| Score Seguridad | 58/100 | 55/100 | ⬇️ -3 (nueva vuln) |
| Vulnerabilidades Críticas | 5 | 5+1=**6** | ⬆️ +1 nueva |
| Vulnerabilidades Altas | 6 | 6 | = |
| Vulnerabilidades Medias | 8 | 7 | ⬇️ -1 (resuelto parcial) |
| Mejoras Arquitectónicas | — | 6 nuevas | ✅ |
| JWT Real implementado | ❌ | ❌ | **Sin cambio** |
| DEBUG=False en producción | ❌ | ❌ | **Sin cambio** |
| Rate Limiting | ❌ | ❌ | **Sin cambio** |
| CSRF Protection | ❌ | ❌ | **Sin cambio** |
| RBAC implementado | ❌ | ❌ | **Sin cambio** |
| Auth Bypass via fallback | — | 🔴 **Nuevo** | Regresión |

---

## 🚨 Prioridades Inmediatas (Semana 1)

| # | Acción | Archivo | Esfuerzo | Impacto |
|---|--------|---------|----------|---------|
| 1 | **Eliminar auth fallback** en `authenticate_user` | `app/core/odoo.py:L147-150` | 30 min | 🔴 Crítico |
| 2 | **DEBUG=False** en ProductionConfig y run.py | `config.py:L188`, `run.py:L66` | 15 min | 🔴 Crítico |
| 3 | **Implementar JWT real** con Flask-JWT-Extended | `app/auth/routes.py` | 4h | 🔴 Crítico |
| 4 | **Añadir Rate Limiting** a /login | `app/auth/routes.py` | 1h | 🔴 Alto |
| 5 | **Agregar límite máximo** a exportaciones | `collections/routes.py`, `exports/routes.py` | 30 min | 🟡 Medio |
| 6 | **Security Headers** en `after_request` | `app/__init__.py` | 1h | 🔴 Alto |
| 7 | **Reemplazar print() con logging** | `app/core/odoo.py` | 1h | 🟡 Medio |

---

**Auditor:** Senior Architecture & Security Reviewer  
**Fecha:** 25 de Junio de 2026  
**Periodo cubierto:** Mayo 26 → Junio 25, 2026  
**Próxima revisión:** Julio 2026  
