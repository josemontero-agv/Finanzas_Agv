# 🎨 Paleta Uniforme Corporativa - APLICADA

## ✅ Problema Resuelto

**Antes:** Los KPI cards tenían colores diferentes (azul, verde, rojo, naranja) que no mantenían una presentación uniforme.

**Después:** Todos los elementos usan la **paleta corporativa morada** de Finanzas AGV.

---

## 🎨 Paleta Corporativa Única

### Colores Base
```css
Primario:   #714B67  (Morado AGV)
Secundario: #875A7B  (Morado claro)
Terciario:  #9d6f91  (Morado más claro)
```

### Opacidades para Variación
```css
Borde:      color/20  (20% opacidad)
Background: color/10  (10% opacidad)
Hover:      color/80  (80% opacidad)
```

---

## 📊 Aplicación en KPI Cards

### Estructura Uniforme en TODOS los módulos:

```tsx
<div className="bg-white p-6 rounded-lg border border-[#714B67]/20 shadow-sm hover:shadow-md transition-shadow">
  <div className="flex items-center justify-between">
    <div>
      <p className="text-sm font-medium text-slate-600">Título</p>
      <p className="text-2xl font-bold text-[#714B67]">Valor</p>
    </div>
    <div className="bg-[#714B67]/10 p-3 rounded-lg">
      <Icon className="h-6 w-6 text-[#714B67]" />
    </div>
  </div>
</div>
```

### Aplicado en:
- ✅ Tesorería (4 cards)
- ✅ Cobranzas (1 card)
- ✅ Letras (1 card)

---

## 🎯 Variaciones por Card (Mismo módulo)

Para diferenciar cards dentro del mismo módulo sin romper la uniformidad:

### Tesorería - 4 Cards:

**Card 1: Total Facturas**
- Color: `#714B67` (primario)
- Background icon: `#714B67/10`
- Border: `#714B67/20`

**Card 2: Monto Total**
- Color: `#875A7B` (secundario)
- Background icon: `#875A7B/10`
- Border: `#875A7B/20`

**Card 3: Saldo Pendiente**
- Color: `#714B67` (primario)
- Background icon: `#714B67/10`
- Border: `#714B67/20`

**Card 4: Facturas Vencidas**
- Color: `#875A7B` (secundario)
- Background icon: `#875A7B/10`
- Border: `#875A7B/20`

**Resultado:** Alternancia sutil entre primario y secundario, manteniendo la uniformidad.

---

## 🎨 Sidebar - Paleta Corporativa

```tsx
<aside className="w-64 bg-[#714B67] text-white">
  {/* Links con hover morado claro */}
  <Link className="hover:bg-[#875A7B] transition-all hover:pl-4">
    ...
  </Link>
</aside>
```

**Características:**
- Background: Morado corporativo sólido
- Hover: Morado claro con desplazamiento
- Bordes: `purple-400/30` (sutil)
- Texto: Blanco puro

---

## 📱 Dashboard - Cards de Módulos

Todos los cards del dashboard ahora usan gradientes de la paleta morada:

```tsx
// Cobranzas
from-[#714B67] to-[#875A7B]

// Tesorería
from-[#875A7B] to-[#9d6f91]

// Letras
from-[#714B67] to-[#875A7B]

// Analytics (deshabilitado)
from-slate-300 to-slate-400
```

**Efecto:** Hover con `scale-105` (crece ligeramente)

---

## 🔄 Comparación Visual

### ❌ Antes (Colores Mezclados):
```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ 🔵 Azul     │ │ 🟢 Verde    │ │ 🔴 Rojo     │ │ 🟠 Naranja  │
│ Total       │ │ Monto       │ │ Pendiente   │ │ Vencidas    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```
**Problema:** Sin cohesión visual, parece un arcoíris.

### ✅ Después (Paleta Uniforme):
```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ 🟣 Morado   │ │ 🟣 Morado   │ │ 🟣 Morado   │ │ 🟣 Morado   │
│ Total       │ │ Monto       │ │ Pendiente   │ │ Vencidas    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```
**Resultado:** Cohesión visual, profesional, corporativo.

---

## 🎨 Elementos con la Paleta Uniforme

### 1. Sidebar
- ✅ Background: `#714B67`
- ✅ Hover: `#875A7B`
- ✅ Transición suave

### 2. KPI Cards (Todos los módulos)
- ✅ Bordes: `#714B67/20` o `#875A7B/20`
- ✅ Iconos: `#714B67` o `#875A7B`
- ✅ Números: `#714B67` o `#875A7B`
- ✅ Background iconos: `color/10`

### 3. Botones Toggle
- ✅ Activo: `bg-[#714B67]`
- ✅ Hover: `hover:bg-[#875A7B]`

### 4. Cards del Dashboard
- ✅ Gradientes morados
- ✅ Hover con scale
- ✅ Iconos en círculos blancos/20

### 5. Banner Informativo
- ✅ Gradiente: `from-[#714B67] to-[#875A7B]`
- ✅ Cards internos: `bg-white/10`

---

## 📋 Checklist de Uniformidad

- [x] Sidebar usa morado corporativo
- [x] Todos los KPI cards usan morado
- [x] Botones usan morado
- [x] Dashboard cards usan gradientes morados
- [x] Banner usa gradiente morado
- [x] Badges default usan morado
- [x] Sin colores azul/verde/rojo/naranja en UI principal
- [x] Solo rojo para indicadores de error/vencido
- [x] Solo verde para indicadores de éxito/vigente

---

## 🎯 Excepciones Permitidas

### Colores de Estado (Semánticos)
Estos SÍ pueden usar colores diferentes porque tienen significado:

- **Rojo**: Vencido, Error, Crítico
- **Verde**: Vigente, Éxito, Conectado
- **Naranja**: Advertencia, Atención
- **Gris**: Deshabilitado, Neutral

**Uso:**
- Badges de estado (VIGENTE/VENCIDO)
- Días vencidos (rojo si > 0, verde si <= 0)
- Checkmarks en diagnóstico
- Alertas y notificaciones

---

## 🔧 Cómo Mantener la Uniformidad

### Al agregar nuevos KPI cards:
```tsx
// ✅ CORRECTO - Usa la paleta corporativa
<div className="border border-[#714B67]/20">
  <p className="text-[#714B67]">Valor</p>
  <div className="bg-[#714B67]/10">
    <Icon className="text-[#714B67]" />
  </div>
</div>

// ❌ INCORRECTO - No uses colores aleatorios
<div className="border border-blue-100">
  <p className="text-blue-600">Valor</p>
  <div className="bg-blue-100">
    <Icon className="text-blue-600" />
  </div>
</div>
```

### Al agregar nuevos módulos:
1. Usa `#714B67` como color principal
2. Usa `#875A7B` como variación
3. Usa opacidades (`/10`, `/20`) para sutileza
4. Solo usa otros colores para estados semánticos

---

## 📸 Resultado Visual

### Tesorería (Ejemplo)
```
┌─────────────────────────────────────────────────────────┐
│  Cuentas por Pagar                    [🟣 Supabase]    │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 🟣 Total │ │ 🟣 Monto │ │ 🟣 Saldo │ │ 🟣 Venc. │  │
│  │    1,234 │ │  S/ 500K │ │  S/ 250K │ │      45  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
├─────────────────────────────────────────────────────────┤
│  Filtros: [Fecha] [Proveedor] [Estado] [Aplicar]       │
├─────────────────────────────────────────────────────────┤
│  [Tabla con datos...]                                   │
└─────────────────────────────────────────────────────────┘
```

**Todos los elementos morados = Cohesión visual perfecta** ✨

---

## ✅ Archivos Actualizados con Paleta Uniforme

1. ✅ `frontend/app/globals.css` - Variables CSS
2. ✅ `frontend/components/sidebar.tsx` - Sidebar morado
3. ✅ `frontend/app/dashboard/page.tsx` - Cards morados
4. ✅ `frontend/app/treasury/page.tsx` - KPIs morados
5. ✅ `frontend/app/collections/page.tsx` - KPI morado
6. ✅ `frontend/app/letters/page.tsx` - KPI morado
7. ✅ `frontend/app/layout.tsx` - Background sutil

---

**¡La paleta ahora es 100% uniforme y profesional!** 🎨✨
