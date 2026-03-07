# Código no usado – Evaluar eliminación

Documento para clean code: lista de código que no está referenciado en la aplicación, con motivo, para que puedas evaluar y eliminarlo con seguridad.

---

## Frontend

| Ubicación | Motivo | Acción recomendada |
|-----------|--------|---------------------|
| `frontend/components/filter-bar.tsx` | Ningún componente importa `FilterBar`. Collections y Treasury usan filtros inline. | Eliminar archivo o integrar en alguna página si se quiere barra de filtros reutilizable. |
| `frontend/app/letters/columns.tsx` | `app/letters/page.tsx` define columnas en un `useMemo` interno; no importa este archivo. | Eliminar o refactorizar Letters para usar estas columnas y evitar duplicación. |
| `frontend/app/treasury/columns.tsx` | `app/treasury/page.tsx` no importa estas columnas. | Eliminar o hacer que Treasury use este archivo. |
| `frontend/components/ui/data-table.tsx` | Ninguna página usa `DataTable`; Letters, Collections y Treasury renderizan tablas a mano. | Eliminar o estandarizar tablas usando este componente. |

**Ya corregido en esta revisión**

- `frontend/app/letters/page.tsx`: se quitaron imports no usados `Letter` (tipo) y `supabase` (cliente). No se usaban en el archivo.

---

## Backend

| Ubicación | Motivo | Acción recomendada |
|-----------|--------|---------------------|
| (ninguno detectado) | Los módulos y rutas revisados están en uso o son entrada de la app (blueprints, tasks). | — |

**Nota:** Celery (`app/core/celery_utils.py`, `app/tasks.py`) está registrado en `app/__init__.py`. Si no usas tareas asíncronas, se puede evaluar desactivar o eliminar esa parte en una revisión aparte.

---

## Rutas/páginas opcionales

Estas rutas existen pero no están en el menú principal (Sidebar). Si no se usan, se puede considerar eliminarlas o ocultarlas.

| Ruta | Archivo | Motivo |
|------|---------|--------|
| `/dashboard` | `frontend/app/dashboard/page.tsx` | Health check y enlaces; no enlazada desde el Sidebar. |
| `/diagnostics` | `frontend/app/diagnostics/page.tsx` | Diagnósticos Supabase/Flask; no enlazada desde el Sidebar. |

---

## Cómo usar este documento

1. **Revisar** cada ítem y decidir: eliminar, refactorizar o dejar (con comentario en código si se mantiene).
2. **Al eliminar**: borrar el archivo y cualquier import roto; ejecutar tests y build.
3. **Actualizar** este doc cuando se elimine o se vuelva a usar algo.

Los archivos listados en la tabla Frontend tienen además un comentario al inicio del archivo indicando que no están referenciados, para facilitar la evaluación en el propio código.
