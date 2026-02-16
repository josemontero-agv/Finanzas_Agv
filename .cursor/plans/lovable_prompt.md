# Prompt para Lovable.dev - Finanzas AGV

**Contexto del Proyecto:**
Estás diseñando y construyendo el frontend para "Finanzas AGV", un dashboard financiero corporativo para la empresa Agrovet Market. El sistema se conecta a un backend existente (Flask/Python) y una base de datos Supabase, pero tu objetivo principal en Lovable es crear una interfaz de usuario (UI) moderna, responsiva y altamente funcional que consuma estos datos.

**Rol:**
Actúa como un Diseñador UI/UX Senior y Desarrollador Frontend experto en React, Tailwind CSS y Shadcn UI.

**Objetivo:**
Crear una aplicación web completa con navegación lateral, modo oscuro/claro y dashboards interactivos para la gestión financiera.

---

## 1. Identidad Visual y Paleta de Colores (Estricto)

El diseño debe reflejar seriedad, confianza y modernidad. Usa la siguiente paleta de colores corporativa extraída del sistema de diseño de AGV:

*   **Color Primario (Primary):** `#714B67` (Un tono púrpura/vino corporativo).
*   **Color Secundario (Secondary):** `#875A7B`.
*   **Fondo (Background - Light):** `#f8fafc` (Slate muy claro).
*   **Fondo (Background - Dark):** `#0a0a0f` (Casi negro, para alto contraste).
*   **Tarjetas (Cards - Light):** `#ffffff` con sombras suaves.
*   **Tarjetas (Cards - Dark):** `#1a1a24` con bordes sutiles (`#2d3748`).
*   **Acentos de Estado:**
    *   Éxito: `#10b981` (Verde esmeralda).
    *   Advertencia: `#f59e0b` (Ámbar).
    *   Error/Destructivo: `#ef4444` (Rojo).

**Tipografía:** Limpia, sans-serif (Inter o similar), con buena legibilidad para tablas de datos densas.

---

## 2. Estructura de Navegación (App Shell)

Implementa un layout persistente con:
1.  **Sidebar Lateral (Izquierda):**
    *   Logo de "Finanzas AGV" en la parte superior.
    *   Menú de navegación con iconos (usa Lucide React):
        *   **Dashboard:** (Icono: LayoutDashboard) - Vista general.
        *   **Cobranzas:** (Icono: Wallet) - Gestión de cuentas por cobrar.
        *   **Tesorería:** (Icono: Landmark) - Gestión de pagos y flujo de caja.
        *   **Letras:** (Icono: FileText) - Gestión de letras de cambio.
        *   **Detracciones:** (Icono: Percent) - Impuestos y retenciones.
        *   **Exportaciones:** (Icono: Globe) - Comercio exterior.
    *   Parte inferior del sidebar:
        *   Toggle de Modo Oscuro/Claro (Sol/Luna).
        *   Perfil de Usuario / Cerrar Sesión (Icono: LogOut).

2.  **Área de Contenido Principal:**
    *   Encabezado con título de la página actual y breadcrumbs.
    *   Espacio amplio para tablas y gráficos.

---

## 3. Requerimientos por Módulo (Funcionalidad)

### A. Login (Autenticación)
*   Diseño minimalista y centrado.
*   Logo de la empresa grande.
*   Campos: Usuario, Contraseña.
*   Botón "Ingresar" con el color primario `#714B67`.
*   Feedback visual de carga y errores.

### B. Dashboard Principal (Home)
*   **KPIs Cards (Tarjetas de Indicadores):**
    *   Total por Cobrar (con indicador de tendencia vs mes anterior).
    *   Total por Pagar.
    *   Saldo en Bancos.
    *   Letras Pendientes.
*   **Gráficos (Usa Recharts o similar):**
    *   Gráfico de barras: Flujo de Caja (Ingresos vs Egresos).
    *   Gráfico de torta: Distribución de deuda por antigüedad.

### C. Módulo de Letras (Ejemplo de Tabla Compleja)
*   Este es un módulo crítico. Necesita una tabla de datos avanzada ("Data Table").
*   **Columnas:** Número de Letra, Aceptante (Cliente), Importe, Moneda, Fecha Vencimiento, Estado (Pendiente, Aceptada, Protestada).
*   **Filtros:**
    *   Buscador por nombre de cliente o número.
    *   Filtro por rango de fechas.
    *   Filtro por estado.
*   **Acciones por fila:** Botón para "Ver Detalle" o "Enviar Correo de Aceptación".

### D. Cobranzas y Tesorería
*   Tablas similares a Letras pero enfocadas en Facturas.
*   Indicadores visuales de "Días de retraso" (semáforo de colores: verde < 0, amarillo 0-30, rojo > 30).

---

## 4. Instrucciones Técnicas y Creativas para Lovable

1.  **Componentes:** Utiliza componentes estilo **Shadcn UI** (Botones, Inputs, Cards, Badges, Dialogs/Modals). Son limpios y profesionales.
2.  **Animaciones:** Agrega transiciones suaves (`framer-motion` si es posible, o CSS transitions) al navegar entre páginas y al hacer hover en tarjetas. Que se sienta "fluido".
3.  **Responsividad:** El sidebar debe colapsarse en móviles a un menú hamburguesa. Las tablas deben tener scroll horizontal en pantallas pequeñas sin romper el layout.
4.  **Conexión de Datos (Simulada para UI):**
    *   Crea interfaces de TypeScript para los datos (ej: `Letter`, `Invoice`, `Partner`).
    *   Usa datos mock (falsos) realistas para poblar las tablas inicialmente, pero estructura el código para que sea fácil conectar `supabase-js` o `axios` después.
5.  **Toque Creativo:**
    *   Sorpréndeme con el diseño de las "KPI Cards". No las hagas planas; usa gradientes sutiles con los colores corporativos (`#714B67` a `#875A7B`) o iconos con fondo translúcido.
    *   Implementa un "Skeleton Loading" (esqueleto de carga) para cuando los datos se están cargando, en lugar de un simple spinner.

---

**Nota Final:** El objetivo es que esta herramienta sea utilizada por analistas financieros, por lo que la **densidad de información** (poder ver muchos datos a la vez) es importante, pero no debe sacrificar la **legibilidad**.
