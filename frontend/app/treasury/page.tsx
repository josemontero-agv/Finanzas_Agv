"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { treasuryApi, ReportParams, flaskApi } from "@/lib/api"
import { FileText, Search, RotateCcw, Download, Filter, CreditCard, DollarSign, AlertCircle, TrendingDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ErrorFallback } from "@/components/error-fallback"
import { cn } from "@/lib/utils"
import { useRealtimeSubscription } from "@/hooks/useRealtimeSubscription"

export default function TreasuryPage() {
  const [useSupabase, setUseSupabase] = useState(true)
  const [filters, setFilters] = useState<ReportParams>({
    date_from: '',
    date_to: '',
    date_cutoff: '',
    supplier: '',
    account_codes: '4212,422,4312',
    payment_state: '',
    include_reconciled: false
  })

  const [isFiltersOpen, setIsFiltersOpen] = useState(true)

  // Consulta principal
  const { data: response, isLoading, error, refetch } = useQuery({
    queryKey: ["treasury", "report", filters, useSupabase],
    queryFn: async () => {
      const params: any = { ...filters }
      if (useSupabase) {
        params.use_supabase = true
      }
      const res = await treasuryApi.getReport(params)
      return res.data
    },
    retry: 1,
  })

  // Suscripción en tiempo real
  useRealtimeSubscription("fact_moves", ["treasury", "report", filters, useSupabase] as any)

  const data = response?.data || []
  const summary = response?.summary

  // Calcular estadísticas manuales si no viene summary (fallback)
  const totalAmount = data.reduce((sum, item) => sum + (item.amount_total || 0), 0)
  const totalPending = data.reduce((sum, item) => sum + (item.amount_residual || 0), 0)
  const overdueCount = data.filter(item => (item.dias_vencido || 0) > 0).length

  const handleFilterChange = (key: keyof ReportParams, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const resetFilters = () => {
    setFilters({
      date_from: '',
      date_to: '',
      date_cutoff: '',
      supplier: '',
      account_codes: '4212,422,4312',
      payment_state: '',
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
    const url = `${flaskApi.defaults.baseURL}/api/v1/exports/treasury/excel?${params.toString()}`
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
      title="Error al cargar Tesorería"
      message="Verifica que Flask esté corriendo en puerto 5000"
    />
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[#714B67] dark:text-purple-400">Cuentas por Pagar</h1>
          <p className="text-muted-foreground dark:text-slate-400 mt-2">
            Reporte de Cuenta 42/43 - Tesorería y Proveedores
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={useSupabase ? "default" : "outline"}
            onClick={() => setUseSupabase(!useSupabase)}
            className={useSupabase ? "bg-[#714B67] hover:bg-[#875A7B] dark:bg-purple-600 dark:hover:bg-purple-700" : "border-[#714B67] text-[#714B67] dark:border-purple-500 dark:text-purple-400"}
          >
            {useSupabase ? "📊 Supabase (Rápido)" : "🔢 Flask (Calculado)"}
          </Button>
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
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Proveedor</label>
                <Input 
                  placeholder="Buscar proveedor..." 
                  value={filters.supplier} 
                  onChange={(e) => handleFilterChange('supplier', e.target.value)}
                  className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Estado de Pago</label>
                <select 
                  className="w-full h-10 px-3 py-2 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-[#714B67] dark:focus:ring-purple-500 focus:ring-offset-0 disabled:opacity-50"
                  value={filters.payment_state || ""} 
                  onChange={(e) => handleFilterChange('payment_state', e.target.value)}
                >
                  <option value="">Todos los estados</option>
                  <option value="not_paid">Pendiente</option>
                  <option value="in_payment">En Proceso</option>
                  <option value="paid">Pagado</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Códigos de Cuenta</label>
                <Input 
                  placeholder="Ej: 4212,422" 
                  value={filters.account_codes} 
                  onChange={(e) => handleFilterChange('account_codes', e.target.value)}
                  className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
              <div className="flex items-end pb-2">
                <div className="flex items-center space-x-2">
                  <input 
                    type="checkbox"
                    id="reconciled_treasury" 
                    className="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-[#714B67] focus:ring-[#714B67] dark:focus:ring-purple-500"
                    checked={!!filters.include_reconciled}
                    onChange={(e) => handleFilterChange('include_reconciled', e.target.checked)}
                  />
                  <label htmlFor="reconciled_treasury" className="text-sm font-semibold text-slate-700 dark:text-slate-300 cursor-pointer">
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
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-blue-50/50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-xl p-6">
          <div className="flex justify-between items-start mb-2">
            <p className="text-sm font-medium text-blue-700 dark:text-blue-300">Monto Total</p>
            <DollarSign className="h-4 w-4 text-blue-600 dark:text-blue-300" />
          </div>
          <p className="text-2xl font-bold text-blue-900 dark:text-blue-200">{formatCurrency(totalAmount)}</p>
        </div>
        <div className="bg-green-50/50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-xl p-6">
          <div className="flex justify-between items-start mb-2">
            <p className="text-sm font-medium text-green-700 dark:text-green-300">Saldo Pendiente</p>
            <TrendingDown className="h-4 w-4 text-green-600 dark:text-green-300" />
          </div>
          <p className="text-2xl font-bold text-green-900 dark:text-green-200">{formatCurrency(totalPending)}</p>
        </div>
        <div className="bg-purple-50/50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800 rounded-xl p-6">
          <div className="flex justify-between items-start mb-2">
            <p className="text-sm font-medium text-purple-700 dark:text-purple-300">Facturas Vencidas</p>
            <AlertCircle className="h-4 w-4 text-purple-600 dark:text-purple-300" />
          </div>
          <p className="text-2xl font-bold text-purple-900 dark:text-purple-200">{overdueCount}</p>
        </div>
        <div className="bg-orange-50/50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-800 rounded-xl p-6">
          <div className="flex justify-between items-start mb-2">
            <p className="text-sm font-medium text-orange-700 dark:text-orange-300">Total Registros</p>
            <CreditCard className="h-4 w-4 text-orange-600 dark:text-orange-300" />
          </div>
          <p className="text-2xl font-bold text-orange-900 dark:text-orange-200">{data.length}</p>
        </div>
      </div>

      {/* Tabla de Datos */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-[#714B67]/20 dark:border-purple-500/20 shadow-md overflow-hidden">
        <div className="bg-[#714B67] dark:bg-slate-800 p-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-white" />
          <h3 className="text-white font-semibold">Detalle de Cuentas por Pagar</h3>
        </div>
        <div className="relative overflow-x-auto overflow-y-auto max-h-[600px]">
          <table className="w-full text-sm text-left border-collapse">
            <thead className="sticky top-0 z-20 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-semibold border-b border-slate-200 dark:border-slate-700 text-xs uppercase tracking-wider">
              <tr>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">Fecha Factura</th>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">N° Documento</th>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">Proveedor</th>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">Moneda</th>
                <th className="px-4 py-4 whitespace-nowrap text-right border-r border-slate-200 dark:border-slate-700">Total Origen</th>
                <th className="px-4 py-4 whitespace-nowrap text-right border-r border-slate-200 dark:border-slate-700">Adeudado</th>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">Vencimiento</th>
                <th className="px-4 py-4 whitespace-nowrap text-center border-r border-slate-200 dark:border-slate-700">Estado</th>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">Referencia</th>
                <th className="px-4 py-4 whitespace-nowrap text-center">Días Venc.</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    {Array.from({ length: 10 }).map((_, j) => (
                      <td key={j} className="px-4 py-4"><div className="h-4 bg-slate-200 dark:bg-slate-700 rounded"></div></td>
                    ))}
                  </tr>
                ))
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-4 py-12 text-center text-slate-500 dark:text-slate-400">
                    No se encontraron resultados con los filtros aplicados.
                  </td>
                </tr>
              ) : (
                data.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors border-b border-slate-50 dark:border-slate-800">
                    <td className="px-4 py-3 whitespace-nowrap border-r border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-300">{row.invoice_date}</td>
                    <td className="px-4 py-3 font-bold text-[#714B67] dark:text-purple-400 whitespace-nowrap border-r border-slate-100 dark:border-slate-800">{row.move_name}</td>
                    <td className="px-4 py-3 max-w-[250px] truncate border-r border-slate-100 dark:border-slate-800 font-medium text-slate-700 dark:text-slate-300" title={row.supplier_name}>{row.supplier_name}</td>
                    <td className="px-4 py-3 text-center border-r border-slate-100 dark:border-slate-800">
                      <Badge variant="outline" className="font-bold border-slate-300 text-slate-600 dark:border-slate-600 dark:text-slate-300">{row.currency_id}</Badge>
                    </td>
                    <td className="px-4 py-3 text-right font-mono border-r border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-300 font-medium">
                      {row.amount_total?.toLocaleString('es-PE', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold border-r border-slate-100 dark:border-slate-800 text-slate-900 dark:text-slate-100 bg-slate-50/50 dark:bg-slate-800/40">
                      {row.amount_residual?.toLocaleString('es-PE', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap border-r border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-300">{row.invoice_date_due}</td>
                    <td className="px-4 py-3 text-center border-r border-slate-100 dark:border-slate-800">
                      <Badge className={cn(
                        "font-bold px-3 py-1",
                        row.payment_state === 'paid' ? "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/40 dark:text-green-300 dark:border-green-800" : 
                        row.payment_state === 'not_paid' ? "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/40 dark:text-red-300 dark:border-red-800" : 
                        "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-900/40 dark:text-orange-300 dark:border-orange-800"
                      )} variant="outline">
                        {row.payment_state === 'paid' ? 'PAGADO' : row.payment_state === 'not_paid' ? 'PENDIENTE' : row.payment_state === 'in_payment' ? 'EN PAGO' : row.payment_state?.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 truncate max-w-[150px] border-r border-slate-100 dark:border-slate-800 text-slate-500 dark:text-slate-400" title={row.ref}>{row.ref}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={cn(
                        "font-black text-sm px-2 py-1 rounded",
                        (row.dias_vencido || 0) > 0 ? "text-red-600 bg-red-50 dark:text-red-300 dark:bg-red-900/40" : "text-green-600 bg-green-50 dark:text-green-300 dark:bg-green-900/40"
                      )}>
                        {row.dias_vencido || 0}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!isLoading && data.length > 0 && (
          <div className="p-4 bg-slate-50 dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 text-xs font-medium text-slate-500 dark:text-slate-400 flex justify-between items-center">
            <span className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#714B67] dark:bg-purple-500"></div>
              Mostrando {data.length} de {response?.count || data.length} registros
            </span>
            <span>* Última actualización: {new Date().toLocaleString("es-PE")}</span>
          </div>
        )}
      </div>
    </div>
  )
}
