# RB-102: Fallo en Envío de Correos

**ID:** RB-102
**Última Actualización:** 2025-11-20
**Responsable:** DevOps / Backend Developer

## 🎯 Objetivo
Diagnosticar y resolver problemas de envío de correos electrónicos desde el sistema Finanzas AGV.

## 📋 Prerrequisitos
- [ ] Acceso a logs de la aplicación.
- [ ] Credenciales SMTP válidas.
- [ ] Acceso al panel de email provider (Gmail, Outlook, etc.).

---

## 🔍 Diagnóstico

### Paso 1: Verificar Configuración SMTP
```bash
cd /opt/finanzas-agv
cat .env | grep MAIL
```

Validar:
- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_USE_TLS`

### Paso 2: Test de Conexión SMTP
```bash
source venv/bin/activate
python -c "
from flask_mail import Mail, Message
from app import create_app
app = create_app()
with app.app_context():
    mail = Mail(app)
    msg = Message('Test', sender='noreply@agrovet.com', recipients=['test@test.com'])
    mail.send(msg)
print('Email enviado correctamente')
"
```

---

## 🛠️ Soluciones Comunes

### Error: "SMTPAuthenticationError"
**Causa:** Credenciales incorrectas o contraseña de app no configurada.

**Solución (Gmail):**
1. Habilitar "Contraseñas de aplicaciones" en cuenta Google.
2. Generar nueva contraseña específica para la app.
3. Actualizar `.env`:
```bash
MAIL_PASSWORD=nueva_app_password
```

### Error: "Connection Refused (Port 587)"
**Causa:** Firewall bloqueando puerto SMTP.

**Solución:**
```bash
# Abrir puerto
sudo ufw allow 587/tcp
sudo systemctl restart finanzas-agv
```

### Error: "Emails en Cola sin Enviar"
**Causa:** Worker de correos detenido.

**Solución:**
```bash
# Si usas Celery
sudo systemctl restart celery-worker
sudo systemctl status celery-worker
```

---

## 📚 Referencias
- [Flask-Mail Documentation](https://pythonhosted.org/Flask-Mail/)
- Ver decisiones arquitectónicas en [Índice de ADRs](../adrs/index_adrs.md)

