# ✅ CHECKLIST DE REMEDIACIÓN - FINANZAS AGV
## Plan de Implementación para Development Team

**Versión:** 1.0  
**Fecha:** 26 Mayo 2026  
**Sprint:** 4 semanas  
**Equipo:** 2-3 Developers + 1 Security Lead  

---

## 🔴 SEMANA 1: VULNERABILIDADES CRÍTICAS

### ✅ TASK 1.1: Implementar JWT Real (Token Validation)
**Prioridad:** 🔴 CRÍTICA  
**Esfuerzo:** 4 horas  
**Responsable:** Backend Lead  
**Status:** ⬜ Not Started

**Checklist:**
- [ ] Instalar Flask-JWT-Extended
  ```bash
  pip install Flask-JWT-Extended==4.5.3
  pip freeze > requirements.txt
  ```
- [ ] Configurar JWT en app/__init__.py
  ```python
  from flask_jwt_extended import JWTManager
  jwt = JWTManager()
  app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
  app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
  jwt.init_app(app)
  ```
- [ ] Actualizar auth/routes.py - endpoint /login
  - [ ] Generar access_token con create_access_token()
  - [ ] Incluir claims: email, role, permissions
  - [ ] Devolver en respuesta JSON
  
- [ ] Crear endpoint /refresh para renovar token
  - [ ] Usar refresh_token
  - [ ] Devolver nuevo access_token
  
- [ ] Crear endpoint /verify para validar token
  - [ ] Proteger con @jwt_required()
  - [ ] Devolver claims del usuario
  
- [ ] Actualizar auth/security.py
  - [ ] Crear require_jwt_login() decorator
  - [ ] Usar @jwt_required() en lugar de session
  
- [ ] Actualizar todos los endpoints API
  - [ ] collections/routes.py: Cambiar require_login a require_jwt_login
  - [ ] treasury/routes.py: Aplicar mismo cambio
  - [ ] letters/routes.py: Aplicar mismo cambio
  - [ ] exports/routes.py: Aplicar mismo cambio
  
- [ ] Actualizar frontend Axios (frontend/lib/api.ts)
  - [ ] Agregar interceptor para incluir token en headers
  - [ ] Implementar refresh token en 401
  
- [ ] Testing
  - [ ] Probar login y obtener token
  - [ ] Probar acceso a endpoint con token válido
  - [ ] Probar rechazo con token inválido
  - [ ] Probar refresh token
  - [ ] Verificar expiración en 1 hora
  
**Código de Referencia:**
Ver INFORME_AUDITORIA_COMPLETA_2026-05-26.md → V3 (Token Dummy)

**PR Review Checklist:**
- [ ] Todos los endpoints usan @jwt_required()
- [ ] No hay hardcoded tokens
- [ ] JWT incluye role y permissions
- [ ] Frontend maneja token refresh
- [ ] Errores 401 redirigen a /login

---

### ✅ TASK 1.2: Generar SECRET_KEY Fuerte
**Prioridad:** 🔴 CRÍTICA  
**Esfuerzo:** 1 hora  
**Responsable:** DevOps / Backend Lead  
**Status:** ⬜ Not Started

**Checklist:**
- [ ] Generar nueva SECRET_KEY
  ```bash
  python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
  ```
- [ ] Agregar a .env (NO COMMITEAR)
  ```bash
  echo "SECRET_KEY=<generated-key>" >> .env
  ```
- [ ] Validar en config.py que exista
  ```python
  def get_secret_key():
      key = os.getenv('SECRET_KEY')
      if not key or len(key) < 32:
          raise ValueError("SECRET_KEY no configurada o débil")
      return key
  ```
- [ ] Testing
  - [ ] Verificar que config.py carga sin error
  - [ ] Verificar que sesiones funcionan
  - [ ] Verificar que JWT se valida correctamente
  
**Documentar:**
- [ ] Guardar SECRET_KEY en AWS Secrets Manager
- [ ] Documentar en .env.example (sin valor real)

---

### ✅ TASK 1.3: Mover Credenciales de Odoo a Secrets Manager
**Prioridad:** 🔴 CRÍTICA  
**Esfuerzo:** 8 horas  
**Responsable:** DevOps Lead + Backend Dev  
**Status:** ⬜ Not Started

**Subtasks:**

#### 1.3.1: Crear Secretos en AWS Secrets Manager
- [ ] Acceder a AWS Console
- [ ] Crear secreto: `prod/finanzas-agv/odoo`
  ```json
  {
    "url": "https://odoo.prod.com",
    "db": "production_db",
    "username": "api_user",
    "password": "<strong-password>"
  }
  ```
- [ ] Configurar rotación automática (30 días)
- [ ] Permitir acceso desde ECS/Lambda/EC2

#### 1.3.2: Implementar SecretsManager en Backend
- [ ] Crear core/secrets.py
  ```python
  import boto3, json, logging
  
  class SecretsManager:
      def __init__(self):
          self.client = boto3.client('secretsmanager')
          self.cache = {}
      
      def get_secret(self, secret_name):
          if secret_name in self.cache:
              return self.cache[secret_name]
          response = self.client.get_secret_value(SecretId=secret_name)
          secret = json.loads(response['SecretString'])
          self.cache[secret_name] = secret
          return secret
  ```
  
- [ ] Actualizar config.py (ProductionConfig)
  ```python
  class ProductionConfig:
      def __init__(self):
          sm = SecretsManager()
          creds = sm.get_secret('prod/finanzas-agv/odoo')
          self.ODOO_URL = creds['url']
          self.ODOO_DB = creds['db']
          self.ODOO_USER = creds['username']
          self.ODOO_PASSWORD = creds['password']
  ```

#### 1.3.3: Testing
- [ ] Probar conexión a AWS Secrets Manager
- [ ] Probar carga de credenciales
- [ ] Probar conexión a Odoo con credenciales del secreto
- [ ] Verificar que no hay credenciales en logs

#### 1.3.4: CI/CD
- [ ] Agregar política IAM para ECS task role
- [ ] Documentar en terraform/secrets.tf
- [ ] Validar en staging antes de prod

---

### ✅ TASK 1.4: Implementar CSRF Protection
**Prioridad:** 🔴 CRÍTICA  
**Esfuerzo:** 2 horas  
**Responsable:** Backend Dev  
**Status:** ⬜ Not Started

**Checklist:**
- [ ] Instalar Flask-WTF
  ```bash
  pip install Flask-WTF==1.2.1
  ```
- [ ] Configurar CSRF en app/__init__.py
  ```python
  from flask_wtf.csrf import CSRFProtect
  csrf = CSRFProtect()
  csrf.init_app(app)
  ```
- [ ] Agregar decorador a endpoints POST/PUT/DELETE
  ```python
  @auth_bp.route('/login', methods=['POST'])
  @csrf.protect
  def login():
      ...
  ```
- [ ] Crear endpoint para obtener CSRF token
  ```python
  @app.route('/api/v1/csrf-token', methods=['GET'])
  def get_csrf_token():
      return jsonify({'csrf_token': generate_csrf()})
  ```
- [ ] Actualizar frontend (lib/api.ts)
  ```typescript
  const token = await fetch('/api/v1/csrf-token').then(r => r.json());
  axios.defaults.headers.common['X-CSRFToken'] = token.csrf_token;
  ```
- [ ] Testing
  - [ ] Probar POST sin CSRF token (debe fallar)
  - [ ] Probar POST con CSRF token válido (debe pasar)
  - [ ] Verificar que token está en cookie

---

### ✅ TASK 1.5: QA y Testing de Semana 1
**Prioridad:** 🔴 CRÍTICA  
**Esfuerzo:** 4 horas  
**Responsable:** QA / Backend Lead  
**Status:** ⬜ Not Started

**Checklist:**
- [ ] Ejecutar suite de tests
  ```bash
  pytest app/ -v --tb=short
  ```
- [ ] Validar cobertura mínimo 80%
  ```bash
  pytest --cov=app app/ --cov-report=html
  ```
- [ ] Testing manual end-to-end
  - [ ] Login → obtener JWT
  - [ ] Acceder con JWT a /collections/report/account12
  - [ ] Refresh token después de 1 hora
  - [ ] Logout y perder acceso
  
- [ ] Testing de seguridad básico
  - [ ] Intentar acceder sin token (debe fallar)
  - [ ] Intentar con token expirado (debe fallar)
  - [ ] Intentar con token falso (debe fallar)
  
- [ ] Code review con Security Lead
  - [ ] Revisar auth/routes.py
  - [ ] Revisar config.py
  - [ ] Revisar secrets.py

---

## 🔴 SEMANA 2: VULNERABILIDADES ALTAS

### ✅ TASK 2.1: Implementar RBAC Completo
**Prioridad:** 🔴 ALTA  
**Esfuerzo:** 12 horas  
**Responsable:** 2 Backend Devs  
**Status:** ⬜ Not Started

**Subtasks:**

#### 2.1.1: Definir Matriz de Roles y Permisos
- [ ] Crear config/roles.py
  ```python
  RBAC_ROLES = {
      'admin': {
          'permissions': [
              'view:collections', 'view:treasury', 'view:letters',
              'send:letters', 'export:reports', 'manage:users'
          ]
      },
      'cobrador': {
          'permissions': [
              'view:collections', 'view:letters', 'send:letters'
          ]
      },
      'tesorero': {
          'permissions': [
              'view:collections', 'view:treasury', 'view:letters'
          ]
      },
      'viewer': {
          'permissions': ['view:collections', 'view:treasury']
      }
  }
  ```

#### 2.1.2: Obtener Roles de Odoo
- [ ] Actualizar core/odoo.py - agregar get_user_role()
  ```python
  def get_user_role(self, user_id):
      # Leer grupos del usuario desde Odoo
      # Mapear a roles de aplicación
  ```

#### 2.1.3: Crear Decoradores de Autorización
- [ ] Actualizar auth/security.py
  ```python
  def require_permission(permission: str):
      def decorator(view_func):
          @wraps(view_func)
          def wrapper(*args, **kwargs):
              claims = get_jwt()
              permissions = claims.get('permissions', [])
              if permission not in permissions:
                  return jsonify({'message': 'Acceso Denegado'}), 403
              return view_func(*args, **kwargs)
          return wrapper
      return decorator
  
  def require_role(*allowed_roles):
      def decorator(view_func):
          # Similar implementación
          return wrapper
      return decorator
  ```

#### 2.1.4: Actualizar Todos los Endpoints
- [ ] collections/routes.py
  ```python
  @require_permission('view:collections')
  def report_account12():
  ```
  
- [ ] treasury/routes.py
  ```python
  @require_permission('view:treasury')
  def report_account42():
  ```
  
- [ ] letters/routes.py
  ```python
  @require_permission('send:letters')
  def send_letter():
  ```
  
- [ ] exports/routes.py
  ```python
  @require_permission('export:reports')
  def export_collections():
  ```

#### 2.1.5: Testing
- [ ] Crear test fixtures por rol
- [ ] Probar cobrador → denied en treasury
- [ ] Probar tesorero → denied en send_letters
- [ ] Probar admin → allowed en todo

---

### ✅ TASK 2.2: Implementar Rate Limiting
**Prioridad:** 🔴 ALTA  
**Esfuerzo:** 3 horas  
**Responsable:** Backend Dev  
**Status:** ⬜ Not Started

**Checklist:**
- [ ] Instalar Flask-Limiter
  ```bash
  pip install Flask-Limiter==3.5.0
  ```
- [ ] Configurar en app/__init__.py
  ```python
  from flask_limiter import Limiter
  from flask_limiter.util import get_remote_address
  
  limiter = Limiter(
      app=app,
      key_func=get_remote_address,
      storage_uri=app.config.get('REDIS_URL')
  )
  ```
- [ ] Aplicar límites a endpoints críticos
  ```python
  @auth_bp.route('/login', methods=['POST'])
  @limiter.limit("5 per minute")
  def login():
  
  @auth_bp.route('/refresh', methods=['POST'])
  @limiter.limit("10 per minute")
  def refresh():
  
  @auth_bp.route('/verify', methods=['GET'])
  @limiter.limit("20 per minute")
  def verify():
  ```
- [ ] Testing
  - [ ] Hacer 5 requests al /login
  - [ ] Sexto request debe fallar con 429 (Too Many Requests)

---

### ✅ TASK 2.3: Sanitizar Errores (No Exponer Detalles)
**Prioridad:** 🔴 ALTA  
**Esfuerzo:** 4 horas  
**Responsable:** Backend Dev  
**Status:** ⬜ Not Started

**Checklist:**
- [ ] Crear logger centralizado en core/logger.py
  ```python
  import logging
  logger = logging.getLogger('finanzas_agv')
  ```
- [ ] Actualizar todos los try/except
  ```python
  try:
      # ... código ...
  except Exception as e:
      logger.error(f"Detalles técnicos: {str(e)}", exc_info=True)
      return jsonify({
          'success': False,
          'message': 'Error interno del servidor. Contacte soporte.'
      }), 500
  ```
- [ ] Endpoints específicos a revisar:
  - [ ] auth/routes.py (línea ~50)
  - [ ] collections/routes.py (línea ~75)
  - [ ] treasury/routes.py (línea ~60)
  - [ ] exports/routes.py (línea ~40)
  - [ ] emails/routes.py (línea ~35)
  - [ ] letters/routes.py (línea ~45)
  
- [ ] Testing
  - [ ] Enviar request malformado
  - [ ] Verificar error genérico en respuesta
  - [ ] Verificar detalles en logs del servidor

---

### ✅ TASK 2.4: Diseñar MFA (2FA) - Phase Planning
**Prioridad:** 🔴 ALTA  
**Esfuerzo:** 4 horas (diseño/planning)  
**Responsable:** Security Lead + Backend Lead  
**Status:** ⬜ Not Started

**Checklist:**
- [ ] Decidir método MFA
  - [ ] TOTP (Google Authenticator) ← Recomendado
  - [ ] SMS (Twilio)
  - [ ] Email
  
- [ ] Diseño de arquitectura
  ```python
  # Propuesta: TOTP con QR code
  POST /api/v1/auth/mfa/setup
  # Devuelve: QR code para Authenticator
  
  POST /api/v1/auth/mfa/verify
  # Verifica código TOTP antes de completar login
  ```
  
- [ ] Crear documento de diseño
  - [ ] User journey de setup
  - [ ] Backup codes (en caso de perder Authenticator)
  - [ ] Recovery path (si usuario pierde acceso)
  
- [ ] Estimación: 16 horas implementación (Semana 3)

---

### ✅ TASK 2.5: QA de Semana 2
**Prioridad:** 🔴 ALTA  
**Esfuerzo:** 4 horas  
**Responsable:** QA / Security Lead  
**Status:** ⬜ Not Started

**Checklist:**
- [ ] Testing de RBAC
  - [ ] Crear usuarios con diferentes roles
  - [ ] Verificar permisos por endpoint
  
- [ ] Testing de Rate Limiting
  - [ ] Verificar límites de login
  - [ ] Verificar límites de refresh
  
- [ ] Testing de Sanitización de Errores
  - [ ] Verificar que no hay stack traces en respuesta
  - [ ] Verificar que detalles están en logs
  
- [ ] Code review con Security Lead

---

## 🟡 SEMANA 3: ENDURECIMIENTO

### ✅ TASK 3.1: Security Headers
**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** 2 horas  
**Responsable:** Backend Dev  
**Status:** ⬜ Not Started

**Checklist:**
- [ ] Crear middleware en app/__init__.py
  ```python
  @app.after_request
  def add_security_headers(response):
      # Strict Transport Security
      response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
      # Content Security Policy
      response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'"
      # X-Frame-Options
      response.headers['X-Frame-Options'] = 'DENY'
      # X-Content-Type-Options
      response.headers['X-Content-Type-Options'] = 'nosniff'
      # X-XSS-Protection
      response.headers['X-XSS-Protection'] = '1; mode=block'
      return response
  ```
- [ ] Testing
  - [ ] Verificar headers en respuesta HTTP

---

### ✅ TASK 3.2: Logging Centralizado
**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** 8 horas  
**Responsable:** DevOps + Backend Dev  
**Status:** ⬜ Not Started

**Checklist:**
- [ ] Instalar python-json-logger
  ```bash
  pip install python-json-logger==2.0.7
  ```
- [ ] Configurar logging en core/logging_config.py
  ```python
  import logging
  from pythonjsonlogger import jsonlogger
  
  logger = logging.getLogger()
  logHandler = logging.StreamHandler()
  formatter = jsonlogger.JsonFormatter()
  logHandler.setFormatter(formatter)
  logger.addHandler(logHandler)
  ```
- [ ] Agregar eventos de auditoría
  - [ ] Login (usuario, timestamp, IP)
  - [ ] Cambios de RBAC
  - [ ] Acceso a datos sensibles
  - [ ] Errores de autorización
  
- [ ] Integración con CloudWatch/ELK
  - [ ] Enviar logs a CloudWatch (AWS)
  - [ ] O ELK Stack (self-hosted)

---

### ✅ TASK 3.3: CI/CD con Controles de Seguridad
**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** 12 horas  
**Responsable:** DevOps + Security Lead  
**Status:** ⬜ Not Started

**Checklist:**
- [ ] Crear GitHub Actions workflow (.github/workflows/security.yml)
  ```yaml
  name: Security Checks
  on: [push, pull_request]
  jobs:
    sast:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v2
        - name: Bandit SAST
          run: |
            pip install bandit
            bandit -r app/ -f json > bandit-report.json
        
        - name: Safety Dependency Check
          run: |
            pip install safety
            safety check --json
        
        - name: Pylint
          run: |
            pip install pylint
            pylint app/
  ```

- [ ] Integración con SonarQube (opcional)
- [ ] Bloqueador: Fallar si hay secretos detectados
  ```yaml
  - name: Detect Secrets
    run: |
      pip install detect-secrets
      detect-secrets scan --all-files --baseline .secrets.baseline
  ```

---

## 🟢 SEMANA 4: VALIDACIÓN Y GO-LIVE

### ✅ TASK 4.1: Penetration Testing
**Prioridad:** 🟢 IMPORTANTE  
**Esfuerzo:** 16 horas  
**Responsable:** Security Professional (externo)  
**Status:** ⬜ Not Started

**Scope:**
- [ ] Validar JWT implementation
- [ ] Validar RBAC
- [ ] Validar CSRF protection
- [ ] Prueba de rate limiting evasion
- [ ] Validar secrets no están expuestos
- [ ] Validar headers de seguridad

---

### ✅ TASK 4.2: Capacitación del Equipo
**Prioridad:** 🟢 IMPORTANTE  
**Esfuerzo:** 8 horas  
**Responsable:** Security Lead  
**Status:** ⬜ Not Started

**Contenido:**
- [ ] OWASP Top 10
- [ ] Principios de Secure Coding
- [ ] Review de cambios de seguridad
- [ ] Proceso de response a incidentes

---

### ✅ TASK 4.3: Documentación
**Prioridad:** 🟢 IMPORTANTE  
**Esfuerzo:** 6 horas  
**Responsable:** Tech Lead + Security Lead  
**Status:** ⬜ Not Started

**Documentos a crear:**
- [ ] Security Policy
- [ ] Incident Response Plan
- [ ] Runbooks (operacionales)
- [ ] Architecture Security Review

---

## 📊 ESTADO DEL PROYECTO

### Week 1 Progress
```
Task 1.1: [ ] [ ] [ ] [ ] [ ]  (0%)
Task 1.2: [ ] [ ] [ ] [ ] [ ]  (0%)
Task 1.3: [ ] [ ] [ ] [ ] [ ]  (0%)
Task 1.4: [ ] [ ] [ ] [ ] [ ]  (0%)
Task 1.5: [ ] [ ] [ ] [ ] [ ]  (0%)
─────────────────────────────────
Total:    0% ██░░░░░░░░ (0/19 hrs)
```

### Metrics to Track
- [ ] Vulnerabilidades remediadas: ___/15
- [ ] Tests pasados: ___/___
- [ ] Code coverage: ___%
- [ ] Security score: __/100

---

## 📋 REFERENCIA RÁPIDA

### Comandos Útiles
```bash
# Testing
pytest app/ -v
pytest --cov=app app/

# Security Scanning
bandit -r app/
safety check
detect-secrets scan --all-files

# Linting
flake8 app/
pylint app/

# Requirements
pip freeze > requirements.txt
```

### Archivo Ubicaciones Clave
```
app/
├── __init__.py        ← JWT init
├── auth/
│   ├── routes.py      ← JWT login/refresh
│   └── security.py    ← RBAC decorators
├── core/
│   ├── secrets.py     ← NEW: SecretsManager
│   └── logger.py      ← NEW: Logging
└── ... (otros módulos con @require_permission)

config.py             ← SECRET_KEY, SecretsManager init

.env                  ← NO COMMITEAR
.env.example          ← COMMITEAR (template)

requirements.txt      ← Actualizar con nuevos packages
```

---

## 📞 ESCALATION / BLOCKERS

**Contacatalog para:**
- 🔴 Decisión sobre MFA método
- 🔴 AWS Secrets Manager setup
- 🔴 Acceso para Penetration Testing

---

**Última actualización:** 26 Mayo 2026  
**Próxima revisión:** Viernes 29 Mayo (EOD)

