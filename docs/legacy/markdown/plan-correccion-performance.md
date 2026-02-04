# 🚀 Plan de Corrección de Performance - Dream Stack

## 🎯 Objetivo
Corregir los problemas críticos de rendimiento detectados en el plan original de Gemini 3 Pro y optimizar la aplicación para cargas de trabajo reales (10,000+ registros).

---

## 📋 Fase 1: Backend - Paginación Real en Odoo

### 1.1 Modificar `app/collections/services.py`

Agregar método optimizado con paginación real:

```python
def get_report_lines_paginated(self, page=1, per_page=50, start_date=None, 
                               end_date=None, customer=None, account_codes=None,
                               sales_channel_id=None, doc_type_id=None):
    """
    Obtiene líneas de reporte con paginación eficiente en Odoo.
    
    Args:
        page (int): Número de página (1-indexed)
        per_page (int): Registros por página
        ... (resto de filtros igual que get_report_lines)
    
    Returns:
        dict: {
            'data': [...],
            'total_count': 1234,
            'page': 1,
            'per_page': 50,
            'total_pages': 25,
            'has_more': True
        }
    """
    try:
        print(f"[INFO] Obteniendo página {page} (per_page={per_page})")
        
        if not self.repository.is_connected():
            raise ValueError("No hay conexión a Odoo disponible")
        
        # Construir domain (igual que get_report_lines original)
        domain = self._build_report_domain(
            start_date=start_date,
            end_date=end_date,
            customer=customer,
            account_codes=account_codes,
            sales_channel_id=sales_channel_id,
            doc_type_id=doc_type_id
        )
        
        # Campos necesarios
        fields = [
            'payment_state', 'invoice_date', 'I10nn_latam_document_type_id',
            'move_name', 'invoice_origin', 'account_id', 'patner_id',
            'currency_id', 'amount_total', 'amount_residual_with_retention',
            'amount_currency', 'amount_residual_currency', 'date',
            'date_maturity', 'invoice_date_due', 'ref',
            'invoice_payment_term_id', 'name', 'move_id',
            'partner_groups', 'sub_channel_id'
        ]
        
        # 1. Obtener TOTAL de registros (sin traer datos)
        total_count = self.repository.search_count('account.move.line', domain)
        
        # 2. Calcular offset y validar página
        offset = (page - 1) * per_page
        if offset >= total_count and page > 1:
            return {
                'data': [],
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page,
                'has_more': False
            }
        
        # 3. Obtener SOLO los registros de esta página
        lines = self.repository.search_read(
            'account.move.line',
            domain,
            fields,
            limit=per_page,
            offset=offset,
            order='date desc'  # Ordenar por fecha descendente
        )
        
        print(f"[OK] Obtenidos {len(lines)} registros de {total_count} totales")
        
        # 4. Procesar líneas (cálculos de mora, antigüedad, etc.)
        processed_lines = []
        for line in lines:
            # Extraer campos relacionales
            line['account_id/code'] = line.get('account_id', ['', ''])[1] if isinstance(line.get('account_id'), list) else ''
            line['account_id/name'] = line.get('account_id', ['', ''])[1] if isinstance(line.get('account_id'), list) else ''
            line['patner_id/vat'] = line.get('patner_id', {}).get('vat', '') if isinstance(line.get('patner_id'), dict) else ''
            line['patner_id/state_id'] = line.get('patner_id', {}).get('state_id', ['', ''])[1] if isinstance(line.get('patner_id'), dict) else ''
            line['patner_id/l10n_pe_district'] = line.get('patner_id', {}).get('l10n_pe_district', '') if isinstance(line.get('patner_id'), dict) else ''
            line['patner_id/country_code'] = line.get('patner_id', {}).get('country_code', '') if isinstance(line.get('patner_id'), dict) else ''
            line['patner_id/country_id'] = line.get('patner_id', {}).get('country_id', ['', ''])[1] if isinstance(line.get('patner_id'), dict) else ''
            
            # Cambiar patner_id a solo el nombre
            line['patner_id'] = line.get('patner_id', ['', ''])[1] if isinstance(line.get('patner_id'), list) else line.get('patner_id', '')
            
            # Cambiar move_id a solo el nombre
            line['move_id/invoice_user_id'] = line.get('move_id', {}).get('invoice_user_id', ['', ''])[1] if isinstance(line.get('move_id'), dict) else ''
            line['move_id/sales_channel_id'] = line.get('move_id', {}).get('sales_channel_id', ['', ''])[1] if isinstance(line.get('move_id'), dict) else ''
            line['move_id/sales_type_id'] = line.get('move_id', {}).get('sales_type_id', ['', ''])[1] if isinstance(line.get('move_id'), dict) else ''
            line['move_id/payment_state'] = line.get('move_id', {}).get('payment_state', '') if isinstance(line.get('move_id'), dict) else ''
            
            # Calcular días vencidos
            if line.get('date_maturity'):
                line['dias_vencido'] = calcular_dias_vencido(line['date_maturity'])
            else:
                line['dias_vencido'] = 0
            
            # Clasificar estado de deuda
            if line['dias_vencido'] > 0:
                line['estado_deuda'] = 'VENCIDO'
            else:
                line['estado_deuda'] = 'VIGENTE'
            
            # Clasificar antigüedad
            line['antiguedad'] = clasificar_antiguedad(line['dias_vencido'])
            
            processed_lines.append(line)
        
        # 5. Calcular metadatos de paginación
        total_pages = (total_count + per_page - 1) // per_page
        has_more = page < total_pages
        
        return {
            'data': processed_lines,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_more': has_more
        }
        
    except Exception as e:
        print(f"[ERROR] Error en paginación: {e}")
        import traceback
        traceback.print_exc()
        raise


def _build_report_domain(self, start_date=None, end_date=None, customer=None,
                        account_codes=None, sales_channel_id=None, doc_type_id=None):
    """
    Construye el domain de Odoo para filtrar líneas de movimiento.
    Método auxiliar para evitar duplicación de código.
    """
    domain = [
        ('move_id.state', '=', 'posted'),
        ('display_type', '=', False),
        ('exclude_from_invoice_tab', '=', False),
        ('account_id.include_initial_balance', '=', False)
    ]
    
    # Filtro por códigos de cuenta
    if account_codes:
        if isinstance(account_codes, str):
            codes = [c.strip() for c in account_codes.split(',')]
        else:
            codes = account_codes
        domain.append(('account_id.code', 'in', codes))
    
    # Filtro por fechas
    if start_date:
        domain.append(('date', '>=', start_date))
    if end_date:
        domain.append(('date', '<=', end_date))
    
    # Filtro por cliente
    if customer:
        domain.append(('patner_id.name', 'ilike', customer))
    
    # Filtro por canal de ventas
    if sales_channel_id:
        domain.append(('move_id.sales_channel_id', '=', sales_channel_id))
    
    # Filtro por tipo de documento
    if doc_type_id:
        domain.append(('move_id.I10nn_latam_document_type_id', '=', doc_type_id))
    
    return domain
```

### 1.2 Agregar método `search_count` en `app/core/odoo.py`

```python
def search_count(self, model, domain):
    """
    Cuenta registros que coinciden con el domain sin traer los datos.
    
    Args:
        model (str): Nombre del modelo de Odoo
        domain (list): Domain de búsqueda
    
    Returns:
        int: Cantidad de registros
    """
    try:
        if not self.is_connected():
            self.connect()
        
        count = self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'search_count', [domain]
        )
        
        return count
        
    except Exception as e:
        print(f"[ERROR] Error en search_count: {e}")
        return 0
```

---

## 📋 Fase 2: Backend - Endpoint de Stats Agregados

### 2.1 Agregar método de stats en `services.py`

```python
def get_aggregated_stats(self, start_date=None, end_date=None, customer=None,
                        account_codes=None, sales_channel_id=None, doc_type_id=None):
    """
    Obtiene estadísticas agregadas sin traer todas las filas.
    Usa consultas optimizadas con read_group de Odoo.
    
    Returns:
        dict: {
            'total_count': 1234,
            'total_amount': 500000.00,
            'pending_amount': 250000.00,
            'overdue_amount': 50000.00,
            'paid_amount': 250000.00
        }
    """
    try:
        if not self.repository.is_connected():
            raise ValueError("No hay conexión a Odoo disponible")
        
        # Construir domain
        domain = self._build_report_domain(
            start_date=start_date,
            end_date=end_date,
            customer=customer,
            account_codes=account_codes,
            sales_channel_id=sales_channel_id,
            doc_type_id=doc_type_id
        )
        
        # 1. Total de registros
        total_count = self.repository.search_count('account.move.line', domain)
        
        # 2. Sumar montos totales y saldos
        # Usar read_group para agregar en Odoo (mucho más eficiente)
        aggregated = self.repository.read_group(
            'account.move.line',
            domain,
            fields=['amount_total', 'amount_residual_with_retention', 'amount_residual_currency'],
            groupby=[]
        )
        
        if aggregated and len(aggregated) > 0:
            total_amount = aggregated[0].get('amount_total', 0)
            pending_amount = aggregated[0].get('amount_residual_with_retention', 0)
        else:
            total_amount = 0
            pending_amount = 0
        
        # 3. Calcular deuda vencida (requiere traer date_maturity)
        # Agregar filtro de fecha vencida al domain
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        overdue_domain = domain + [('date_maturity', '<', today)]
        
        overdue_aggregated = self.repository.read_group(
            'account.move.line',
            overdue_domain,
            fields=['amount_residual_with_retention'],
            groupby=[]
        )
        
        if overdue_aggregated and len(overdue_aggregated) > 0:
            overdue_amount = overdue_aggregated[0].get('amount_residual_with_retention', 0)
        else:
            overdue_amount = 0
        
        # 4. Monto pagado (diferencia)
        paid_amount = total_amount - pending_amount
        
        return {
            'total_count': total_count,
            'total_amount': round(total_amount, 2),
            'pending_amount': round(pending_amount, 2),
            'overdue_amount': round(overdue_amount, 2),
            'paid_amount': round(paid_amount, 2)
        }
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo stats: {e}")
        import traceback
        traceback.print_exc()
        return {
            'total_count': 0,
            'total_amount': 0,
            'pending_amount': 0,
            'overdue_amount': 0,
            'paid_amount': 0
        }
```

### 2.2 Agregar método `read_group` en `app/core/odoo.py`

```python
def read_group(self, model, domain, fields, groupby):
    """
    Realiza consulta agregada en Odoo (equivalente a GROUP BY en SQL).
    
    Args:
        model (str): Nombre del modelo
        domain (list): Filtros
        fields (list): Campos a agregar
        groupby (list): Campos para agrupar (vacío para agregación total)
    
    Returns:
        list: Resultados agregados
    """
    try:
        if not self.is_connected():
            self.connect()
        
        result = self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'read_group',
            [domain],
            {
                'fields': fields,
                'groupby': groupby,
                'lazy': False
            }
        )
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Error en read_group: {e}")
        return []
```

### 2.3 Agregar endpoint en `routes.py`

```python
@collections_bp.route('/report/account12/stats', methods=['GET'])
def report_account12_stats():
    """
    Endpoint para obtener KPIs agregados sin traer filas.
    Optimizado con read_group de Odoo.
    """
    try:
        # Filtros (mismos que rows)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        customer = request.args.get('customer')
        account_codes = request.args.get('account_codes', '122,1212,123,1312,132')
        sales_channel_id = request.args.get('sales_channel_id', type=int)
        doc_type_id = request.args.get('doc_type_id', type=int)
        
        # Crear servicio
        odoo_repo = _get_odoo_repository()
        collections_service = CollectionsService(odoo_repo)
        
        # Obtener stats agregados
        stats = collections_service.get_aggregated_stats(
            start_date=date_from,
            end_date=date_to,
            customer=customer,
            account_codes=account_codes,
            sales_channel_id=sales_channel_id,
            doc_type_id=doc_type_id
        )
        
        return jsonify({
            'success': True,
            'data': stats,
            'message': 'Stats calculados exitosamente'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error calculando stats: {str(e)}',
            'data': {
                'total_count': 0,
                'total_amount': 0,
                'pending_amount': 0,
                'overdue_amount': 0
            }
        }), 500
```

---

## 📋 Fase 3: Backend - Actualizar Endpoint de Filas

### 3.1 Modificar `routes.py::report_account12_rows()`

```python
@collections_bp.route('/report/account12/rows', methods=['GET'])
def report_account12_rows():
    """
    Endpoint para lazy loading con HTMX - retorna solo filas HTML.
    VERSIÓN OPTIMIZADA con paginación real en Odoo.
    """
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
        doc_type_id = request.args.get('doc_type_id', type=int)
        
        # Crear repositorio y servicio
        odoo_repo = _get_odoo_repository()
        collections_service = CollectionsService(odoo_repo)
        
        # ✅ OBTENER DATOS PAGINADOS (solo esta página)
        result = collections_service.get_report_lines_paginated(
            page=page,
            per_page=per_page,
            start_date=date_from,
            end_date=date_to,
            customer=customer,
            account_codes=account_codes,
            sales_channel_id=sales_channel_id,
            doc_type_id=doc_type_id
        )
        
        data = result['data']
        has_more = result['has_more']
        
        # Si no hay datos
        if not data and page == 1:
            return '''
                <tr>
                    <td colspan="33" class="text-center py-4 text-gray-500">
                        No se encontraron registros con los filtros aplicados
                    </td>
                </tr>
            '''
        elif not data:
            # Página sin datos - eliminar trigger de scroll infinito
            return '''
                <div id="infinite-scroll-trigger" hx-swap-oob="delete"></div>
            '''
        
        # Renderizar filas
        html = render_template('collections/report_account12_rows.html', rows=data)
        
        # Si hay más páginas, actualizar trigger con OOB swap
        if has_more:
            next_page = page + 1
            filters_params = f"&date_from={date_from or ''}&date_to={date_to or ''}&customer={customer or ''}&account_codes={account_codes}&sales_channel_id={sales_channel_id or ''}"
            
            trigger_html = f'''
                <div id="infinite-scroll-trigger" hx-swap-oob="true"
                     hx-get="/api/v1/collections/report/account12/rows?page={next_page}{filters_params}"
                     hx-trigger="revealed"
                     hx-swap="beforeend"
                     hx-target="#table-body"
                     class="text-center py-2 text-gray-400">
                    <div class="htmx-indicator">
                        <span class="text-sm">Cargando más resultados...</span>
                    </div>
                </div>
            '''
            html += trigger_html
        else:
            # No hay más páginas - eliminar trigger
            html += '<div id="infinite-scroll-trigger" hx-swap-oob="delete"></div>'
        
        return html
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f'''
            <tr>
                <td colspan="33" class="text-center text-red-600 py-4">
                    Error: {str(e)}
                </td>
            </tr>
        ''', 500
```

---

## 📋 Fase 4: Frontend - Actualizar Template HTML

### 4.1 Modificar `report_account12.html`

```html
<!-- Tabla con HTMX Lazy Loading -->
<div class="bg-white rounded-lg shadow-sm overflow-hidden">
    <div class="overflow-x-auto" style="max-height: 600px;">
        <table class="w-full text-sm">
            <thead class="bg-primary text-white sticky top-0 z-10">
                <tr>
                    <!-- ... columnas ... -->
                </tr>
            </thead>
            <tbody id="table-body">
                <!-- Filas se cargarán aquí vía HTMX -->
            </tbody>
        </table>
    </div>
    
    <!-- Loading indicator -->
    <div id="loading-spinner" 
         class="htmx-indicator flex justify-center items-center py-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>
    
    <!-- ✅ Infinite scroll trigger FUERA del tbody -->
    <div id="infinite-scroll-trigger"
         hx-get="/api/v1/collections/report/account12/rows?page=1"
         hx-trigger="revealed"
         hx-swap="beforeend"
         hx-target="#table-body"
         hx-indicator="#loading-spinner"
         class="text-center py-2 text-gray-400">
        <div class="htmx-indicator">
            <span class="text-sm">Cargando más resultados...</span>
        </div>
    </div>
</div>
```

### 4.2 Actualizar Alpine.js Controller

```javascript
function reportController() {
    return {
        loading: false,
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
            this.loadStats(); // ✅ Cargar stats al inicio
            this.setupHTMXListeners();
            this.triggerInitialLoad();
        },
        
        triggerInitialLoad() {
            // Disparar carga inicial de datos
            const params = new URLSearchParams(this.filters);
            const trigger = document.getElementById('infinite-scroll-trigger');
            if (trigger) {
                htmx.trigger(trigger, 'revealed');
            }
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
        
        // ✅ Nuevo método para cargar stats
        async loadStats() {
            try {
                this.loading = true;
                const params = new URLSearchParams(this.filters);
                const { data } = await axios.get(`/api/v1/collections/report/account12/stats?${params}`);
                
                if (data.success) {
                    this.stats = {
                        count: data.data.total_count,
                        total: data.data.total_amount,
                        pending: data.data.pending_amount,
                        overdue: data.data.overdue_amount
                    };
                }
            } catch (error) {
                console.error('Error loading stats:', error);
                showToast('Error cargando estadísticas', 'error');
            } finally {
                this.loading = false;
            }
        },
        
        setupHTMXListeners() {
            // Mostrar loading durante requests
            document.body.addEventListener('htmx:beforeRequest', (event) => {
                if (event.detail.target.id === 'table-body') {
                    this.loading = true;
                }
            });
            
            // Ocultar loading después de cargar
            document.body.addEventListener('htmx:afterSwap', (event) => {
                if (event.detail.target.id === 'table-body') {
                    this.loading = false;
                }
            });
            
            // Manejar errores
            document.body.addEventListener('htmx:responseError', (event) => {
                showToast('Error cargando datos', 'error');
                this.loading = false;
            });
        },
        
        applyFilters() {
            // Resetear tabla
            document.getElementById('table-body').innerHTML = '';
            
            // Construir URL con filtros
            const params = new URLSearchParams(this.filters);
            const url = `/api/v1/collections/report/account12/rows?page=1&${params}`;
            
            // Recrear trigger
            const triggerContainer = document.getElementById('infinite-scroll-trigger').parentElement;
            triggerContainer.innerHTML = `
                <div id="infinite-scroll-trigger"
                     hx-get="${url}"
                     hx-trigger="revealed"
                     hx-swap="beforeend"
                     hx-target="#table-body"
                     hx-indicator="#loading-spinner"
                     class="text-center py-2 text-gray-400">
                    <div class="htmx-indicator">
                        <span class="text-sm">Cargando resultados...</span>
                    </div>
                </div>
            `;
            
            // Procesar HTMX en el nuevo elemento
            htmx.process(document.getElementById('infinite-scroll-trigger'));
            
            // Recargar stats
            this.loadStats();
            
            // Disparar carga
            this.triggerInitialLoad();
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
```

---

## 📋 Fase 5: Implementar Cache (Opcional pero Recomendado)

### 5.1 Instalar Flask-Caching

```bash
pip install Flask-Caching
```

### 5.2 Configurar cache en `app/__init__.py`

```python
from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'simple',  # O 'redis' para producción
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutos
})

def create_app():
    app = Flask(__name__)
    
    # ... otras configuraciones ...
    
    # Inicializar cache
    cache.init_app(app)
    
    return app
```

### 5.3 Usar cache en endpoints

```python
from app import cache

@collections_bp.route('/report/account12/stats', methods=['GET'])
@cache.cached(timeout=300, query_string=True)  # Cache por 5 min
def report_account12_stats():
    # ... código existente ...
    pass

@collections_bp.route('/report/account12/rows', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def report_account12_rows():
    # ... código existente ...
    pass
```

---

## 📋 Fase 6: Comprimir Respuestas HTTP

### 6.1 Instalar Flask-Compress

```bash
pip install Flask-Compress
```

### 6.2 Configurar en `app/__init__.py`

```python
from flask_compress import Compress

def create_app():
    app = Flask(__name__)
    
    # ... otras configuraciones ...
    
    # Configurar compresión
    app.config['COMPRESS_MIMETYPES'] = [
        'text/html',
        'text/css',
        'text/javascript',
        'application/json',
        'application/javascript'
    ]
    app.config['COMPRESS_LEVEL'] = 6
    app.config['COMPRESS_MIN_SIZE'] = 500
    
    # Inicializar compresión
    Compress(app)
    
    return app
```

---

## 🧪 Fase 7: Testing

### 7.1 Crear script de prueba de carga

```python
# test_performance.py
import time
import requests
import statistics

BASE_URL = "http://localhost:5000/api/v1/collections"

def test_pagination_performance():
    """Testea performance de paginación"""
    times = []
    
    for page in range(1, 11):  # 10 páginas
        start = time.time()
        response = requests.get(f"{BASE_URL}/report/account12/rows?page={page}")
        elapsed = time.time() - start
        times.append(elapsed)
        
        print(f"Página {page}: {elapsed:.3f}s - {len(response.text)} bytes")
        
        assert response.status_code == 200
        assert 'Error' not in response.text
    
    print(f"\n📊 Estadísticas:")
    print(f"  - Media: {statistics.mean(times):.3f}s")
    print(f"  - Mediana: {statistics.median(times):.3f}s")
    print(f"  - Mín: {min(times):.3f}s")
    print(f"  - Máx: {max(times):.3f}s")
    
    # Asegurar que todas las páginas cargan en < 1s
    assert max(times) < 1.0, f"Página más lenta: {max(times):.3f}s"
    
def test_stats_performance():
    """Testea performance de stats"""
    start = time.time()
    response = requests.get(f"{BASE_URL}/report/account12/stats")
    elapsed = time.time() - start
    
    print(f"\n📊 Stats: {elapsed:.3f}s")
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'total_count' in data['data']
    
    # Stats debe responder en < 500ms
    assert elapsed < 0.5, f"Stats muy lento: {elapsed:.3f}s"

if __name__ == '__main__':
    print("🚀 Iniciando pruebas de performance...\n")
    test_pagination_performance()
    test_stats_performance()
    print("\n✅ Todas las pruebas pasaron!")
```

### 7.2 Ejecutar pruebas

```bash
python test_performance.py
```

---

## 📊 Checklist de Implementación

### Backend
- [ ] Agregar `search_count()` en `OdooRepository`
- [ ] Agregar `read_group()` en `OdooRepository`
- [ ] Crear `_build_report_domain()` en `CollectionsService`
- [ ] Crear `get_report_lines_paginated()` en `CollectionsService`
- [ ] Crear `get_aggregated_stats()` en `CollectionsService`
- [ ] Actualizar `report_account12_rows()` en `routes.py`
- [ ] Crear endpoint `report_account12_stats()` en `routes.py`
- [ ] Instalar y configurar Flask-Caching
- [ ] Instalar y configurar Flask-Compress

### Frontend
- [ ] Mover trigger fuera del `<tbody>`
- [ ] Implementar OOB swap en respuestas
- [ ] Actualizar `loadStats()` para usar endpoint real
- [ ] Actualizar `applyFilters()` para recargar stats
- [ ] Agregar listeners de HTMX para loading states
- [ ] Remover variable global `currentPage`
- [ ] Testear en móviles

### Testing
- [ ] Crear script de pruebas de performance
- [ ] Testear con 10,000+ registros
- [ ] Verificar que paginación funciona con filtros
- [ ] Verificar que stats se actualizan con filtros
- [ ] Verificar que scroll infinito no duplica
- [ ] Testear exportación Excel
- [ ] Monitorear uso de memoria del servidor

### Producción
- [ ] Cambiar cache de `simple` a `redis`
- [ ] Configurar logging de performance
- [ ] Implementar rate limiting
- [ ] Documentar API
- [ ] Capacitar equipo en nuevo sistema

---

## 🎯 Resultados Esperados

### Performance
- Tiempo primera carga: **< 500ms** (antes: 3-5s)
- Tiempo paginación: **< 300ms** (antes: 3-5s)
- Tiempo stats: **< 400ms** (nueva funcionalidad)
- Memoria servidor: **< 5MB** por request (antes: 50MB+)

### UX
- Loading instantáneo al aplicar filtros
- KPIs actualizados en tiempo real
- Scroll infinito sin duplicados
- Sin freezes con 10,000+ registros

### Escalabilidad
- Soporta datasets de 100,000+ registros
- Múltiples usuarios concurrentes
- Cache reduce carga en Odoo 80%

---

**Siguiente Paso:** Implementar Fase 1 y testear

