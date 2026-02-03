# 🎨 Paleta de Colores - Finanzas AGV Next.js

## 🎯 Colores Corporativos Principales

### Color Primario (Morado AGV)
```css
--primary: #714B67
--secondary: #875A7B
```

**Uso:**
- Sidebar background
- Botones principales
- Badges de estado "default"
- Iconos destacados

---

## 📊 Colores por Módulo

### 🔵 Cobranzas (Azul)
```css
Color principal: #3b82f6 (blue-500)
Color hover: #2563eb (blue-600)
Background: from-blue-500 to-blue-600
```

**Elementos:**
- Card del Dashboard: Gradiente azul
- KPI Cards: Borde azul, icono azul
- Badges: Variante azul

### 🟢 Tesorería (Verde)
```css
Color principal: #10b981 (green-500)
Color hover: #059669 (green-600)
Background: from-green-500 to-green-600
```

**Elementos:**
- Card del Dashboard: Gradiente verde
- KPI "Monto Total": Verde
- Iconos de dinero: Verde

### 🟣 Letras (Morado Corporativo)
```css
Color principal: #714B67
Color hover: #875A7B
Background: from-[#714B67] to-[#875A7B]
```

**Elementos:**
- Card del Dashboard: Gradiente morado
- KPI Cards: Borde morado, icono morado
- Botones toggle: Morado cuando activo

### 🔴 Alertas y Vencimientos (Rojo)
```css
Color principal: #ef4444 (red-500)
Color hover: #dc2626 (red-600)
```

**Uso:**
- Saldo pendiente
- Facturas vencidas
- Días vencidos > 0
- Badges "destructive"

### 🟠 Advertencias (Naranja)
```css
Color principal: #f59e0b (orange-500)
Color hover: #d97706 (orange-600)
```

**Uso:**
- Facturas próximas a vencer
- Alertas de atención
- Estados intermedios

---

## 🎨 Componentes UI

### Sidebar
```css
Background: #714B67 (morado corporativo)
Hover: #875A7B (morado claro)
Text: white
Border separator: purple-400/30
```

### KPI Cards
```css
Background: white
Border: color-100 (según módulo)
Shadow: sm → md en hover
Icon background: color-100
Icon color: color-600
```

**Ejemplo Tesorería:**
```tsx
<div className="bg-white p-6 rounded-lg border border-purple-100 shadow-sm">
  <div className="bg-purple-100 p-3 rounded-lg">
    <Icon className="h-6 w-6 text-[#714B67]" />
  </div>
</div>
```

### Badges
```css
default: bg-[#714B67] (morado corporativo)
secondary: bg-slate-500
destructive: bg-red-500
```

### Botones
```css
Primary: bg-[#714B67] hover:bg-[#875A7B]
Outline: border con hover suave
Secondary: bg-slate-200
```

---

## 🌈 Gradientes Aplicados

### Dashboard Cards
```css
Cobranzas: from-blue-500 to-blue-600
Tesorería: from-green-500 to-green-600
Letras: from-[#714B67] to-[#875A7B]
Analytics: from-slate-400 to-slate-500
```

### Banner Informativo
```css
from-[#714B67] to-[#875A7B]
```

### Background General
```css
from-slate-50 to-purple-50
```

---

## 📋 Tabla de Referencia Rápida

| Elemento | Color | Código Hex |
|----------|-------|------------|
| **Sidebar** | Morado AGV | #714B67 |
| **Sidebar Hover** | Morado Claro | #875A7B |
| **Cobranzas** | Azul | #3b82f6 |
| **Tesorería** | Verde | #10b981 |
| **Letras** | Morado AGV | #714B67 |
| **Vencido** | Rojo | #ef4444 |
| **Vigente** | Verde | #10b981 |
| **Advertencia** | Naranja | #f59e0b |
| **Background** | Gris Claro | #f8fafc |

---

## 🎯 Consistencia Visual

### Estados de Deuda
- **VIGENTE**: Badge verde (#10b981)
- **VENCIDO**: Badge rojo (#ef4444)
- **Días > 0**: Texto rojo y negrita
- **Días <= 0**: Texto verde

### Antigüedad
- **Vigente**: Badge default (morado)
- **Atraso Corto**: Badge secondary (gris)
- **Atraso Medio/Prolongado**: Badge destructive (rojo)
- **Cobranza Judicial**: Badge destructive (rojo)

---

## 🔧 Cómo Cambiar Colores

### Para cambiar el color corporativo principal:

1. Edita `frontend/app/globals.css`:
```css
--primary: #TU_COLOR_AQUI;
--secondary: #TU_COLOR_SECUNDARIO;
```

2. Actualiza el Sidebar en `frontend/components/sidebar.tsx`:
```tsx
className="w-64 bg-[#TU_COLOR] text-white"
```

3. Actualiza los botones en las páginas:
```tsx
className="bg-[#TU_COLOR] hover:bg-[#TU_COLOR_HOVER]"
```

---

## ✅ Resultado Visual

### Antes (Colores genéricos):
- Sidebar: Gris oscuro (#1e293b)
- Cards: Sin color distintivo
- Botones: Azul genérico

### Después (Paleta corporativa):
- ✅ Sidebar: Morado AGV (#714B67)
- ✅ Cards: Gradientes por módulo
- ✅ Botones: Morado corporativo
- ✅ KPIs: Iconos con background de color
- ✅ Badges: Colores según estado

---

**¡La paleta de colores ahora es 100% profesional y coherente con la identidad de Finanzas AGV!** 🎨
