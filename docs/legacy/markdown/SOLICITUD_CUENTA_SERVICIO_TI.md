# Solicitud de Cuenta de Servicio para Aplicación "Finanzas AGV"

**Fecha:** 03/02/2026
**Solicitante:** Desarrollo / Créditos y Cobranzas
**Asunto:** Creación de cuenta de servicio de correo electrónico institucional

## 1. Recurso Solicitado

Se solicita la creación de la siguiente cuenta de correo electrónico institucional:

- **Dirección sugerida:** `creditosycobranzas@agrovetmarket.com`
- **Tipo:** Cuenta de servicio / Buzón compartido (No nominal)
- **Permisos requeridos:** Acceso SMTP para envío de correos automatizados.

## 2. Justificación Técnica y de Negocio

La aplicación **Finanzas AGV**, utilizada por el equipo de Créditos y Cobranzas para la gestión y envío de letras y estados de cuenta, requiere una cuenta centralizada para el envío de notificaciones por correo electrónico.

### 2.1. Centralización y Escalabilidad
Actualmente, el sistema requeriría que cada uno de los 5 usuarios del equipo configure sus credenciales personales para enviar correos. Esto no es escalable ni operativo, ya que implica compartir contraseñas o reconfigurar el servidor constantemente. Una cuenta de servicio permite una configuración única en el servidor (`.env`), transparente para todos los usuarios.

### 2.2. Seguridad
El uso de cuentas personales (`nombre.apellido@agrovetmarket.com`) en configuraciones de servidores expone credenciales de dominio y mezcla la responsabilidad individual con procesos automáticos. Una cuenta de servicio aísla este riesgo y permite rotar contraseñas sin afectar a usuarios individuales.

### 2.3. Identidad Corporativa
Los clientes reciben correos de cobranza. Es imperativo que el remitente refleje la entidad oficial (**Área de Créditos y Cobranzas**) en lugar de un nombre personal, otorgando mayor formalidad y evitando que los correos sean ignorados o tratados como spam.

### 2.4. Auditoría
Centralizar el envío permite tener una bandeja de "Enviados" común donde el equipo de supervisión puede auditar qué notificaciones han salido del sistema, independientemente de qué usuario operativo disparó la acción desde la interfaz web.

## 3. Configuración Requerida

Para la integración con el sistema, se requieren los siguientes datos una vez creada la cuenta:

- **Servidor SMTP:** (Ej: `smtp.gmail.com` o `smtp.office365.com`)
- **Puerto:** (Ej: `587` TLS)
- **Usuario:** `creditosycobranzas@agrovetmarket.com`
- **Contraseña:** Contraseña de aplicación (App Password) o credencial de servicio.

Agradecemos su atención a esta solicitud para proceder con el despliegue a producción de la herramienta.
