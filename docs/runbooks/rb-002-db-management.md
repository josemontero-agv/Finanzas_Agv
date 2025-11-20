# RB-002: Gestión de Base de Datos

**ID:** RB-002
**Última Actualización:** 2025-11-20
**Responsable:** DBA / DevOps

## 🎯 Objetivo
Realizar operaciones seguras de backup, restore y migraciones de la base de datos del sistema Finanzas AGV.

## 📋 Prerrequisitos
- [ ] Acceso al servidor de base de datos.
- [ ] Credenciales con permisos de administración.
- [ ] Espacio suficiente en disco para backups (mínimo 2GB).

---

## 🔄 Sección 1: Backup de Base de Datos

### Paso 1.1: Conectar al Servidor
```bash
ssh user@db-server
cd /var/backups/finanzas-agv
```

### Paso 1.2: Crear Backup
```bash
# PostgreSQL
pg_dump -U finanzas_user -d finanzas_db -F c -f backup_$(date +%Y%m%d_%H%M%S).dump

# MySQL
mysqldump -u finanzas_user -p finanzas_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Paso 1.3: Verificar Integridad
```bash
ls -lh backup_*.dump
md5sum backup_*.dump > backup_checksums.txt
```

### Paso 1.4: Subir a S3 (Opcional)
```bash
aws s3 cp backup_$(date +%Y%m%d).dump s3://finanzas-backups/
```

---

## 🔙 Sección 2: Restore de Base de Datos

⚠️ **ADVERTENCIA:** Esta operación sobrescribirá los datos existentes.

### Paso 2.1: Detener la Aplicación
```bash
sudo systemctl stop finanzas-agv
```

### Paso 2.2: Restaurar desde Backup
```bash
# PostgreSQL
pg_restore -U finanzas_user -d finanzas_db -c backup_20251120.dump

# MySQL
mysql -u finanzas_user -p finanzas_db < backup_20251120.sql
```

### Paso 2.3: Verificar Datos
```bash
psql -U finanzas_user -d finanzas_db -c "SELECT COUNT(*) FROM invoices;"
```

### Paso 2.4: Reiniciar Aplicación
```bash
sudo systemctl start finanzas-agv
```

---

## 🔧 Sección 3: Aplicar Migraciones

### Paso 3.1: Revisar Migraciones Pendientes
```bash
cd /opt/finanzas-agv
source venv/bin/activate
flask db current
flask db history
```

### Paso 3.2: Crear Backup Preventivo
Ver **Sección 1**.

### Paso 3.3: Ejecutar Migraciones
```bash
flask db upgrade
```

### Paso 3.4: Validar Resultado
```bash
flask db current
# Verificar que la versión coincida con la última migración
```

---

## 🆘 Troubleshooting

### Error: "Permission denied"
**Causa:** Usuario sin permisos suficientes.
**Solución:**
```bash
sudo -u postgres pg_dump ...
```

### Error: "Disk full"
**Causa:** Sin espacio para el backup.
**Solución:**
```bash
# Limpiar backups antiguos (más de 30 días)
find /var/backups/finanzas-agv -name "backup_*.dump" -mtime +30 -delete
```

### Error: "Migration conflict"
**Causa:** Ramas con migraciones paralelas.
**Solución:**
```bash
flask db merge heads
flask db upgrade
```

---

## 📚 Referencias
- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- Ver decisiones arquitectónicas en [Índice de ADRs](../adrs/index_adrs.md)

