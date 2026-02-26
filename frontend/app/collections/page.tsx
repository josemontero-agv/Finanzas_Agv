"use client"

import { useState, useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { collectionsApi, ReportParams, flaskApi } from "@/lib/api"
import { FileText, Search, RotateCcw, Download, Filter } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ErrorFallback } from "@/components/error-fallback"
import { cn } from "@/lib/utils"

const DEFAULT_FILTERS: ReportParams = {
  date_from: '',
  date_to: '',
  date_cutoff: '',
  customer: '',
  sub_channel: '',
  account_codes: '',
  sales_channel_id: undefined,
  doc_type_id: undefined,
  include_reconciled: false,
}

export default function CollectionsPage() {
  const [draftFilters, setDraftFilters] = useState<ReportParams>(DEFAULT_FILTERS)
  const [appliedFilters, setAppliedFilters] = useState<ReportParams>(DEFAULT_FILTERS)
  const [hasAppliedFilters, setHasAppliedFilters] = useState(false)

  const [isFiltersOpen, setIsFiltersOpen] = useState(true)
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)

  // AppShell ya validó sesión; esta página solo se monta si hay auth OK
  const { data: filterOptions } = useQuery({
    queryKey: ["collections", "filter-options", appliedFilters],
    queryFn: async () => {
      const response = await collectionsApi.getFilterOptions(appliedFilters)
      return response.data.data
    },
  })

  const { data: response, isLoading, error, refetch } = useQuery({
    queryKey: ["collections", "report", appliedFilters],
    queryFn: async () => {
      const response = await collectionsApi.getReport({ ...appliedFilters, limit: 500 })
      return response.data
    },
    enabled: hasAppliedFilters,
    retry: 1,
    staleTime: 60_000,
  })

  const data = response?.data || []
  const summary = response?.summary

  const handleFilterChange = (key: keyof ReportParams, value: any) => {
    setDraftFilters(prev => ({ ...prev, [key]: value }))
  }

  const resetFilters = () => {
    setDraftFilters(DEFAULT_FILTERS)
    setAppliedFilters(DEFAULT_FILTERS)
    setHasAppliedFilters(false)
  }

  const applyFilters = () => {
    setAppliedFilters(draftFilters)
    setHasAppliedFilters(true)
  }

  const handleExport = () => {
    if (!hasAppliedFilters) return
    const params = new URLSearchParams()
    Object.entries(appliedFilters).forEach(([key, value]) => {
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

  const normalizeText = (value: unknown) => {
    if (value === null || value === undefined || value === false) return ""
    const text = String(value).trim()
    if (!text || text.toLowerCase() === "false") return ""
    return text
  }

  const firstValue = (row: Record<string, any>, keys: string[]) => {
    for (const key of keys) {
      const value = normalizeText(row[key])
      if (value) return value
    }
    return ""
  }

  const firstNumber = (row: Record<string, any>, keys: string[]) => {
    for (const key of keys) {
      const raw = row[key]
      if (raw !== null && raw !== undefined && raw !== "" && raw !== false) {
        const n = Number(raw)
        if (!Number.isNaN(n)) return n
      }
    }
    return 0
  }

  const formatDateDisplay = (value: unknown) => {
    const text = normalizeText(value)
    if (!text) return ""
    const match = text.match(/^(\d{4})-(\d{2})-(\d{2})$/)
    if (!match) return text
    const [, yyyy, mm, dd] = match
    return `${dd}/${mm}/${yyyy}`
  }

  const columns = useMemo(() => ([
    { key: "tipo_documento", label: "Tipo Documento", get: (row: any) => firstValue(row, ["account.move/l10n_latam_document_type_id", "l10n_latam_document_type_id"]), maxWidth: "max-w-[180px]" },
    { key: "factura", label: "Nro Factura", get: (row: any) => firstValue(row, ["account.move/name", "move_name"]), maxWidth: "max-w-[180px]" },
    { key: "nro_pedido", label: "Nro Pedido", get: (row: any) => firstValue(row, ["account.move/invoice_origin", "invoice_origin"]), maxWidth: "max-w-[160px]" },
    { key: "fecha_factura", label: "Fecha Factura", get: (row: any) => firstValue(row, ["move_id/invoice_date", "invoice_date"]), isDate: true },
    { key: "fecha_contabilizacion", label: "Fecha Contabilización", get: (row: any) => firstValue(row, ["account.move/invoice_date", "date"]), isDate: true },
    { key: "fecha_vencimiento", label: "Fecha Vencimiento", get: (row: any) => firstValue(row, ["account.move/invoice_date_due", "invoice_date_due", "date_maturity"]), isDate: true },
    { key: "letra", label: "Letra", get: (row: any) => firstValue(row, ["account.move/l10n_latam_boe_number", "l10n_latam_boe_number"]) },
    { key: "cuenta", label: "Cuenta", get: (row: any) => firstValue(row, ["account_id/code"]) },
    { key: "nombre_cuenta", label: "Nombre Cuenta", get: (row: any) => firstValue(row, ["account_id/name"]), maxWidth: "max-w-[260px]" },
    { key: "cliente", label: "Cliente", get: (row: any) => firstValue(row, ["patner_id", "partner_name"]), maxWidth: "max-w-[260px]" },
    { key: "ruc", label: "RUC", get: (row: any) => firstValue(row, ["patner_id/vat", "partner_vat"]) },
    { key: "moneda", label: "Moneda", get: (row: any) => firstValue(row, ["account_id/currency_id", "currency_id"]) },
    { key: "monto_total", label: "Monto Total", get: (row: any) => firstNumber(row, ["account.move/amount_total", "amount_total", "amount_currency"]), isMoney: true },
    { key: "saldo", label: "Monto Residual", get: (row: any) => firstNumber(row, ["account.move/amount_residual", "amount_residual_with_retention", "amount_residual_historical"]), isMoney: true },
    { key: "condicion_pago", label: "Condición Pago", get: (row: any) => firstValue(row, ["account.move/invoice_payment_term_id", "invoice_payment_term_id"]), maxWidth: "max-w-[180px]" },
    { key: "descripcion", label: "Descripción", get: (row: any) => firstValue(row, ["account.move.line/name", "name"]), maxWidth: "max-w-[260px]" },
    { key: "vendedor", label: "Vendedor", get: (row: any) => firstValue(row, ["account.move/invoice_user_id", "invoice_user_name", "move_id/invoice_user_id"]), maxWidth: "max-w-[220px]" },
    { key: "estado_documento", label: "Estado Documento", get: (row: any) => firstValue(row, ["move_id/state", "state"]), maxWidth: "max-w-[160px]" },
    { key: "linea_comercial", label: "Línea Comercial", get: (row: any) => firstValue(row, ["account.move/linea_comercial", "linea_comercial", "team_name"]), maxWidth: "max-w-[220px]" },
    { key: "grupo_comercial", label: "Grupo Comercial", get: (row: any) => firstValue(row, ["grupo_comercial", "agr.credit.customer/partner_groups_ids", "agr.credit.customer/patner_groups_ids", "partner_groups"]), maxWidth: "max-w-[220px]" },
    { key: "sub_canal", label: "Sub Canal", get: (row: any) => firstValue(row, ["agr.credit.customer/sub_channel_id", "sub_channel_id"]), maxWidth: "max-w-[160px]" },
    { key: "canal_venta", label: "Canal Venta", get: (row: any) => firstValue(row, ["account.move/sales_channel_id", "sales_channel_name", "move_id/sales_channel_id"]), maxWidth: "max-w-[180px]" },
    { key: "tipo_venta", label: "Tipo Venta", get: (row: any) => firstValue(row, ["account.move/sale_type_id", "account.move/sales_type_id", "sales_type_name", "move_id/sales_type_id"]), maxWidth: "max-w-[180px]" },
    { key: "provincia", label: "Provincia", get: (row: any) => firstValue(row, ["patner_id/state_id", "partner_state"]) },
    { key: "pais", label: "País", get: (row: any) => firstValue(row, ["patner_id/country_id", "partner_country_name"]) },
    { key: "dias", label: "Días Venc.", get: (row: any) => row.dias_vencido || 0 },
    { key: "estado", label: "Estado", get: (row: any) => firstValue(row, ["estado_deuda"]) },
  ]), [])

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
            disabled={!hasAppliedFilters}
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
                  value={draftFilters.date_cutoff} 
                  onChange={(e) => handleFilterChange('date_cutoff', e.target.value)}
                  className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Fecha Desde</label>
                <Input 
                  type="date" 
                  value={draftFilters.date_from} 
                  onChange={(e) => handleFilterChange('date_from', e.target.value)}
                  disabled={!!draftFilters.date_cutoff}
                  className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Fecha Hasta</label>
                <Input 
                  type="date" 
                  value={draftFilters.date_to} 
                  onChange={(e) => handleFilterChange('date_to', e.target.value)}
                  disabled={!!draftFilters.date_cutoff}
                  className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Cliente</label>
                <Input 
                  placeholder="Buscar cliente..." 
                  value={draftFilters.customer} 
                  onChange={(e) => handleFilterChange('customer', e.target.value)}
                  className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
            </div>

            <div className="mt-4">
              <Button
                type="button"
                variant="ghost"
                className="text-sm text-slate-600 dark:text-slate-300"
                onClick={() => setShowAdvancedFilters((prev) => !prev)}
              >
                {showAdvancedFilters ? "Ocultar filtros avanzados" : "Mostrar filtros avanzados"}
              </Button>
            </div>

            {showAdvancedFilters && (
              <div className="mt-3 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Canal de Venta</label>
                <select 
                  className="w-full h-10 px-3 py-2 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-[#714B67] dark:focus:ring-purple-500 focus:ring-offset-0 disabled:opacity-50"
                  value={draftFilters.sales_channel_id?.toString() || ""} 
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
                  value={draftFilters.doc_type_id?.toString() || ""} 
                  onChange={(e) => handleFilterChange('doc_type_id', e.target.value ? parseInt(e.target.value) : undefined)}
                >
                  <option value="">Todos los tipos</option>
                  {filterOptions?.document_types.map(t => (
                    <option key={t.id} value={t.id.toString()}>{t.name}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Sub Canal</label>
                <select
                  className="w-full h-10 px-3 py-2 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-[#714B67] dark:focus:ring-purple-500 focus:ring-offset-0 disabled:opacity-50"
                  value={draftFilters.sub_channel || ""}
                  onChange={(e) => handleFilterChange('sub_channel', e.target.value)}
                >
                  <option value="">Todos los sub canales</option>
                  {filterOptions?.sub_channels?.map(sc => (
                    <option key={sc.value} value={sc.value}>{sc.name}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Códigos de Cuenta</label>
                <Input 
                  placeholder="Ingresa su cuenta contable" 
                  value={draftFilters.account_codes} 
                  onChange={(e) => handleFilterChange('account_codes', e.target.value)}
                  className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
              </div>
            )}
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="ghost" onClick={resetFilters} className="text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">
                <RotateCcw className="mr-2 h-4 w-4" />
                Limpiar
              </Button>
              <Button onClick={applyFilters} className="bg-[#714B67] hover:bg-[#875A7B] dark:bg-purple-600 dark:hover:bg-purple-700">
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
          <p className="text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">Monto Residual Total</p>
          <p className="text-2xl font-bold text-purple-900 dark:text-purple-200">
            {formatCurrency(summary?.overall.saldo_total ?? summary?.overall.saldo)}
          </p>
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
                {columns.map((col) => (
                  <th key={col.key} className="px-4 py-3 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    {Array.from({ length: columns.length }).map((_, j) => (
                      <td key={j} className="px-4 py-4"><div className="h-4 bg-slate-200 dark:bg-slate-700 rounded"></div></td>
                    ))}
                  </tr>
                ))
              ) : !hasAppliedFilters ? (
                <tr>
                  <td colSpan={columns.length} className="px-4 py-12 text-center text-slate-500 dark:text-slate-400">
                    Aplica filtros para consultar y luego exportar a Excel.
                  </td>
                </tr>
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-4 py-12 text-center text-slate-500 dark:text-slate-400">
                    No se encontraron resultados con los filtros aplicados.
                  </td>
                </tr>
              ) : (
                data.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                    {columns.map((col) => {
                      const value = col.get(row)
                      const isState = col.key === "estado"
                      const isDays = col.key === "dias"
                      const cellValue = col.isMoney
                        ? Number(value || 0).toLocaleString('es-PE', { minimumFractionDigits: 2 })
                        : col.isDate
                          ? formatDateDisplay(value)
                        : normalizeText(value)

                      return (
                        <td key={col.key} className={cn(
                          "px-4 py-3 whitespace-nowrap border-r border-slate-100 dark:border-slate-800",
                          col.isMoney && "text-right font-mono",
                          isDays && "text-center font-bold",
                          isState && "text-center",
                          !col.isMoney && !isState && !isDays && "max-w-[220px]"
                        )}>
                          {isState ? (
                            <Badge className={cn(
                              value === 'VENCIDO'
                                ? "bg-red-100 text-red-700 hover:bg-red-100 dark:bg-red-900/40 dark:text-red-300"
                                : "bg-green-100 text-green-700 hover:bg-green-100 dark:bg-green-900/40 dark:text-green-300"
                            )}>
                              {normalizeText(value)}
                            </Badge>
                          ) : isDays ? (
                            <span className={cn(
                              Number(value || 0) > 0 ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400"
                            )}>
                              {value || 0}
                            </span>
                          ) : (
                            <span className={cn("block truncate", col.maxWidth || "max-w-[220px]")} title={cellValue}>
                              {cellValue}
                            </span>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!isLoading && data.length > 0 && (
          <div className="p-4 bg-slate-50 dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 text-xs text-slate-500 dark:text-slate-400 flex justify-between">
            <span>
              Mostrando {response?.shown_count || data.length} de {response?.count || data.length} registros.
              Para ver el total detallado, exporta a Excel.
            </span>
            <span>* Montos en moneda local del sistema</span>
          </div>
        )}
      </div>
    </div>
  )
}
