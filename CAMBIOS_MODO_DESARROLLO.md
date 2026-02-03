# 🔧 Implementación de Modo Desarrollo para Correos

## 📝 Resumen

Se ha implementado un **Modo Desarrollo** que redirige automáticamente todos los correos electrónicos a un email de prueba (`josemontero2415@gmail.com`) durante el desarrollo, evitando envíos accidentales a clientes reales.

## 🎯 Objetivo

Permitir probar el flujo completo de envío de correos de letras sin afectar a los clientes reales, manteniendo la seguridad y trazabilidad del sistema.

## ✅ Cambios Realizados

### 1. Backend (Flask)

#### `config.py`
- ✅ Agregadas variables de configuración:
  - `DEV_EMAIL_MODE`: Activa/desactiva el modo desarrollo
  - `DEV_EMAIL_RECIPIENT`: Email de prueba donde se redirigen los correos
- ✅ Configuración por defecto:
  - **Development**: `DEV_EMAIL_MODE=True` (activado)
  - **Production**: `DEV_EMAIL_MODE=False` (desactivado)

#### `app/emails/email_service.py`
- ✅ Modificado método `send_acceptance_reminders()`:
  - Detecta si está en modo desarrollo
  - Redirige correos al email de prueba
  - Agrega prefijo `[DEV - Original: email@cliente.com]` al asunto
  - Mantiene logs con el destinatario original para auditoría
  - Muestra mensajes claros en consola sobre la redirección

### 2. Frontend (Next.js)

#### `frontend/app/letters/page.tsx`
- ✅ **Banner de Advertencia**: 
  - Muestra un banner amarillo visible en la parte superior
  - Indica claramente que el modo desarrollo está activo
  - Muestra el email de prueba donde llegarán los correos

- ✅ **Confirmación de Envío**:
  - Diálogo de confirmación antes de enviar correos
  - Informa al usuario que los correos irán al email de prueba
  - Muestra la cantidad de correos que se enviarán

- ✅ **Mensaje de Éxito**:
  - Mensaje diferenciado para modo desarrollo
  - Confirma que los correos fueron enviados al email de prueba

### 3. Documentación

#### `docs/MODO_DESARROLLO_CORREOS.md`
- ✅ Documentación completa del modo desarrollo
- ✅ Instrucciones de configuración
- ✅ Guía de uso y pruebas
- ✅ Solución de problemas comunes
- ✅ Ejemplos de configuración

## 🚀 Cómo Usar

### Configuración Rápida

1. **Edita tu archivo `.env.desarrollo`**:
```bash
# Activar modo desarrollo
DEV_EMAIL_MODE=True

# Email de prueba
DEV_EMAIL_RECIPIENT=josemontero2415@gmail.com
```

2. **Reinicia el servidor Flask**:
```bash
python run.py
```

3. **Inicia el frontend**:
```bash
cd frontend
npm run dev
```

4. **Prueba el envío**:
   - Ve a http://localhost:3000/letters
   - Verás el banner amarillo de modo desarrollo
   - Selecciona letras y haz clic en "Enviar Correos"
   - Confirma el envío
   - Revisa tu email `josemontero2415@gmail.com`

## 📧 Ejemplo de Correo Recibido

Cuando envíes correos en modo desarrollo, recibirás emails con:

**Asunto:**
```
[DEV - Original: cliente@agrovet.com] Letras Pendientes de Firma - Agrovet S.A.
```

**Destinatario:**
```
josemontero2415@gmail.com
```

**Contenido:**
- El cuerpo del correo será exactamente igual al que recibiría el cliente
- Podrás ver todas las letras y su información
- El formato será el mismo que en producción

## 🔍 Verificación en Logs

En la consola del backend Flask verás:

```bash
[DEV MODE] Email redirigido de cliente1@agrovet.com a josemontero2415@gmail.com
[DEV MODE] Email redirigido de cliente2@example.com a josemontero2415@gmail.com
[OK] Email de aceptación enviado
```

## ⚠️ Importante para Producción

Antes de desplegar a producción, asegúrate de:

1. ✅ Configurar `DEV_EMAIL_MODE=False` en `.env.produccion`
2. ✅ Verificar que la configuración SMTP de producción sea correcta
3. ✅ Probar con un correo de prueba antes de enviar masivamente
4. ✅ Revisar los logs para confirmar que no hay redirecciones

## 🎨 Interfaz Visual

### Banner de Modo Desarrollo
```
┌─────────────────────────────────────────────────────┐
│ 🔧 MODO DESARROLLO ACTIVADO                         │
│ Todos los correos se enviarán a:                    │
│ josemontero2415@gmail.com                           │
└─────────────────────────────────────────────────────┘
```

### Diálogo de Confirmación
```
🔧 MODO DESARROLLO ACTIVADO

Todos los correos se enviarán a: josemontero2415@gmail.com

¿Deseas continuar con el envío de 5 correos de prueba?

[Cancelar]  [Aceptar]
```

### Mensaje de Éxito
```
✅ MODO DESARROLLO

Se enviaron 5 correos de prueba a josemontero2415@gmail.com
```

## 📊 Flujo de Funcionamiento

```
Usuario selecciona letras
         ↓
Banner muestra modo desarrollo activo
         ↓
Usuario hace clic en "Enviar Correos"
         ↓
Aparece diálogo de confirmación
         ↓
Usuario confirma envío
         ↓
Frontend envía petición al backend
         ↓
Backend detecta DEV_EMAIL_MODE=True
         ↓
Backend redirige correos a josemontero2415@gmail.com
         ↓
Backend registra en logs el email original
         ↓
Correos se envían al email de prueba
         ↓
Usuario recibe confirmación en frontend
         ↓
Usuario verifica correos en josemontero2415@gmail.com
```

## 🧪 Testing

### Checklist de Pruebas

- [ ] Banner de modo desarrollo visible en la página
- [ ] Diálogo de confirmación aparece al enviar
- [ ] Correos llegan a josemontero2415@gmail.com
- [ ] Asunto incluye prefijo `[DEV - Original: ...]`
- [ ] Logs muestran redirección correcta
- [ ] Contenido del correo es correcto
- [ ] Múltiples correos se envían correctamente
- [ ] Mensaje de éxito se muestra correctamente

## 📁 Archivos Modificados

```
config.py                              ← Configuración de variables
app/emails/email_service.py           ← Lógica de redirección
frontend/app/letters/page.tsx         ← UI y confirmaciones
docs/MODO_DESARROLLO_CORREOS.md       ← Documentación completa
CAMBIOS_MODO_DESARROLLO.md            ← Este archivo
```

## 🔗 Enlaces Útiles

- [Documentación completa](docs/MODO_DESARROLLO_CORREOS.md)
- [Configuración de Gmail](docs/MODO_DESARROLLO_CORREOS.md#-configuración-de-gmail-para-desarrollo)
- [Solución de problemas](docs/MODO_DESARROLLO_CORREOS.md#-solución-de-problemas)

## 👤 Contacto

Para dudas o problemas con esta funcionalidad:
- Email: josemontero2415@gmail.com
- Proyecto: Finanzas AGV - Sistema de Gestión de Letras

---

**Fecha de implementación**: 19 de Enero, 2026
**Versión**: 1.0.0
**Estado**: ✅ Implementado y Documentado
