# Modo Desarrollo para Envío de Correos

## 📋 Descripción

El **Modo Desarrollo de Correos** es una funcionalidad que permite probar el envío de correos sin afectar a los clientes reales. Cuando está activado, todos los correos se redirigen automáticamente a un email de prueba.

## 🔧 Configuración

### Variables de Entorno

Agrega estas variables en tu archivo `.env.desarrollo`:

```bash
# Activar modo desarrollo (True/False)
DEV_EMAIL_MODE=True

# Email de prueba donde se recibirán todos los correos
DEV_EMAIL_RECIPIENT=josemontero2415@gmail.com
```

### Comportamiento por Entorno

| Entorno | DEV_EMAIL_MODE por defecto | Descripción |
|---------|---------------------------|-------------|
| **Development** | `True` | Activado automáticamente, todos los correos van al email de prueba |
| **Production** | `False` | Desactivado, los correos se envían a los destinatarios reales |
| **Testing** | `False` | Desactivado para tests unitarios |

## 🚀 Uso

### En el Frontend (Next.js)

Cuando envías correos desde la página de Letras:

1. **Banner de Advertencia**: Se muestra un banner amarillo en la parte superior indicando que el modo desarrollo está activo
2. **Confirmación**: Al hacer clic en "Enviar Correos", aparece un diálogo de confirmación indicando que los correos irán a `josemontero2415@gmail.com`
3. **Mensaje de Éxito**: Después del envío, se muestra un mensaje confirmando que los correos fueron enviados al email de prueba

### En el Backend (Flask)

El servicio de emails (`EmailService`) automáticamente:

1. **Detecta el modo**: Lee la configuración `DEV_EMAIL_MODE` de Flask
2. **Redirige correos**: Cambia el destinatario real por el email de prueba
3. **Modifica el asunto**: Agrega `[DEV - Original: email@cliente.com]` al inicio del asunto
4. **Registra en logs**: Guarda el email original en los logs para auditoría

### Ejemplo de Correo en Modo Desarrollo

**Asunto Original:**
```
Letras Pendientes de Firma - Agrovet S.A.
```

**Asunto en Modo Desarrollo:**
```
[DEV - Original: cliente@agrovet.com] Letras Pendientes de Firma - Agrovet S.A.
```

**Destinatario:**
- Original: `cliente@agrovet.com`
- En desarrollo: `josemontero2415@gmail.com`

## 📝 Logs del Sistema

Los logs mostrarán información clara sobre el modo desarrollo:

```bash
[DEV MODE] Email redirigido de cliente@agrovet.com a josemontero2415@gmail.com
```

En modo producción:
```bash
[OK] Email de aceptación enviado a cliente@agrovet.com
```

## ⚠️ Consideraciones Importantes

### ✅ Ventajas

- **Seguridad**: No se envían correos accidentales a clientes reales durante desarrollo
- **Testing**: Puedes probar el flujo completo de envío de correos
- **Auditoría**: Los logs mantienen registro del destinatario original
- **Flexibilidad**: Fácil de activar/desactivar con una variable de entorno

### ⚠️ Precauciones

1. **Producción**: Asegúrate de que `DEV_EMAIL_MODE=False` en producción
2. **Email válido**: Verifica que `DEV_EMAIL_RECIPIENT` sea un email válido y accesible
3. **Configuración SMTP**: El modo desarrollo requiere configuración SMTP válida para enviar correos reales
4. **Logs**: Revisa los logs para confirmar que los correos se están redirigiendo correctamente

## 🧪 Pruebas

### Probar el Envío de Correos

1. Asegúrate de que `DEV_EMAIL_MODE=True` en `.env.desarrollo`
2. Inicia el backend Flask: `python run.py`
3. Inicia el frontend Next.js: `cd frontend && npm run dev`
4. Navega a la página de Letras: `http://localhost:3000/letters`
5. Selecciona algunas letras
6. Haz clic en "Previsualizar" y luego "Enviar Correos"
7. Confirma el envío en el diálogo
8. Revisa tu email `josemontero2415@gmail.com` para verificar la recepción

### Verificar Logs

```bash
# En la consola del backend Flask verás:
[DEV MODE] Email redirigido de cliente1@example.com a josemontero2415@gmail.com
[DEV MODE] Email redirigido de cliente2@example.com a josemontero2415@gmail.com
```

## 🔄 Cambiar a Modo Producción

Para desactivar el modo desarrollo y enviar correos a destinatarios reales:

1. Edita `.env.produccion`:
```bash
DEV_EMAIL_MODE=False
```

2. O elimina la variable (por defecto es False en producción)

3. Reinicia el servidor Flask

4. Los correos ahora se enviarán a los clientes reales

## 📧 Configuración de Gmail para Desarrollo

Para que los correos se envíen correctamente desde tu cuenta de Gmail:

1. **Habilita la verificación en 2 pasos** en tu cuenta de Google
2. **Genera una contraseña de aplicación**:
   - Ve a: https://myaccount.google.com/apppasswords
   - Genera una contraseña para "Correo"
   - Usa esa contraseña en `MAIL_PASSWORD`

3. **Configura las variables**:
```bash
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-contraseña-de-aplicacion-de-16-digitos
```

## 🐛 Solución de Problemas

### Los correos no llegan

1. Verifica que `DEV_EMAIL_MODE=True` esté configurado
2. Revisa los logs del backend para ver si hay errores
3. Confirma que la configuración SMTP sea correcta
4. Verifica que `josemontero2415@gmail.com` sea accesible

### Los correos van a clientes reales en desarrollo

1. Verifica que estés usando el archivo `.env.desarrollo`
2. Confirma que `DEV_EMAIL_MODE=True` (con mayúscula en True)
3. Reinicia el servidor Flask después de cambiar la configuración

### El banner no aparece en el frontend

1. Verifica que `NODE_ENV=development` en el frontend
2. Reinicia el servidor de Next.js
3. Limpia la caché del navegador

## 📚 Referencias

- Configuración: `config.py`
- Servicio de Emails: `app/emails/email_service.py`
- Frontend: `frontend/app/letters/page.tsx`
- Rutas de Letras: `app/letters/routes.py`
