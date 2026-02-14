"use client"

import { useState, useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { collectionsApi, ReportParams, flaskApi } from "@/lib/api"
import { FileText, Search, RotateCcw, Download, Filter, ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ErrorFallback } from "@/components/error-fallback"
import { cn } from "@/lib/utils"

export default function CollectionsPage() {
  const [filters, setFilters] = useState<ReportParams>({
    date_from: '',
    date_to: '',
    date_cutoff: '',
    customer: '',
    account_codes: '122,1212,123,1312,132,13',
    sales_channel_id: undefined,
    doc_type_id: undefined,
    include_reconciled: false
  })

  const [isFiltersOpen, setIsFiltersOpen] = useState(true)

  // Opciones de filtros
  const { data: filterOptions } = useQuery({
    queryKey: ["collections", "filter-options"],
    queryFn: async () => {
      const response = await collectionsApi.getFilterOptions()
      return response.data.data
    }
  })

  // Consulta principal
  const { data: response, isLoading, error, refetch } = useQuery({
    queryKey: ["collections", "report", filters],
    queryFn: async () => {
      const response = await collectionsApi.getReport(filters)
      return response.data
    },
    retry: 1,
  })

  const data = response?.data || []
  const summary = response?.summary

  const handleFilterChange = (key: keyof ReportParams, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const resetFilters = () => {
    setFilters({
      date_from: '',
      date_to: '',
      date_cutoff: '',
      customer: '',
      account_codes: '122,1212,123,1312,132,13',
      sales_channel_id: undefined,
      doc_type_id: undefined,
      include_reconciled: false
    })
  }

  const handleExport = () => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '' && value !== null) {
        params.append(key, String(value))
      }
    })
    const url = `${flaskApi.defaults.baseURL}/api/v1/exports/collections/excel?${params.toString()}`
    window.location.href = url
  }

  const formatCurrency = (value: number | undefined) => {
    return new Intl.NumberFormat('es-PE', {
      style: 'currency',
      currency: 'PEN',
      minimumFractionDigits: 2
    }).format(value || 0)
  }

  if (error) {
    return <ErrorFallback 
      error={error instanceof Error ? error : null}
      title="Error al cargar Cobranzas"
      message="Verifica que Flask esté corriendo en puerto 5000"
    />
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[#714B67] dark:text-purple-400">Cuentas por Cobrar</h1>
          <p className="text-muted-foreground dark:text-slate-400 mt-2">
            Reporte de Cuenta 12 - Facturas y Notas de Crédito
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => setIsFiltersOpen(!isFiltersOpen)}
            className="border-[#714B67] text-[#714B67] hover:bg-[#714B67]/10 dark:border-purple-500 dark:text-purple-400 dark:hover:bg-purple-500/10"
          >
            <Filter className="mr-2 h-4 w-4" />
            {isFiltersOpen ? "Ocultar Filtros" : "Mostrar Filtros"}
          </Button>
          <Button 
            onClick={handleExport}
            className="bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-600 text-white"
          >
            <Download className="mr-2 h-4 w-4" />
            Excel
          </Button>
          <Button 
            onClick={() => refetch()} 
            disabled={isLoading}
            className="bg-[#714B67] hover:bg-[#875A7B] dark:bg-purple-600 dark:hover:bg-purple-700"
          >
            <RotateCcw className={cn("mr-2 h-4 w-4", isLoading && "animate-spin")} />
            Actualizar
          </Button>
        </div>
      </div>

      {/* Panel de Filtros */}
      {isFiltersOpen && (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-[#714B67]/20 dark:border-purple-500/20 shadow-sm overflow-hidden">
          <div className="p-4 pb-3 border-b border-slate-100 dark:border-slate-800">
            <h2 className="text-lg font-medium flex items-center gap-2 text-slate-800 dark:text-slate-200">
              <Search className="h-4 w-4 text-[#714B67] dark:text-purple-400" />
              Filtros de Búsqueda
            </h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Fecha de Corte (Histórico)</label>
                <Input 
                  type="date" 
                  value={filters.date_cutoff} 
                  onChange={(e) => handleFilterChange('date_cutoff', e.target.value)}
                  className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Fecha Desde</label>
                <Input 
                  type="date" 
                  value={filters.date_from} 
                  onChange={(e) => handleFilterChange('date_from', e.target.value)}
                  disabled={!!filters.date_cutoff}
                  className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Fecha Hasta</label>
                <Input 
                  type="date" 
                  value={filters.date_to} 
                  onChange={(e) => handleFilterChange('date_to', e.target.value)}
                  disabled={!!filters.date_cutoff}
                  className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Cliente</label>
                <Input 
                  placeholder="Buscar cliente..." 
                  value={filters.customer} 
                  onChange={(e) => handleFilterChange('customer', e.target.value)}
                  className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Canal de Venta</label>
                <select 
                  className="w-full h-10 px-3 py-2 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-[#714B67] dark:focus:ring-purple-500 focus:ring-offset-0 disabled:opacity-50"
                  value={filters.sales_channel_id?.toString() || ""} 
                  onChange={(e) => handleFilterChange('sales_channel_id', e.target.value ? parseInt(e.target.value) : undefined)}
                >
                  <option value="">Todos los canales</option>
                  {filterOptions?.sales_channels.map(c => (
                    <option key={c.id} value={c.id.toString()}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Tipo Documento</label>
                <select 
                  className="w-full h-10 px-3 py-2 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-[#714B67] dark:focus:ring-purple-500 focus:ring-offset-0 disabled:opacity-50"
                  value={filters.doc_type_id?.toString() || ""} 
                  onChange={(e) => handleFilterChange('doc_type_id', e.target.value ? parseInt(e.target.value) : undefined)}
                >
                  <option value="">Todos los tipos</option>
                  {filterOptions?.document_types.map(t => (
                    <option key={t.id} value={t.id.toString()}>{t.name}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Códigos de Cuenta</label>
                <Input 
                  placeholder="Ej: 122,1212" 
                  value={filters.account_codes} 
                  onChange={(e) => handleFilterChange('account_codes', e.target.value)}
                  className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
              <div className="flex items-end pb-2">
                <div className="flex items-center space-x-2">
                  <input 
                    type="checkbox"
                    id="reconciled" 
                    className="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-[#714B67] focus:ring-[#714B67] dark:focus:ring-purple-500"
                    checked={!!filters.include_reconciled}
                    onChange={(e) => handleFilterChange('include_reconciled', e.target.checked)}
                  />
                  <label htmlFor="reconciled" className="text-sm font-semibold text-slate-700 dark:text-slate-300 cursor-pointer">
                    Incluir pagados
                  </label>
                </div>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="ghost" onClick={resetFilters} className="text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">
                <RotateCcw className="mr-2 h-4 w-4" />
                Limpiar
              </Button>
              <Button onClick={() => refetch()} className="bg-[#714B67] hover:bg-[#875A7B] dark:bg-purple-600 dark:hover:bg-purple-700">
                <Search className="mr-2 h-4 w-4" />
                Aplicar Filtros
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Resumen KPIs */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <div className="bg-blue-50/50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-xl p-6">
          <p className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">Débito Total</p>
          <p className="text-2xl font-bold text-blue-900 dark:text-blue-200">{formatCurrency(summary?.overall.debit)}</p>
        </div>
        <div className="bg-green-50/50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-xl p-6">
          <p className="text-sm font-medium text-green-700 dark:text-green-300 mb-2">Haber Total</p>
          <p className="text-2xl font-bold text-green-900 dark:text-green-200">{formatCurrency(summary?.overall.credit)}</p>
        </div>
        <div className="bg-purple-50/50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800 rounded-xl p-6">
          <p className="text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">Saldo Pendiente</p>
          <p className="text-2xl font-bold text-purple-900 dark:text-purple-200">{formatCurrency(summary?.overall.pending_cutoff)}</p>
        </div>
        <div className="bg-red-50/50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-xl p-6">
          <p className="text-sm font-medium text-red-700 dark:text-red-300 mb-2">Deuda Vencida</p>
          <p className="text-2xl font-bold text-red-900 dark:text-red-200">{formatCurrency(summary?.overall.overdue_amount)}</p>
        </div>
        <div className="bg-orange-50/50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-800 rounded-xl p-6">
          <p className="text-sm font-medium text-orange-700 dark:text-orange-300 mb-2">Registros</p>
          <p className="text-2xl font-bold text-orange-900 dark:text-orange-200">{summary?.overall.count || 0}</p>
        </div>
      </div>

      {/* Tabla de Datos */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-[#714B67]/20 dark:border-purple-500/20 shadow-md overflow-hidden">
        <div className="bg-[#714B67] dark:bg-slate-800 p-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-white" />
          <h3 className="text-white font-semibold">Detalle de Movimientos (Cuenta 12)</h3>
        </div>
        <div className="relative overflow-x-auto overflow-y-auto max-h-[600px]">
          <table className="w-full text-sm text-left border-collapse">
            <thead className="sticky top-0 z-20 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-semibold border-b border-slate-200 dark:border-slate-700">
              <tr>
                <th className="px-4 py-3 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">Factura</th>
                <th className="px-4 py-3 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">Letra</th>
                <th className="px-4 py-3 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">Origen</th>
                <th className="px-4 py-3 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">Cliente</th>
                <th className="px-4 py-3 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">RUC/DNI</th>
                <th className="px-4 py-3 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">F. Emisión</th>
                <th className="px-4 py-3 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">F. Vencimiento</th>
                <th className="px-4 py-3 whitespace-nowrap border-r border-slate-200 dark:border-slate-700 text-center">Moneda</th>
                <th className="px-4 py-3 whitespace-nowrap text-right border-r border-slate-200 dark:border-slate-700">Monto Total</th>
                <th className="px-4 py-3 whitespace-nowrap text-right border-r border-slate-200 dark:border-slate-700">Saldo</th>
                <th className="px-4 py-3 whitespace-nowrap text-center border-r border-slate-200 dark:border-slate-700">Días Venc.</th>
                <th className="px-4 py-3 whitespace-nowrap text-center border-r border-slate-200 dark:border-slate-700">Estado</th>
                <th className="px-4 py-3 whitespace-nowrap text-center">Antigüedad</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    {Array.from({ length: 13 }).map((_, j) => (
                      <td key={j} className="px-4 py-4"><div className="h-4 bg-slate-200 dark:bg-slate-700 rounded"></div></td>
                    ))}
                  </tr>
                ))
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={13} className="px-4 py-12 text-center text-slate-500 dark:text-slate-400">
                    No se encontraron resultados con los filtros aplicados.
                  </td>
                </tr>
              ) : (
                data.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                    <td className="px-4 py-3 font-medium text-[#714B67] dark:text-purple-400 whitespace-nowrap border-r border-slate-100 dark:border-slate-800">{row.move_name}</td>
                    <td className="px-4 py-3 whitespace-nowrap border-r border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-400">{row.l10n_latam_boe_number || '-'}</td>
                    <td className="px-4 py-3 whitespace-nowrap border-r border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-400">{row.invoice_origin || '-'}</td>
                    <td className="px-4 py-3 max-w-[200px] truncate border-r border-slate-100 dark:border-slate-800 text-slate-700 dark:text-slate-300" title={row.partner_name}>{row.partner_name}</td>
                    <td className="px-4 py-3 whitespace-nowrap border-r border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-400">{row.partner_vat}</td>
                    <td className="px-4 py-3 whitespace-nowrap border-r border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-300">{row.invoice_date}</td>
                    <td className="px-4 py-3 whitespace-nowrap border-r border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-300">{row.date_maturity}</td>
                    <td className="px-4 py-3 text-center border-r border-slate-100 dark:border-slate-800">
                      <Badge variant="outline" className="dark:border-slate-600 dark:text-slate-300">{row.currency_id}</Badge>
                    </td>
                    <td className="px-4 py-3 text-right font-mono border-r border-slate-100 dark:border-slate-800 text-slate-700 dark:text-slate-300">
                      {row.amount_currency?.toLocaleString('es-PE', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold border-r border-slate-100 dark:border-slate-800 text-slate-900 dark:text-slate-100">
                      {(row.amount_residual_historical || row.amount_residual_with_retention)?.toLocaleString('es-PE', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-center border-r border-slate-100 dark:border-slate-800">
                      <span className={cn(
                        "font-bold",
                        (row.dias_vencido || 0) > 0 ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400"
                      )}>
                        {row.dias_vencido || 0}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center border-r border-slate-100 dark:border-slate-800">
                      <Badge className={cn(
                        row.estado_deuda === 'VENCIDO' ? "bg-red-100 text-red-700 hover:bg-red-100 dark:bg-red-900/40 dark:text-red-300" : 
                        "bg-green-100 text-green-700 hover:bg-green-100 dark:bg-green-900/40 dark:text-green-300"
                      )}>
                        {row.estado_deuda || 'VIGENTE'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-600 dark:text-slate-400">
                      {row.antiguedad}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!isLoading && data.length > 0 && (
          <div className="p-4 bg-slate-50 dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 text-xs text-slate-500 dark:text-slate-400 flex justify-between">
            <span>Mostrando {data.length} de {response?.count || data.length} registros</span>
            <span>* Montos en moneda local del sistema</span>
          </div>
        )}
      </div>
    </div>
  )
}
