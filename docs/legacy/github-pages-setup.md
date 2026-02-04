# 🚀 Guía de Activación de GitHub Pages

Esta guía te ayudará a activar GitHub Pages para publicar tu documentación automáticamente.

---

## 📋 Prerrequisitos

- ✅ Repositorio GitHub creado
- ✅ Archivos `.github/workflows/` en el repo
- ✅ Documentación en carpeta `docs/`
- ✅ Archivo `mkdocs.yml` configurado

---

## 🔧 Paso 1: Configurar GitHub Pages

### 1.1 Acceder a Configuración del Repositorio

1. Ve a tu repositorio en GitHub: `https://github.com/<tu-usuario>/Finanzas_Agv`
2. Haz clic en **"Settings"** (⚙️ Configuración)
3. En el menú lateral izquierdo, busca **"Pages"**

### 1.2 Configurar Source (Fuente)

En la sección **"Build and deployment"**:

1. **Source:** Selecciona **"Deploy from a branch"**
2. **Branch:** Selecciona **`gh-pages`** ← *Importante: esta rama se crea automáticamente*
3. **Folder:** Deja **`/ (root)`**
4. Haz clic en **"Save"**

![Configuración GitHub Pages](https://docs.github.com/assets/cb-47267/images/help/pages/select-branch-and-folder.png)

---

## 🎯 Paso 2: Primer Despliegue

### Opción A: Despliegue Manual desde Terminal

Ejecuta estos comandos en tu terminal local:

```bash
# 1. Asegúrate de estar en la carpeta del proyecto
cd "C:\Users\jmontero\Desktop\GitHub Proyectos_AGV\Finanzas_Agv"

# 2. Instala dependencias si no las tienes
pip install mkdocs mkdocs-material

# 3. Despliega manualmente
mkdocs gh-deploy --force --clean --verbose
```

**Salida esperada:**
```
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: site
INFO    -  Copying 'site' to 'gh-pages' branch and pushing to GitHub
INFO    -  Your documentation should shortly be available at:
            https://<tu-usuario>.github.io/Finanzas_Agv/
```

### Opción B: Despliegue Automático via Git Push

```bash
# 1. Haz cualquier cambio en docs/
echo "# Test" >> docs/test.md

# 2. Commit y push a main
git add docs/test.md
git commit -m "docs: trigger initial deployment"
git push origin main
```

El workflow `.github/workflows/docs-cd.yml` se ejecutará automáticamente y desplegará.

---

## 📊 Paso 3: Verificar Despliegue

### 3.1 Ver el Workflow en Acción

1. Ve a tu repositorio en GitHub
2. Haz clic en la pestaña **"Actions"**
3. Verás el workflow **"🚀 CD - Despliegue de Documentación"** ejecutándose

![GitHub Actions](https://docs.github.com/assets/cb-33882/images/help/repository/actions-tab.png)

### 3.2 Revisar Logs

Haz clic en el workflow en ejecución para ver:
- ✅ Checkout del código
- ✅ Configuración de Python
- ✅ Instalación de dependencias
- ✅ Despliegue a gh-pages

**Si todo está bien, verás:**
```
✅ Deploy - 📦 Desplegar a GitHub Pages (42s)
```

### 3.3 Acceder a la Documentación Publicada

Una vez completado el despliegue (1-2 minutos), tu documentación estará disponible en:

```
https://<tu-usuario>.github.io/Finanzas_Agv/
```

**Ejemplo real:**
```
https://josemontero-agv.github.io/Finanzas_Agv/
```

---

## 🔍 Paso 4: Verificar Configuración

### 4.1 Verificar que la rama `gh-pages` existe

```bash
# Ver todas las ramas remotas
git fetch
git branch -r
```

Deberías ver:
```
origin/main
origin/gh-pages  ← Esta rama fue creada automáticamente
```

### 4.2 Inspeccionar contenido de gh-pages

```bash
# Ver qué hay en la rama gh-pages
git checkout gh-pages
ls
```

Verás solo HTML compilado:
```
404.html
assets/
index.html
search/
sitemap.xml
...
```

**No verás archivos `.md` porque MkDocs los convirtió a HTML.**

---

## 🛠️ Comandos Útiles para el Terminal

### Opción A: Usar el Script de Activación (Recomendado)

**Windows (PowerShell):**
```powershell
cd "C:\Users\jmontero\Desktop\GitHub Proyectos_AGV\Finanzas_Agv"
.\activate-docs.ps1
```

**Linux/Mac:**
```bash
cd ~/Finanzas_Agv
chmod +x activate-docs.sh
./activate-docs.sh
```

El script te presenta un menú interactivo con opciones:
1. 🌐 Servir localmente
2. 🔨 Construir sitio
3. 🚀 Desplegar a GitHub Pages
4. ✅ Validar construcción

### Opción B: Comandos Manuales

#### Ver documentación localmente:
```bash
cd "C:\Users\jmontero\Desktop\GitHub Proyectos_AGV\Finanzas_Agv"
mkdocs serve
```
Abre: `http://127.0.0.1:8000`

#### Construir sin desplegar (test):
```bash
mkdocs build --strict
```

#### Desplegar manualmente a GitHub Pages:
```bash
mkdocs gh-deploy --force --clean
```

#### Ver diferencias antes de desplegar:
```bash
mkdocs build
git diff gh-pages
```

---

## ⚠️ Troubleshooting

### Problema: "404 - There isn't a GitHub Pages site here"

**Causa:** GitHub Pages aún no terminó de activarse.

**Solución:**
1. Espera 2-3 minutos después del primer despliegue
2. Verifica en Settings → Pages que dice: **"Your site is live at..."**
3. Fuerza recarga en el navegador (Ctrl + F5)

---

### Problema: Workflow falla con "Permission denied"

**Causa:** GitHub Actions no tiene permisos para escribir en el repo.

**Solución:**
1. Ve a **Settings → Actions → General**
2. En **"Workflow permissions"**, selecciona:
   - ✅ **"Read and write permissions"**
3. Guarda cambios
4. Re-ejecuta el workflow

---

### Problema: "Page build failed"

**Causa:** Error en la construcción del sitio.

**Solución:**
1. Ve a **Actions** y revisa los logs del workflow fallido
2. Ejecuta localmente: `mkdocs build --strict`
3. Corrige errores mostrados
4. Haz nuevo commit y push

---

### Problema: Cambios no se reflejan en el sitio

**Causa:** Caché del navegador.

**Solución:**
1. Limpia caché: Ctrl + Shift + Del
2. Fuerza recarga: Ctrl + F5
3. Verifica timestamp en Settings → Pages (última actualización)

---

## 🎉 Configuración Completada

Una vez que veas tu documentación en `https://<usuario>.github.io/Finanzas_Agv/`:

✅ **Workflow CI validará** cada Pull Request automáticamente  
✅ **Workflow CD desplegará** cada merge a `main` automáticamente  
✅ **Documentación siempre actualizada** sin intervención manual  

---

## 📚 Referencias

- [Documentación oficial GitHub Pages](https://docs.github.com/en/pages)
- [MkDocs Deployment Guide](https://www.mkdocs.org/user-guide/deploying-your-docs/)
- [GitHub Actions para MkDocs](https://github.com/marketplace/actions/deploy-mkdocs)
- [Flujo de Automatización](automatizacion-cicd.md) - Detalles del CI/CD

---

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs en **Actions**
2. Ejecuta `mkdocs build --strict` localmente
3. Consulta la [Guía de Contribución](CONTRIBUTING.md)
4. Abre un issue en el repositorio

