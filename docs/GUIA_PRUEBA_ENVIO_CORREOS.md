# 📧 Guía de Prueba: Envío de Correos de Letras

## 🔍 ¿Cómo Funciona el Sistema?

### 1. **Visualización de Datos (Tabla) - SÍ ES NECESARIO**

La tabla muestra todas las letras en estado "Por aceptar" (`to_accept`) con los siguientes campos:

| Campo | Descripción |
|-------|-------------|
| Socio/NIF | RUC del cliente |
| Aceptante | Nombre del cliente |
| Nro.Letra | Número de la letra |
| Planilla/Facturas | Referencias de facturas relacionadas |
| Total firmado | Monto en moneda |
| Origen | Origen de la operación |
| Fecha | Fecha de emisión |
| Fecha vencimiento | Fecha de vencimiento |
| **Estado** | **Calculado: VIGENTE o POR RECUPERAR** |
| Vendedor | Vendedor asignado |
| Ciudad | Ciudad del cliente |
| Referencia | Referencia adicional |

**¿Por qué es necesario mostrar?**
- ✅ Permite seleccionar qué letras enviar
- ✅ Muestra el estado calculado (Lima >4 días = POR RECUPERAR, Provincia >10 días = POR RECUPERAR)
- ✅ Permite revisar antes de enviar
- ✅ Facilita la auditoría visual

### 2. **Proceso de Envío de Correos**

```
Usuario selecciona letras → Click "Enviar" → Backend agrupa por cliente → 
Genera correo HTML → Envía vía Gmail → Registra en auditoría
```

**Detalles del proceso:**

1. **Selección**: Usuario marca checkboxes de letras a enviar
2. **Agrupación**: El sistema agrupa automáticamente por email del cliente
   - Si un cliente tiene 3 letras seleccionadas → 1 correo con las 3 letras
   - Si hay 2 clientes diferentes → 2 correos separados
3. **Generación de correo**: Se crea un HTML con:
   - Saludo personalizado
   - Lista de letras (número, monto, fecha vencimiento)
   - Firma de José Montero
4. **Envío**: Se envía vía Gmail SMTP
5. **Auditoría**: Se registra en `logs/email_audit.db`

### 3. **Contenido del Correo**

El correo que recibe el cliente contiene:

```
Buenas tardes Estimada/o,

Se adjunta las letras para su pronta firma:

• Letra L-2024001 - PEN 15,234.50 - Vence: 2024-12-15
• Letra L-2024002 - PEN 8,900.00 - Vence: 2024-12-20

Por favor responder correo cuando se esté enviando las letras firmadas.

Cordialmente,
José Montero | Asistente de Créditos y Cobranzas
(1) 2300 300 Anexo | +51 965 252 063 | jose.montero@agrovetmarket.com
```

## 🧪 Cómo Hacer una Prueba

### Paso 1: Verificar que la Tabla se Muestra

1. Abre el navegador y ve a: `http://localhost:5000/letters/management`
2. Deberías ver la tabla con letras (datos mock por ahora)
3. Verifica que aparezcan las 13 columnas
4. Verifica que el estado se muestre (VIGENTE o POR RECUPERAR)

**Si la tabla NO se muestra:**
- Abre la consola del navegador (F12)
- Revisa si hay errores en la consola
- Verifica que el endpoint `/api/v1/letters/to-accept` responda correctamente

### Paso 2: Configurar Gmail (Opcional para Prueba)

**Opción A: Prueba sin Gmail (Modo Mock)**
- El sistema funcionará pero solo mostrará en consola
- Los logs se guardarán igual en la base de datos

**Opción B: Prueba con Gmail Real**
1. Ve a: https://myaccount.google.com/security
2. Activa "Verificación en 2 pasos"
3. Genera "Contraseña de aplicación" para "Correo"
4. Agrega en `.env.desarrollo`:
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu_email@gmail.com
MAIL_PASSWORD=xxxx xxxx xxxx xxxx  # Contraseña de aplicación
MAIL_DEFAULT_SENDER=tu_email@gmail.com
```

### Paso 3: Probar el Envío

1. Selecciona algunas letras en la tabla (marca los checkboxes)
2. Verás un contador: "X seleccionadas"
3. Click en "Enviar Recordatorios de Firma"
4. Verás un mensaje de confirmación con los emails destino
5. Confirma el envío
6. Verás un mensaje con resultados (enviados/fallidos)

### Paso 4: Verificar Logs

Los logs se guardan en: `Finanzas_Agv/logs/email_audit.db`

Puedes consultarlos con:
```python
from app.emails.email_logger import EmailLogger
logger = EmailLogger()
logs = logger.get_logs(limit=10)
for log in logs:
    print(f"{log['timestamp']} - {log['recipient_email']} - {log['status']}")
```

O usar el endpoint: `GET /api/v1/emails/logs`

## ❓ Preguntas Frecuentes

**P: ¿Es necesario mostrar la tabla?**
R: **SÍ**, porque:
- Permite seleccionar qué letras enviar
- Muestra el estado calculado
- Facilita la revisión antes de enviar

**P: ¿Qué pasa si la tabla no se muestra?**
R: Verifica:
1. Consola del navegador (F12) para errores
2. Que el endpoint `/api/v1/letters/to-accept` funcione
3. Que el método `get_letters_to_accept()` retorne datos

**P: ¿Los correos se envían automáticamente?**
R: **NO**, se envían manualmente cuando:
- El usuario selecciona letras
- Click en "Enviar Recordatorios de Firma"
- Confirma el envío

**P: ¿Puedo hacer envío automático diario?**
R: **SÍ**, puedes crear un script que:
- Llame a `/api/v1/letters/to-accept`
- Agrupe por cliente
- Llame a `/api/v1/letters/send-acceptance`
- Programarlo con Windows Task Scheduler

## 🔧 Solución de Problemas

**Problema: La tabla está vacía**
- Verifica que `get_letters_to_accept()` retorne datos
- Revisa la consola del navegador
- Verifica el endpoint en: `http://localhost:5000/api/v1/letters/to-accept`

**Problema: Los correos no se envían**
- Verifica configuración SMTP en `.env.desarrollo`
- Revisa logs del servidor Flask
- Verifica que `MAIL_PASSWORD` sea contraseña de aplicación (no la normal)

**Problema: Error al cargar datos**
- Revisa la consola del navegador (F12)
- Verifica que el servidor Flask esté corriendo
- Revisa logs del servidor

