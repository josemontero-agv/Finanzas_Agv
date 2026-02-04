# RB-001: Despliegue en Producción

**ID:** RB-001
**Última Actualización:** 2025-11-20
**Responsable:** DevOps / Tech Lead

## 🎯 Objetivo
Desplegar una nueva versión del backend y frontend en el servidor de producción minimizando el tiempo de inactividad.

## 📋 Prerrequisitos
- [ ] Acceso SSH al servidor de producción.
- [ ] La rama `main` debe haber pasado todos los tests en CI.
- [ ] Backup reciente de la base de datos (ver [RB-002](rb-002-db-management.md)).

## 👣 Pasos de Ejecución

### 1. Acceder al Servidor
```bash
ssh user@produccion-server
cd /opt/finanzas-agv
```

### 2. Actualizar Código
```bash
git pull origin main
```

### 3. Actualizar Dependencias (Backend)
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Aplicar Migraciones de Base de Datos
```bash
flask db upgrade
```
> ⚠️ **Atención:** Si hay errores en la migración, ejecutar `flask db downgrade` y revisar logs.

### 5. Reiniciar Servicios
```bash
sudo systemctl restart finanzas-agv
sudo systemctl status finanzas-agv
```

### 6. Verificación (Smoke Test)
1.  Entrar a `https://finanzas.agrovetmarket.com`
2.  Hacer login.
3.  Verificar que el Dashboard cargue datos recientes.

## 🔙 Plan de Rollback
Si algo falla críticamente:
1.  Revertir código: `git reset --hard HEAD@{1}`
2.  Revertir dependencias: `pip install -r requirements.txt`
3.  Reiniciar servicio: `sudo systemctl restart finanzas-agv`

