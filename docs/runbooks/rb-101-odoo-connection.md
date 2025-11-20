# RB-101: Error de Conexión Odoo

**ID:** RB-101
**Última Actualización:** 2025-11-20
**Responsable:** DevOps / Backend Developer

## 🎯 Objetivo
Diagnosticar y resolver problemas de conexión entre el sistema Finanzas AGV y el ERP Odoo.

## 📋 Prerrequisitos
- [ ] Acceso al servidor de aplicación.
- [ ] Credenciales de Odoo para testing.
- [ ] Acceso a logs del sistema.

---

## 🔍 Diagnóstico

### Paso 1: Verificar Estado del Servicio
```bash
cd /opt/finanzas-agv
source venv/bin/activate
python conectar_odoo.py
```

### Paso 2: Revisar Logs
```bash
tail -f /var/log/finanzas-agv/app.log | grep -i "odoo\|xmlrpc"
```

### Paso 3: Verificar Variables de Entorno
```bash
echo $ODOO_URL
echo $ODOO_DB
echo $ODOO_USER
```

---

## 🛠️ Soluciones Comunes

### Error: "Connection Timeout"
**Causa:** Odoo no responde o firewall bloqueando.

**Solución:**
```bash
# Verificar conectividad
curl -v $ODOO_URL/web/database/selector

# Verificar firewall
sudo ufw status
```

### Error: "Authentication Failed"
**Causa:** Credenciales incorrectas o usuario deshabilitado.

**Solución:**
1. Validar credenciales en interfaz web de Odoo.
2. Actualizar `.env`:
```bash
ODOO_USER=usuario_correcto
ODOO_PASSWORD=nueva_password
```

### Error: "xmlrpc.client.Fault: Access Denied"
**Causa:** Usuario sin permisos API.

**Solución:**
En Odoo, asignar grupo "API Access" al usuario técnico.

---

## 📚 Referencias
- [Documentación Odoo XML-RPC](https://www.odoo.com/documentation/17.0/developer/reference/external_api.html)
- Ver `conectar_odoo.py` para implementación actual

