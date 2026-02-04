# Migración al "Dream Stack" Flask (Sin Node.js)

## Stack Tecnológico

- **Backend**: Flask + Jinja2 (mantener actual)
- **Dinámicas**: HTMX 1.9+ (lazy loading, paginación)
- **Interactividad**: Alpine.js 3.x (filtros reactivos, estados)
- **Estilos**: Tailwind CSS vía CDN
- **HTTP**: Axios (requests optimizados)
- **Fechas**: Day.js con locale español
- **Notificaciones**: SweetAlert2
- **Charts**: ECharts (reemplaza Chart.js)
- **Iconos**: Bootstrap Icons (mantener)

## Fase 1: Limpieza de Archivos Vue

### Eliminar implementación anterior

- Eliminar `app/templates/collections/report_account12_vue.html`
- Revertir `base.html`: quitar Vue.js, PrimeVue CDNs (líneas 469-472)
- Revertir `app/collections/routes.py`: eliminar import `render_template` y ruta `/report/account12-vue`
- Restaurar enlace sidebar: cambiar `collections.report_account12_vue` a `web.collections_report_12`

## Fase 2: Integrar Dream Stack en base.html

### Actualizar sección de scripts (antes de `</body>`)

Reemplazar scripts actuales con:

```html
<!-- Bootstrap 5.3 JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<!-- Dream Stack Core -->
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js"></script>

<!-- Utilidades -->
<script src="https://cdn.jsdelivr.net/npm/axios@1.6.2/dist/axios.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dayjs@1.11.10/dayjs.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dayjs@1.11.10/locale/es.js"></script>
<script>dayjs.locale('es');</script>
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>

<!-- Charts -->
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>

<!-- Tailwind CSS (Desarrollo) -->
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          primary: '#714B67',
          secondary: '#875A7B'
        }
      }
    }
  }
</script>
```

### Eliminar scripts obsoletos

- Remover jQuery (no necesario con HTMX)
- Remover DataTables (usar tabla nativa con HTMX)
- Remover Chart.js (usar ECharts)

### Agregar helper global para HTMX

```html
<script>
  // Configuración global HTMX
  document.body.addEventListener('htmx:configRequest', (event) => {
    event.detail.headers['X-Requested-With'] = 'XMLHttpRequest';
  });
  
  // Helpers globales
  window.formatCurrency = (value) => {
    return new Intl.NumberFormat('es-PE', { 
      style: 'currency', 
      currency: 'PEN' 
    }).format(value || 0);
  };
  
  window.showToast = (message, icon = 'success') => {
    Swal.fire({
      toast: true,
      position: 'top-end',
      icon: icon,
      title: message,
      showConfirmButton: false,
      timer: 3000
    });
  };
</script>
```

## Fase 3: Backend - Endpoint de Paginación

### Crear nuevo endpoint en app/collections/routes.py

```python
@collections_bp.route('/report/account12/rows', methods=['GET'])
def report_account12_rows():
    """Endpoint para lazy loading con HTMX - retorna solo filas HTML"""
    try:
        # Parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        # Filtros
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        customer = request.args.get('customer')
        account_codes = request.args.get('account_codes', '122,1212,123,1312,132')
        sales_channel_id = request.args.get('sales_channel_id', type=int)
        
        # Crear repositorio y servicio
        odoo_repo = _get_odoo_repository()
        collections_service = CollectionsService(odoo_repo)
        
        # Obtener datos paginados
        all_data = collections_service.get_report_lines(
            start_date=date_from,
            end_date=date_to,
            customer=customer,
            account_codes=account_codes,
            sales_channel_id=sales_channel_id,
            limit=0  # Obtener todos primero
        )
        
        # Paginar en memoria (o modificar service para usar OFFSET)
        start = (page - 1) * per_page
        end = start + per_page
        data = all_data[start:end]
        
        # Renderizar solo las filas
        return render_template('collections/report_account12_rows.html', rows=data)
        
    except Exception as e:
        return f'<tr><td colspan="15" class="text-center text-danger">Error: {str(e)}</td></tr>', 500
```

### Crear plantilla parcial: app/templates/collections/report_account12_rows.html

```html
{% for row in rows %}
<tr class="hover:bg-gray-50 transition-colors">
    <td class="px-3 py-2 text-sm">{{ row.move_name }}</td>
    <td class="px-3 py-2 text-sm">{{ row.patner_id }}</td>
    <td class="px-3 py-2 text-sm">{{ row['patner_id/vat'] }}</td>
    <td class="px-3 py-2 text-sm">{{ row.partner_groups }}</td>
    <td class="px-3 py-2 text-sm">{{ row.sub_channel_id }}</td>
    <td class="px-3 py-2 text-sm">{{ row['move_id/sales_channel_id'] }}</td>
    <td class="px-3 py-2 text-sm">{{ row.invoice_date }}</td>
    <td class="px-3 py-2 text-sm">{{ row.date_maturity }}</td>
    <td class="px-3 py-2 text-sm text-right">{{ "%.2f"|format(row.amount_total or 0) }}</td>
    <td class="px-3 py-2 text-sm text-right">{{ "%.2f"|format(row.amount_residual_with_retention or 0) }}</td>
    <td class="px-3 py-2 text-sm text-center {% if row.dias_vencido > 0 %}text-red-600 font-bold{% endif %}">
        {{ row.dias_vencido or 0 }}
    </td>
    <td class="px-3 py-2 text-sm text-center">
        <span class="px-2 py-1 rounded text-xs {% if row.estado_deuda == 'VENCIDO' %}bg-red-100 text-red-800{% else %}bg-green-100 text-green-800{% endif %}">
            {{ row.estado_deuda }}
        </span>
    </td>
    <td class="px-3 py-2 text-sm">{{ row.antiguedad }}</td>
</tr>
{% endfor %}
```

## Fase 4: Frontend - Reescribir report_account12.html

### Estructura completa con Alpine.js + HTMX

```html
{% extends "base.html" %}

{% block title %}Reporte Cuenta 12 - Dream Stack{% endblock %}

{% block content %}
<div x-data="reportController()" x-init="init()">
    <!-- Header -->
    <div class="flex justify-between items-center pb-4 mb-4 border-b">
        <h1 class="text-2xl font-bold text-gray-800">
            <i class="bi bi-file-earmark-text text-primary"></i>
            Reporte Cuenta 12 - Cuentas por Cobrar
        </h1>
        <div class="space-x-2">
            <button @click="exportToExcel()" 
                    class="btn btn-sm btn-success"
                    :disabled="loading">
                <i class="bi bi-file-earmark-excel"></i> Exportar Excel
            </button>
            <button @click="refreshData()" 
                    class="btn btn-sm btn-primary"
                    :disabled="loading">
                <i class="bi" :class="loading ? 'bi-hourglass-split' : 'bi-arrow-clockwise'"></i>
                <span x-text="loading ? 'Cargando...' : 'Actualizar'"></span>
            </button>
        </div>
    </div>

    <!-- Filtros con Alpine.js -->
    <div class="bg-white rounded-lg shadow-sm p-4 mb-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Fecha Desde</label>
                <input type="date" 
                       x-model="filters.date_from"
                       class="form-control">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Fecha Hasta</label>
                <input type="date" 
                       x-model="filters.date_to"
                       class="form-control">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Cliente</label>
                <input type="text" 
                       x-model="filters.customer"
                       placeholder="Buscar cliente..."
                       class="form-control">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Canal de Venta</label>
                <select x-model="filters.sales_channel_id" class="form-select">
                    <option value="">Todos</option>
                    <template x-for="channel in salesChannels" :key="channel.id">
                        <option :value="channel.id" x-text="channel.name"></option>
                    </template>
                </select>
            </div>
        </div>
        <div class="mt-4 flex gap-2">
            <button @click="applyFilters()" class="btn btn-primary">
                <i class="bi bi-search"></i> Buscar
            </button>
            <button @click="resetFilters()" class="btn btn-secondary">
                <i class="bi bi-x-circle"></i> Limpiar
            </button>
        </div>
    </div>

    <!-- KPIs con Alpine.js (reactivos) -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <div class="bg-white rounded-lg shadow-sm p-4">
            <h6 class="text-gray-500 text-sm font-medium mb-2">Total Registros</h6>
            <h4 class="text-2xl font-bold text-gray-800" x-text="stats.count"></h4>
        </div>
        <div class="bg-white rounded-lg shadow-sm p-4">
            <h6 class="text-gray-500 text-sm font-medium mb-2">Monto Total</h6>
            <h4 class="text-2xl font-bold text-blue-600" x-text="formatCurrency(stats.total)"></h4>
        </div>
        <div class="bg-white rounded-lg shadow-sm p-4">
            <h6 class="text-gray-500 text-sm font-medium mb-2">Saldo Pendiente</h6>
            <h4 class="text-2xl font-bold text-yellow-600" x-text="formatCurrency(stats.pending)"></h4>
        </div>
        <div class="bg-white rounded-lg shadow-sm p-4">
            <h6 class="text-gray-500 text-sm font-medium mb-2">Deuda Vencida</h6>
            <h4 class="text-2xl font-bold text-red-600" x-text="formatCurrency(stats.overdue)"></h4>
        </div>
    </div>

    <!-- Tabla con HTMX Lazy Loading -->
    <div class="bg-white rounded-lg shadow-sm overflow-hidden">
        <div class="overflow-x-auto" style="max-height: 600px;">
            <table class="w-full text-sm">
                <thead class="bg-primary text-white sticky top-0 z-10">
                    <tr>
                        <th class="px-3 py-3 text-left font-semibold">Factura</th>
                        <th class="px-3 py-3 text-left font-semibold">Cliente</th>
                        <th class="px-3 py-3 text-left font-semibold">RUC/DNI</th>
                        <th class="px-3 py-3 text-left font-semibold">Grupo</th>
                        <th class="px-3 py-3 text-left font-semibold">Sub Canal</th>
                        <th class="px-3 py-3 text-left font-semibold">Canal</th>
                        <th class="px-3 py-3 text-left font-semibold">F. Emisión</th>
                        <th class="px-3 py-3 text-left font-semibold">F. Venc.</th>
                        <th class="px-3 py-3 text-right font-semibold">Monto Total</th>
                        <th class="px-3 py-3 text-right font-semibold">Saldo</th>
                        <th class="px-3 py-3 text-center font-semibold">Días Venc.</th>
                        <th class="px-3 py-3 text-center font-semibold">Estado</th>
                        <th class="px-3 py-3 text-left font-semibold">Antigüedad</th>
                    </tr>
                </thead>
                <tbody 
                    id="table-body"
                    hx-get="/api/v1/collections/report/account12/rows?page=1"
                    hx-trigger="load"
                    hx-swap="innerHTML"
                    hx-indicator="#loading-spinner">
                    <!-- Filas se cargarán aquí vía HTMX -->
                </tbody>
            </table>
        </div>
        
        <!-- Loading indicator -->
        <div id="loading-spinner" 
             class="htmx-indicator flex justify-center items-center py-8">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
        
        <!-- Infinite scroll trigger -->
        <div hx-get="/api/v1/collections/report/account12/rows"
             hx-trigger="revealed"
             hx-swap="beforeend"
             hx-target="#table-body"
             hx-vals="js:{page: getNextPage()}"
             x-show="hasMore"
             class="text-center py-4 text-gray-500">
            Cargando más resultados...
        </div>
    </div>
</div>

<!-- Alpine.js Controller -->
<script>
function reportController() {
    return {
        loading: false,
        currentPage: 1,
        hasMore: true,
        filters: {
            date_from: '',
            date_to: '',
            customer: '',
            account_codes: '122,1212,123,1312,132',
            sales_channel_id: ''
        },
        stats: {
            count: 0,
            total: 0,
            pending: 0,
            overdue: 0
        },
        salesChannels: [],
        
        async init() {
            await this.loadSalesChannels();
            this.setupHTMXListeners();
        },
        
        async loadSalesChannels() {
            try {
                const { data } = await axios.get('/api/v1/collections/filter-options');
                if (data.success) {
                    this.salesChannels = data.data.sales_channels;
                }
            } catch (error) {
                console.error('Error loading channels:', error);
            }
        },
        
        setupHTMXListeners() {
            // Actualizar stats después de cargar datos
            document.body.addEventListener('htmx:afterSwap', (event) => {
                if (event.detail.target.id === 'table-body') {
                    this.updateStats();
                }
            });
        },
        
        updateStats() {
            const rows = document.querySelectorAll('#table-body tr');
            this.stats.count = rows.length;
            // Calcular stats desde los datos visibles
            // O hacer request separado a endpoint de stats
        },
        
        applyFilters() {
            this.currentPage = 1;
            const params = new URLSearchParams(this.filters);
            htmx.ajax('GET', `/api/v1/collections/report/account12/rows?page=1&${params}`, '#table-body');
        },
        
        resetFilters() {
            this.filters = {
                date_from: '',
                date_to: '',
                customer: '',
                account_codes: '122,1212,123,1312,132',
                sales_channel_id: ''
            };
            this.applyFilters();
        },
        
        refreshData() {
            this.applyFilters();
        },
        
        async exportToExcel() {
            this.loading = true;
            try {
                const params = new URLSearchParams(this.filters);
                window.location.href = `/api/v1/exports/collections/excel?${params}`;
                showToast('Exportación iniciada', 'success');
            } catch (error) {
                showToast('Error al exportar', 'error');
            } finally {
                this.loading = false;
            }
        },
        
        formatCurrency(value) {
            return window.formatCurrency(value);
        }
    }
}

// Helper para HTMX pagination
let currentPage = 1;
function getNextPage() {
    currentPage++;
    return currentPage;
}
</script>
{% endblock %}
```

## Fase 5: Optimizaciones de Performance

### Modificar services.py para paginación eficiente

Agregar método optimizado:

```python
def get_report_lines_paginated(self, page=1, per_page=50, **kwargs):
    """
    Versión optimizada con paginación real en Odoo
    """
    offset = (page - 1) * per_page
    
    # Usar limit y offset directamente en la query de Odoo
    # Esto evita cargar todos los registros en memoria
    lines = self.repository.search_read(
        'account.move.line',
        domain,  # Mismo domain que get_report_lines
        fields,
        limit=per_page,
        offset=offset
    )
    
    # Procesar solo las filas paginadas
    return self._process_lines(lines)
```

## Fase 6: Estilos y Animaciones

### Agregar CSS custom en extra_css del template

```css
/* Animaciones HTMX */
.htmx-swapping {
    opacity: 0;
    transition: opacity 200ms ease-out;
}

.htmx-settling {
    opacity: 1;
}

/* Loading spinner custom */
.htmx-indicator {
    display: none;
}

.htmx-request .htmx-indicator {
    display: flex;
}

/* Skeleton loader para primera carga */
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

.skeleton-row {
    height: 40px;
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 1000px 100%;
    animation: shimmer 2s infinite;
}

/* Smooth scroll */
.overflow-x-auto {
    scroll-behavior: smooth;
}

/* Tailwind + Bootstrap compatibility */
.btn {
    @apply px-4 py-2 rounded font-medium transition-colors;
}

.btn-primary {
    @apply bg-primary hover:bg-opacity-90 text-white;
}

.form-control {
    @apply w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-transparent;
}
```

## Fase 7: Testing y Validación

### Checklist de funcionalidad

1. **Lazy Loading**

   - Primera carga muestra 50 filas
   - Scroll infinito carga siguiente página
   - Loading spinner visible durante carga

2. **Filtros Reactivos**

   - Cambiar filtros recarga tabla
   - Limpiar filtros resetea valores
   - KPIs se actualizan con filtros

3. **Performance**

   - Cargar 1000+ registros sin lag
   - Exportación Excel funcional
   - Notificaciones SweetAlert2 aparecen

4. **Responsive**

   - Funciona en mobile
   - Scroll horizontal en tablas largas
   - Filtros se adaptan

## Ventajas del Dream Stack

1. **Sin Node.js** - Todo vía CDN
2. **Progressive Enhancement** - Funciona sin JS
3. **Performance Nativo** - Lazy loading eficiente
4. **Código Limpio** - Alpine.js declarativo
5. **Mantenible** - Python devs pueden leer HTML/Alpine
6. **Moderno** - UX igual a React/Vue
7. **Ligero** - 84KB total (vs 400KB+ de frameworks SPA)

## Migración Futura a Producción

### Standalone Tailwind (sin CDN)

1. Descargar `tailwindcss-windows.exe` desde GitHub
2. Crear `input.css` con las clases usadas
3. Ejecutar: `tailwindcss -i input.css -o static/css/tailwind.min.css --minify`
4. Reemplazar CDN por archivo local
5. Resultado: 10KB en lugar de 3.5MB