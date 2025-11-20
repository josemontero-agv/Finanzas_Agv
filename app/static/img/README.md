# 📁 Carpeta de Imágenes

## Logo de la Empresa

**Guardar aquí el logo de Agrovet Market:**

### Nombre del archivo:
```
agrovet-market.png
```

### Ubicación completa:
```
Finanzas_Agv/app/static/img/agrovet-market.png
```

### Especificaciones recomendadas:
- **Formato:** PNG (con fondo transparente preferiblemente)
- **Dimensiones recomendadas:** 300x300 px o similar (cuadrado)
- **Peso:** Menor a 500KB
- **Fondo:** Transparente o blanco

### ¿Dónde se usa?
- Página de login (120px de ancho)
- Se puede usar en otras secciones del sistema

### Alternativa si no tienes el logo:
Si no tienes el logo, la aplicación funcionará igual. El logo simplemente no se mostrará (está configurado con `onerror="this.style.display='none'"`).

### Cómo copiar el logo:
1. Localiza tu logo de Agrovet Market
2. Renómbralo a: `agrovet-market.png`
3. Cópialo a: `Finanzas_Agv/app/static/img/`
4. Reinicia la aplicación si está corriendo
5. Refresca el navegador (Ctrl + F5)

---

## Otras Imágenes

Puedes guardar otras imágenes aquí para usar en el sistema:
- Iconos personalizados
- Banners
- Gráficos
- Etc.

Para usarlas en templates:
```html
<img src="{{ url_for('static', filename='img/nombre-archivo.png') }}" alt="Descripción">
```

