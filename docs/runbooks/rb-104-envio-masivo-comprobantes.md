# RB-104: Envío Masivo de Comprobantes de Pago a Proveedores

**ID:** RB-104  
**Última Actualización:** 2025-11-25  
**Responsable:** José Montero  
**Estado:** 🔴 Pendiente de Implementación  

## 🎯 Objetivo

Enviar de forma masiva y automatizada los comprobantes de pago (constancias bancarias) a los proveedores al finalizar el día, reemplazando el proceso manual actual.

## 📋 Prerrequisitos

- [ ] Sistema de adjuntos de constancias bancarias implementado (ver [ADR-003](../adrs/0003-estrategia-envio-correos.md))
- [ ] Acceso al servidor de correos SMTP
- [ ] Conexión con ODU para obtener datos de pagos y proveedores
- [ ] Lista de proveedores con correos electrónicos válidos

## 👣 Pasos de Ejecución (Diseñado)

> ⚠️ **NOTA:** Este runbook está en estado de diseño. La implementación está pendiente según [Reporte de Estado de Proyectos](../reporte-estado-proyectos.md).

### 1. Validar Pagos del Día

```bash
# En el servidor de la aplicación
cd /opt/finanzas-agv
source venv/bin/activate
python -m app.scripts.validate_daily_payments --date $(date +%Y-%m-%d)
```

**Salida esperada:**
```
✅ 15 pagos registrados hoy
✅ 12 pagos tienen constancia bancaria adjunta
⚠️  3 pagos sin constancia (IDs: 1234, 1235, 1236)
```

### 2. Revisar Pagos sin Constancia

Si hay pagos sin constancia adjunta:
1. Validar con Tesorería si son pagos válidos
2. Solicitar adjuntar las constancias faltantes
3. Re-ejecutar validación

### 3. Generar Correos Masivos

```bash
python -m app.scripts.send_payment_notifications \
  --date $(date +%Y-%m-%d) \
  --template "comprobante_pago" \
  --dry-run
```

**Parámetros:**
- `--date`: Fecha de pagos a procesar
- `--template`: Plantilla de correo a usar
- `--dry-run`: Solo muestra preview sin enviar (remover para envío real)

**Preview esperado:**
```
📧 Correo 1/12
Para: proveedor1@example.com
Asunto: Comprobante de Pago - Factura F001-00123
Adjuntos: constancia_123456.pdf (245 KB)
---
Estimado proveedor...
[Preview del cuerpo del correo]
```

### 4. Enviar Correos (Producción)

```bash
# Quitar --dry-run para envío real
python -m app.scripts.send_payment_notifications \
  --date $(date +%Y-%m-%d) \
  --template "comprobante_pago"
```

**Confirmación:**
```
✅ 12/12 correos enviados exitosamente
📊 Resumen:
   - Enviados: 12
   - Fallidos: 0
   - Tiempo total: 45s
```

### 5. Verificar Logs de Envío

```bash
tail -f /var/log/finanzas-agv/email.log
```

Verificar que no haya errores tipo:
- ❌ SMTP connection refused
- ❌ Invalid email address
- ❌ Attachment size exceeded

## 🔍 Troubleshooting

### Problema: Correo no se envía

**Síntomas:**
- Error "SMTP connection failed"

**Solución:**
1. Verificar configuración SMTP en `config.py`:
   ```python
   MAIL_SERVER = 'smtp.gmail.com'
   MAIL_PORT = 587
   MAIL_USE_TLS = True
   ```
2. Validar credenciales:
   ```bash
   echo $MAIL_USERNAME
   echo $MAIL_PASSWORD
   ```
3. Consultar [RB-102: Fallas en Envío de Correos](rb-102-email-failure.md)

### Problema: Constancia bancaria no se adjunta

**Síntomas:**
- Correo se envía pero sin adjunto
- Error "File not found"

**Solución:**
1. Verificar ruta de almacenamiento de constancias:
   ```bash
   ls -lh /opt/finanzas-agv/storage/constancias/2025-11-25/
   ```
2. Validar permisos del archivo:
   ```bash
   chmod 644 /opt/finanzas-agv/storage/constancias/*.pdf
   ```

### Problema: Proveedor no tiene correo registrado

**Síntomas:**
- Warning "Proveedor sin correo electrónico"

**Solución:**
1. Consultar con Melissa Román para obtener lista de proveedores activos
2. Actualizar en ODU el correo del proveedor
3. Como workaround temporal, enviar manualmente a:
   ```
   cobranzas@agrovetmarket.com (con copia a proveedor)
   ```

## 📊 KPIs de Monitoreo

| Métrica | Valor Esperado | ¿Qué hacer si falla? |
| :--- | :--- | :--- |
| **Tasa de envío exitoso** | > 95% | Revisar logs, validar SMTP |
| **Tiempo de ejecución** | < 2 minutos | Optimizar script, revisar red |
| **Proveedores sin correo** | < 5% | Coordinación con Melissa Román |

## 📅 Tareas Recurrentes

- **Diaria (17:00):** Ejecutar script de envío masivo (automatizar con cron)
- **Semanal:** Revisar lista de proveedores sin correo y solicitar actualización
- **Mensual:** Validar que plantilla de correo siga vigente (revisar con Angie/Marilia)

## 🚧 Tareas Pendientes (Para Implementación)

- [ ] Desarrollar script `send_payment_notifications.py`
- [ ] Definir template de correo con Angie y Marilia
- [ ] Implementar sistema de almacenamiento de constancias (cloud o servidor)
- [ ] Configurar cron job para ejecución diaria automática
- [ ] Crear dashboard de monitoreo de envíos (opcional)

## 🔗 Referencias

- [ADR-003: Estrategia de Envío Masivo de Correos](../adrs/0003-estrategia-envio-correos.md)
- [RB-102: Fallas en Envío de Correos](rb-102-email-failure.md)
- [Código Fuente - Servicio de Emails](../../app/emails/email_service.py)
- [Reporte de Estado de Proyectos](../reporte-estado-proyectos.md)
- [Notas de Reunión - 13 Oct 2025](../../../Downloads/Levante%20de%20Información%20y%20Procesos%20-%20Tesoreria%20-%202025_10_13%2015_56%20GMT-05_00%20-%20Notas%20de%20Gemini.txt)

## 📞 Contacto

**Usuarios solicitantes:**
- Angie Gomero (Tesorería)
- Marilia Tinoco (Cuentas por Pagar)

**Escalamiento:**
- José Montero (Desarrollo)
- Teodoro Balarezo (Jefe de Proyectos)

