# Finanzas AGV - Frontend (Next.js)

Sistema de gestión financiera con arquitectura moderna desacoplada.

## Stack Tecnológico

- **Framework**: Next.js 15 (App Router)
- **Lenguaje**: TypeScript
- **Estilos**: Tailwind CSS
- **Componentes**: Shadcn/UI
- **Estado**: TanStack Query (React Query)
- **Base de Datos**: Supabase (directo) + Flask API
- **Iconos**: Lucide React

## Instalación

```bash
# Instalar dependencias
npm install

# Modo desarrollo
npm run dev

# Build para producción
npm run build
npm run start
```

## Variables de Entorno

Crear `.env.local`:

```env
NEXT_PUBLIC_FLASK_API_URL=http://localhost:5000
NEXT_PUBLIC_SUPABASE_URL=https://qupyfyextppvlwlykmle.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu_clave_anon
```

## Estructura

```
frontend/
├── app/                    # Pages (App Router)
│   ├── letters/           # Dashboard de Letras
│   ├── collections/       # Reporte de Cobranzas
│   ├── layout.tsx         # Layout principal
│   └── providers.tsx      # TanStack Query Provider
├── components/
│   ├── ui/                # Componentes Shadcn
│   └── sidebar.tsx        # Navegación
├── lib/
│   ├── api.ts             # Cliente Flask API
│   ├── supabase.ts        # Cliente Supabase
│   └── utils.ts           # Utilidades
└── hooks/
    └── useRealtimeSubscription.ts
```

## Características

- ✅ Conexión dual: Supabase (rápido) + Flask API (calculado)
- ✅ Actualización en tiempo real con WebSockets
- ✅ UI profesional con Shadcn/UI
- ✅ TypeScript para type-safety
- ✅ Optimización de queries con React Query

## Rutas Disponibles

- `/letters` - Dashboard de Letras por Firmar
- `/collections` - Cuentas por Cobrar (Cuenta 12)
- `/treasury` - Cuentas por Pagar (Cuenta 42) [Pendiente]
- `/dashboard` - Dashboard principal [Pendiente]
