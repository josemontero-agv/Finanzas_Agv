"use client"

import { useQuery } from "@tanstack/react-query"
import { lettersApi, Letter, authApi } from "@/lib/api"
import { supabase } from "@/lib/supabase"
import { Mail, Search, X, Send, Eye, RotateCcw, FileText, CheckCircle2 } from "lucide-react"
import { useState, useMemo, useEffect } from "react"
import { useRouter } from "next/navigation"
import axios from "axios"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ErrorFallback } from "@/components/error-fallback"
import { cn } from "@/lib/utils"

export default function LettersPage() {
  const router = useRouter()
  const [clientFilter, setClientFilter] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("TODOS")
  const [rowSelection, setRowSelection] = useState<Record<number, boolean>>({})
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [isConfirmOpen, setIsConfirmOpen] = useState(false)
  const [isSuccessOpen, setIsSuccessOpen] = useState(false)
  const [isErrorOpen, setIsErrorOpen] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [lastSentCount, setLastSentCount] = useState(0)
  const [sentLetterIds, setSentLetterIds] = useState<Set<number>>(new Set())
  const [isSending, setIsSending] = useState(false)
  const isDev = process.env.NODE_ENV === 'development'

  const {
    data: authData,
    isLoading: isAuthLoading,
    isError: isAuthError,
    error: authError,
  } = useQuery({
    queryKey: ["auth", "user-info"],
    queryFn: async () => {
      const response = await authApi.getUserInfo()
      return response.data
    },
    retry: false,
  })

  useEffect(() => {
    if (!isAuthError) return
    if (axios.isAxiosError(authError) && authError.response?.status === 401) {
      router.replace("/login")
    }
  }, [isAuthError, authError, router])

  // Consulta a Flask API (tiene los datos completos de Odoo)
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["letters", "to-accept"],
    queryFn: async () => {
      const response = await lettersApi.getToAccept()
      return response.data.data
    },
    enabled: authData?.success === true,
    retry: 1,
  })

  const normalizeStatus = (status: string) => {
    return status === "POR RECUPERAR" ? "VENCIDO" : status
  }

  // Filtrado local
  const filteredData = useMemo(() => {
    if (!data) return []
    const search = clientFilter.toLowerCase()
    return data.filter(item => {
      const matchesSearch = 
        item.acceptor_id?.toLowerCase().includes(search) ||
        item.number?.toLowerCase().includes(search) ||
        item.vat?.toLowerCase().includes(search)
      
      const normalizedFilter = normalizeStatus(statusFilter)
      const normalizedItemStatus = normalizeStatus(item.status_calc)
      const matchesStatus = normalizedFilter === "TODOS" || normalizedItemStatus === normalizedFilter
      
      return matchesSearch && matchesStatus
    })
  }, [data, clientFilter, statusFilter])

  // Obtener letras seleccionadas
  const selectedLetters = useMemo(() => {
    return filteredData.filter((_, index) => rowSelection[index])
  }, [filteredData, rowSelection])

  const toggleAll = (checked: boolean) => {
    if (checked) {
      const newSelection: Record<number, boolean> = {}
      filteredData.forEach((_, idx) => {
        newSelection[idx] = true
      })
      setRowSelection(newSelection)
    } else {
      setRowSelection({})
    }
  }

  const toggleRow = (idx: number) => {
    setRowSelection(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }))
  }

  const alreadySentInSelection = useMemo(() => {
    return selectedLetters.filter(l => sentLetterIds.has(l.id))
  }, [selectedLetters, sentLetterIds])

  const handleSendEmails = async () => {
    if (selectedLetters.length === 0) return
    setIsConfirmOpen(true)
  }

  const executeSendEmails = async () => {
    setIsConfirmOpen(false)
    setIsSending(true)
    try {
      const ids = selectedLetters.map(l => l.id)
      await lettersApi.sendAcceptanceEmails(ids)
      
      setLastSentCount(selectedLetters.length)
      setSentLetterIds(prev => {
        const next = new Set(prev)
        ids.forEach(id => next.add(id))
        return next
      })
      setIsSuccessOpen(true)
      
      setRowSelection({})
      setIsPreviewOpen(false)
      refetch()
    } catch (err) {
      console.error("Error enviando correos:", err)
      setErrorMessage(err instanceof Error ? err.message : "Ocurrió un problema inesperado al enviar los correos.")
      setIsErrorOpen(true)
    } finally {
      setIsSending(false)
    }
  }

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } finally {
      router.replace("/login")
    }
  }

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat("es-PE", {
      style: "currency",
      currency: "PEN",
    }).format(amount).replace("PEN", "S/.")
  }

  const getStatusBadgeClass = (status: string) => {
    const normalizedStatus = normalizeStatus(status)
    if (normalizedStatus === "VENCIDO") {
      return "bg-red-100 text-red-700 border-red-200"
    }
    if (normalizedStatus === "POR VENCER") {
      return "bg-amber-100 text-amber-700 border-amber-200"
    }
    if (normalizedStatus === "VIGENTE") {
      return "bg-blue-100 text-blue-700 border-blue-200"
    }
    return "bg-slate-100 text-slate-700 border-slate-200"
  }

  if (isAuthLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-[#714B67]"></div>
        <p className="mt-4 text-lg font-semibold text-slate-700 font-bold">Validando sesión...</p>
      </div>
    )
  }

  if (isAuthError && !(axios.isAxiosError(authError) && authError.response?.status === 401)) {
    return <ErrorFallback
      error={authError instanceof Error ? authError : null}
      title="Error de autenticación"
      message="No se pudo validar la sesión actual."
    />
  }

  if (error) {
    return <ErrorFallback 
      error={error instanceof Error ? error : null}
      title="Error al cargar Letras"
      message="Verifica que Flask esté corriendo en puerto 5000"
    />
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-[#714B67]"></div>
        <p className="mt-4 text-lg font-semibold text-slate-700 font-bold">Cargando letras...</p>
        <p className="text-sm text-slate-500 font-medium">Sincronizando con Odoo ERP</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Banner de Modo Desarrollo */}
      {isDev && (
        <div className="bg-amber-50 dark:bg-amber-950/50 border-2 border-amber-400 dark:border-amber-600 rounded-xl p-4 flex items-center gap-3 shadow-sm">
          <div className="w-10 h-10 bg-amber-400 dark:bg-amber-600 rounded-lg flex items-center justify-center">
            <span className="text-2xl">🔧</span>
          </div>
          <div className="flex-1">
            <p className="font-black text-amber-900 dark:text-amber-200 text-sm uppercase tracking-wide">Modo Desarrollo Activado</p>
            <p className="text-amber-700 dark:text-amber-300 text-xs font-medium mt-0.5">
              Todos los correos se enviarán a: <strong>creditosycobranzas@agrovetmarket.com</strong>
            </p>
          </div>
        </div>
      )}
      
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-[#714B67] dark:text-purple-400">Letras por Firmar</h1>
          <p className="text-slate-500 dark:text-slate-400 font-medium mt-1">
            Gestión de letras pendientes de aceptación y firma electrónica
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleLogout}
            className="border-red-500 text-red-600 font-bold hover:bg-red-50"
          >
            Cerrar sesión
          </Button>
          {selectedLetters.length > 0 && (
            <>
              <Button 
                onClick={() => setIsPreviewOpen(true)}
                className="bg-[#875A7B] hover:bg-[#714B67] text-white font-bold shadow-lg shadow-purple-200 transition-all active:scale-95"
              >
                <Eye className="mr-2 h-4 w-4" />
                Previsualizar ({selectedLetters.length})
              </Button>
              <Button 
                onClick={handleSendEmails}
                disabled={isSending}
                className="bg-[#714B67] hover:bg-[#5a3c52] text-white font-bold shadow-lg shadow-purple-300 transition-all active:scale-95"
              >
                {isSending ? (
                  <RotateCcw className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Send className="mr-2 h-4 w-4" />
                )}
                Enviar Correos
              </Button>
            </>
          )}
          <Button 
            variant="outline"
            onClick={() => refetch()}
            className="border-[#714B67] text-[#714B67] font-bold hover:bg-[#714B67]/5"
          >
            <RotateCcw className={cn("mr-2 h-4 w-4", isLoading && "animate-spin")} />
            Actualizar
          </Button>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm">
        <div className="flex flex-col md:flex-row gap-4 items-center">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 dark:text-slate-500" />
            <Input 
              placeholder="Buscar por cliente, RUC o número de letra..."
              value={clientFilter}
              onChange={(e) => setClientFilter(e.target.value)}
              className="pl-11 h-12 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:ring-[#714B67] dark:focus:ring-purple-500 rounded-xl text-slate-700 font-medium"
            />
          </div>

          {/* Filtro por Estado */}
          <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl border border-slate-200 dark:border-slate-700">
            {["TODOS", "VIGENTE", "POR VENCER", "VENCIDO"].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={cn(
                  "px-4 py-2 rounded-lg text-xs font-black transition-all",
                  statusFilter === status 
                    ? "bg-white dark:bg-slate-700 text-[#714B67] dark:text-purple-400 shadow-sm scale-105" 
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                )}
              >
                {status}
              </button>
            ))}
          </div>

          <div className="bg-slate-50 dark:bg-slate-800 px-4 py-2 rounded-xl border border-slate-100 dark:border-slate-700 flex items-center gap-3">
            <div className="w-10 h-10 bg-white dark:bg-slate-700 rounded-lg shadow-sm flex items-center justify-center">
              <Mail className="h-5 w-5 text-[#714B67] dark:text-purple-400" />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest font-black text-slate-400 dark:text-slate-500">Total Filtradas</p>
              <p className="text-xl font-black text-[#714B67] dark:text-purple-400">{filteredData.length}</p>
            </div>
          </div>

          {sentLetterIds.size > 0 && (
            <div className="bg-green-50 dark:bg-green-950/30 px-4 py-2 rounded-xl border border-green-100 dark:border-green-900/50 flex items-center gap-3 animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="w-10 h-10 bg-white dark:bg-green-900/50 rounded-lg shadow-sm flex items-center justify-center">
                <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-widest font-black text-green-600 dark:text-green-400">Enviadas hoy</p>
                <div className="flex items-center gap-2">
                  <p className="text-xl font-black text-green-700 dark:text-green-300">{sentLetterIds.size}</p>
                  <button 
                    onClick={() => setSentLetterIds(new Set())}
                    className="text-[9px] font-bold text-green-600 dark:text-green-400 hover:underline ml-1 uppercase"
                  >
                    Reiniciar
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabla de Datos - Estilo Collections */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-[#714B67]/20 dark:border-purple-500/20 shadow-xl overflow-hidden">
        <div className="bg-[#714B67] dark:bg-slate-800 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/10 dark:bg-purple-500/20 rounded-lg">
              <FileText className="h-5 w-5 text-white" />
            </div>
            <h3 className="text-white font-bold tracking-wide">Listado de Letras Pendientes</h3>
          </div>
          {selectedLetters.length > 0 && (
            <Badge className="bg-white dark:bg-purple-500 text-[#714B67] dark:text-white font-black animate-pulse">
              {selectedLetters.length} SELECCIONADAS
            </Badge>
          )}
        </div>
        
        <div className="relative overflow-x-auto overflow-y-auto max-h-[600px]">
          <table className="w-full text-sm text-left border-collapse">
            <thead className="sticky top-0 z-20 bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold border-b border-slate-200 dark:border-slate-700 text-xs uppercase tracking-tighter">
              <tr>
                <th className="px-4 py-4 text-center border-r border-slate-200 dark:border-slate-700 w-12">
                  <input 
                    type="checkbox" 
                    className="h-4 w-4 rounded border-slate-300 text-[#714B67] focus:ring-[#714B67] cursor-pointer"
                    checked={filteredData.length > 0 && selectedLetters.length === filteredData.length}
                    onChange={(e) => toggleAll(e.target.checked)}
                  />
                </th>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">LETRA</th>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">FACTURA</th>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700">CLIENTE</th>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700 text-right">MONTO</th>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700 text-center">F.EMISIÓN</th>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700 text-center">F. VENCIMIENTO</th>
                <th className="px-4 py-4 whitespace-nowrap border-r border-slate-200 dark:border-slate-700 text-center">ESTADO</th>
                <th className="px-4 py-4 whitespace-nowrap text-center">VENDEDOR</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {filteredData.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-20 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Search className="h-10 w-10 text-slate-200 dark:text-slate-700" />
                      <p className="text-slate-400 dark:text-slate-500 font-bold text-lg">No se encontraron letras con ese criterio.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredData.map((row, idx) => (
                  <tr 
                    key={idx} 
                    className={cn(
                      "hover:bg-slate-50 dark:hover:bg-slate-800 transition-all cursor-pointer group",
                      rowSelection[idx] ? "bg-purple-50/50 dark:bg-purple-900/20" : ""
                    )}
                    onClick={() => toggleRow(idx)}
                  >
                    <td className="px-4 py-3 text-center border-r border-slate-100 dark:border-slate-800" onClick={(e) => e.stopPropagation()}>
                      <input 
                        type="checkbox" 
                        className="h-4 w-4 rounded border-slate-300 text-[#714B67] focus:ring-[#714B67] cursor-pointer"
                        checked={!!rowSelection[idx]}
                        onChange={() => toggleRow(idx)}
                      />
                    </td>
                    <td className="px-4 py-3 font-black text-[#714B67] dark:text-purple-400 whitespace-nowrap border-r border-slate-100 dark:border-slate-800 group-hover:underline">
                      <div className="flex items-center gap-2">
                        {row.number}
                        {sentLetterIds.has(row.id) && (
                          <Badge className="bg-green-100 text-green-700 border-green-200 text-[10px] px-1 py-0 h-4">
                            ENVIADO
                          </Badge>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 border-r border-slate-100 dark:border-slate-800 font-bold text-slate-500 dark:text-slate-400 max-w-[150px] truncate">
                      {row.ref_docs}
                    </td>
                    <td className="px-4 py-3 border-r border-slate-100 dark:border-slate-800 font-bold text-slate-700 dark:text-slate-300 max-w-[250px] truncate" title={row.acceptor_id}>
                      {row.acceptor_id}
                    </td>
                    <td className="px-4 py-3 border-r border-slate-100 dark:border-slate-800 text-right font-black text-slate-900 dark:text-slate-100 bg-slate-50/30 dark:bg-slate-800/30 whitespace-nowrap">
                      {formatCurrency(row.amount, row.currency)}
                    </td>
                    <td className="px-4 py-3 border-r border-slate-100 dark:border-slate-800 text-center font-bold text-slate-500 dark:text-slate-400 whitespace-nowrap">
                      {row.invoice_date ? new Date(row.invoice_date).toLocaleDateString("es-PE") : "-"}
                    </td>
                    <td className="px-4 py-3 border-r border-slate-100 dark:border-slate-800 text-center font-bold text-slate-600 dark:text-slate-400 whitespace-nowrap">
                      {row.due_date ? new Date(row.due_date).toLocaleDateString("es-PE") : "-"}
                    </td>
                    <td className="px-4 py-3 border-r border-slate-100 dark:border-slate-800 text-center">
                      <Badge className={cn(
                        "font-black px-3 py-1",
                        getStatusBadgeClass(row.status_calc)
                      )} variant="outline">
                        {normalizeStatus(row.status_calc)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-center text-slate-500 dark:text-slate-400 font-medium truncate max-w-[120px]">
                      {row.salesperson || "-"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {filteredData.length > 0 && (
          <div className="p-4 bg-slate-50 dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 text-xs font-bold text-slate-500 dark:text-slate-400 flex justify-between items-center">
            <span className="flex items-center gap-2 uppercase tracking-tighter">
              <div className="w-2 h-2 rounded-full bg-[#714B67] dark:bg-purple-500"></div>
              Total de registros: {filteredData.length}
            </span>
            <span className="text-[#714B67] dark:text-purple-400 bg-white dark:bg-slate-700 px-3 py-1 rounded-full border border-slate-200 dark:border-slate-600 shadow-sm">
              Sincronizado con Odoo v17
            </span>
          </div>
        )}
      </div>

      {/* Modal de Previsualización (Borrador) */}
      {isPreviewOpen && (
        <div className="fixed inset-0 bg-black/60 dark:bg-black/80 z-[100] flex items-center justify-center p-4 backdrop-blur-md animate-in fade-in duration-300">
          <div className="bg-white dark:bg-slate-900 rounded-[2rem] shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col border border-white/20 dark:border-slate-700">
            <div className="p-8 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-gradient-to-r from-slate-50 to-white dark:from-slate-900 dark:to-slate-800">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#714B67] dark:bg-purple-600 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-200 dark:shadow-purple-900/50">
                  <Mail className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-black text-[#714B67] dark:text-purple-400 leading-none">Borrador de Correo</h2>
                  <p className="text-slate-500 dark:text-slate-400 font-bold mt-1 uppercase tracking-widest text-[10px]">Previsualización Formal</p>
                </div>
              </div>
              <button 
                onClick={() => setIsPreviewOpen(false)}
                className="p-3 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-2xl transition-all active:scale-90"
              >
                <X className="h-6 w-6 text-slate-400 dark:text-slate-500" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-8 space-y-8 bg-slate-50/50 dark:bg-slate-950/50">
              {/* Ejemplo del Correo */}
              {selectedLetters.length > 0 && (
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-3xl shadow-xl overflow-hidden mx-auto max-w-4xl border-t-8 border-t-[#714B67] dark:border-t-purple-600">
                  <div className="p-10 space-y-6 text-slate-700 dark:text-slate-300">
                    <div className="flex justify-between items-start border-b border-slate-100 dark:border-slate-700 pb-6">
                      <div className="h-12">
                        <img src="/img/agrovet-market.png" alt="Agrovet Market" className="h-full w-auto object-contain" />
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase">Fecha de Emisión</p>
                        <p className="text-sm font-bold text-slate-700 dark:text-slate-300">{new Date().toLocaleDateString("es-PE")}</p>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <p className="text-lg">Estimado(a) <strong className="text-slate-900 dark:text-slate-100">{selectedLetters[0].acceptor_id}</strong>,</p>
                      <p className="leading-relaxed">Le saludamos cordialmente del <strong>Área de Créditos y Cobranzas de Agrovet Market S.A.</strong></p>
                      <p className="leading-relaxed bg-blue-50/50 dark:bg-blue-950/30 p-4 rounded-2xl border border-blue-100 dark:border-blue-900 italic text-blue-800 dark:text-blue-300">
                        Adjunto el detalle de las letras que aún se encuentran pendientes de firma, confirmar fecha de recojo.
                      </p>
                    </div>
                    
                    <div className="my-8 border border-slate-200 dark:border-slate-700 rounded-2xl overflow-hidden shadow-sm">
                      <table className="w-full text-sm">
                        <thead className="bg-[#714B67] dark:bg-slate-800 text-white">
                          <tr>
                            <th className="px-4 py-3 text-left font-bold uppercase tracking-tighter text-[10px]">LETRA</th>
                            <th className="px-4 py-3 text-left font-bold uppercase tracking-tighter text-[10px]">FACTURA</th>
                            <th className="px-4 py-3 text-right font-bold uppercase tracking-tighter text-[10px]">MONTO</th>
                            <th className="px-4 py-3 text-center font-bold uppercase tracking-tighter text-[10px]">F.EMISIÓN</th>
                            <th className="px-4 py-3 text-center font-bold uppercase tracking-tighter text-[10px]">VENCIMIENTO</th>
                            <th className="px-4 py-3 text-center font-bold uppercase tracking-tighter text-[10px]">ESTADO</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                          {selectedLetters
                            .filter(l => l.acceptor_id === selectedLetters[0].acceptor_id)
                            .map(letter => (
                              <tr key={letter.id}>
                                <td className="px-4 py-4 font-black text-[#714B67] dark:text-purple-400">{letter.number}</td>
                                <td className="px-4 py-4 font-bold text-slate-500 dark:text-slate-400">{letter.ref_docs}</td>
                                <td className="px-4 py-4 text-right font-black text-slate-900 dark:text-slate-100 whitespace-nowrap">
                                  {formatCurrency(letter.amount, letter.currency)}
                                </td>
                                <td className="px-4 py-4 text-center font-bold text-slate-500 dark:text-slate-400 whitespace-nowrap">
                                  {letter.invoice_date ? new Date(letter.invoice_date).toLocaleDateString("es-PE") : "-"}
                                </td>
                                <td className="px-4 py-4 text-center font-bold text-slate-600 dark:text-slate-400 whitespace-nowrap">
                                  {new Date(letter.due_date).toLocaleDateString("es-PE")}
                                </td>
                                <td className="px-4 py-4 text-center">
                                  <span className={cn(
                                    "inline-flex items-center rounded-full border text-[10px] font-black px-2 py-1",
                                    getStatusBadgeClass(letter.status_calc)
                                  )}>
                                    {normalizeStatus(letter.status_calc)}
                                  </span>
                                </td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="space-y-4 border-t border-slate-100 dark:border-slate-700 pt-6">
                      <p className="font-medium">Agradecemos su pronta atención a este requerimiento para evitar cualquier inconveniente en la aprobación de su próximo pedido.</p>
                      <div className="pt-4">
                        <p className="font-black text-[#714B67] dark:text-purple-400 text-lg">Créditos y Cobranzas</p>
                        <p className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Agrovet Market S.A.</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="text-center p-4 bg-[#714B67]/5 dark:bg-purple-950/30 rounded-2xl border border-[#714B67]/10 dark:border-purple-800/30">
                <p className="text-xs text-[#714B67] dark:text-purple-400 font-black uppercase tracking-widest flex items-center justify-center gap-2">
                  <CheckCircle2 className="h-4 w-4" />
                  Envío Consolidado Automático
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 font-bold mt-1">
                  Se enviarán correos individuales a cada uno de los {new Set(selectedLetters.map(l => l.acceptor_id)).size} clientes seleccionados.
                </p>
              </div>
            </div>

            <div className="p-8 border-t border-slate-100 dark:border-slate-800 flex flex-col md:flex-row justify-end gap-4 bg-white dark:bg-slate-900">
              <Button 
                variant="outline" 
                onClick={() => setIsPreviewOpen(false)}
                className="h-12 px-8 rounded-xl font-bold border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                Cerrar Borrador
              </Button>
              <Button 
                onClick={handleSendEmails}
                disabled={isSending}
                className="h-12 bg-[#714B67] hover:bg-[#5a3c52] dark:bg-purple-600 dark:hover:bg-purple-700 text-white font-black px-10 rounded-xl shadow-xl shadow-purple-200 dark:shadow-purple-900/50 transition-all active:scale-95 flex items-center gap-2"
              >
                {isSending ? (
                  <RotateCcw className="h-5 w-5 animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
                CONFIRMAR ENVÍO A {selectedLetters.length} LETRAS
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Confirmación (Pre-Envío) */}
      {isConfirmOpen && (
        <div className="fixed inset-0 bg-black/40 z-[110] flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-sm overflow-hidden border border-slate-200 dark:border-slate-800">
            <div className="p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-50 dark:bg-purple-900/30 rounded-full flex items-center justify-center text-xl">
                  📬
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">¿Confirmar envío?</h2>
                  <p className="text-xs text-slate-500 font-medium italic">Preparado para enviar {selectedLetters.length} letras</p>
                </div>
              </div>

              {alreadySentInSelection.length > 0 && (
                <div className="p-3 bg-red-50 dark:bg-red-950/30 rounded-xl border border-red-100 dark:border-red-900/50 flex items-start gap-2">
                  <div className="text-red-600 mt-0.5 font-bold">⚠️</div>
                  <div className="flex-1">
                    <p className="text-[10px] text-red-800 dark:text-red-300 font-black uppercase">¡Atención: Duplicados!</p>
                    <p className="text-[10px] text-red-700/80 dark:text-red-400 leading-tight mt-0.5">
                      Hay <strong>{alreadySentInSelection.length}</strong> letras que ya fueron enviadas en esta sesión. ¿Deseas enviarlas nuevamente?
                    </p>
                  </div>
                </div>
              )}

              {isDev && (
                <div className="p-3 bg-amber-50 dark:bg-amber-950/30 rounded-xl border border-amber-100 dark:border-amber-900/50">
                  <p className="text-[10px] text-amber-800 dark:text-amber-300 leading-tight">
                    <span className="font-bold uppercase mr-1">Modo Dev:</span> 
                    Los correos se redirigirán a creditosycobranzas@agrovetmarket.com
                  </p>
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <Button 
                  onClick={() => setIsConfirmOpen(false)}
                  variant="outline" 
                  className="flex-1 h-10 text-xs font-bold rounded-lg border-slate-200"
                >
                  Cancelar
                </Button>
                <Button 
                  onClick={executeSendEmails}
                  className="flex-1 h-10 text-xs font-bold bg-[#714B67] hover:bg-[#5a3c52] text-white rounded-lg shadow-md transition-all active:scale-95"
                >
                  Enviar
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Éxito (Post-Envío) */}
      {isSuccessOpen && (
        <div className="fixed inset-0 bg-black/40 z-[110] flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in zoom-in duration-200">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-sm overflow-hidden border border-slate-200 dark:border-slate-800">
            <div className="p-6 text-center space-y-4">
              <div className="mx-auto w-12 h-12 bg-green-50 dark:bg-green-900/30 rounded-full flex items-center justify-center">
                <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">¡Envío exitoso!</h2>
                <p className="text-xs text-slate-500 font-medium mt-1">
                  Se enviaron <span className="font-bold text-slate-700 dark:text-slate-300">{lastSentCount}</span> correos correctamente.
                </p>
              </div>

              <Button 
                onClick={() => setIsSuccessOpen(false)}
                className="w-full h-10 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 font-bold text-xs rounded-lg transition-all active:scale-95"
              >
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Error */}
      {isErrorOpen && (
        <div className="fixed inset-0 bg-black/40 z-[120] flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in zoom-in duration-200">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-sm overflow-hidden border border-slate-200 dark:border-slate-800">
            <div className="p-6 text-center space-y-4">
              <div className="mx-auto w-12 h-12 bg-red-50 dark:bg-red-900/30 rounded-full flex items-center justify-center">
                <X className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
              
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">Hubo un error</h2>
                <p className="text-[11px] text-slate-500 font-medium mt-1 leading-tight">
                  {errorMessage}
                </p>
              </div>

              <Button 
                onClick={() => setIsErrorOpen(false)}
                className="w-full h-10 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded-lg transition-all active:scale-95"
              >
                Entendido
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
