"use client"

import { useQuery } from "@tanstack/react-query"
import { supabase } from "@/lib/supabase"
import { healthApi } from "@/lib/api"
import { CheckCircle, XCircle, AlertCircle, Activity } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

export default function DiagnosticsPage() {
  // Test Supabase tables
  const { data: movesCount } = useQuery({
    queryKey: ["diagnostics", "moves"],
    queryFn: async () => {
      const { count, error } = await supabase
        .from("fact_moves")
        .select("*", { count: "exact", head: true })
      
      if (error) throw error
      return count
    },
  })

  const { data: lettersCount } = useQuery({
    queryKey: ["diagnostics", "letters"],
    queryFn: async () => {
      const { count, error } = await supabase
        .from("fact_letters")
        .select("*", { count: "exact", head: true })
      
      if (error) throw error
      return count
    },
  })

  const { data: partnersCount } = useQuery({
    queryKey: ["diagnostics", "partners"],
    queryFn: async () => {
      const { count, error } = await supabase
        .from("dim_partners")
        .select("*", { count: "exact", head: true })
      
      if (error) throw error
      return count
    },
  })

  // Test Flask API
  const { data: flaskHealth, error: flaskError } = useQuery({
    queryKey: ["diagnostics", "flask"],
    queryFn: async () => {
      const response = await healthApi.check()
      return response.data
    },
    retry: false,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">Diagnóstico del Sistema</h1>
        <p className="text-muted-foreground mt-2">
          Verificación de conexiones y datos disponibles
        </p>
      </div>

      {/* Supabase Tables */}
      <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm transition-colors duration-300">
        <h2 className="text-xl font-bold mb-6 text-[#714B67] dark:text-purple-400 flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Tablas de Supabase (Cloud)
        </h2>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700 flex flex-col items-center text-center transition-colors duration-300">
            {movesCount !== undefined && movesCount > 0 ? (
              <CheckCircle className="h-8 w-8 text-green-500 dark:text-green-400 mb-2" />
            ) : movesCount === 0 ? (
              <AlertCircle className="h-8 w-8 text-yellow-500 dark:text-yellow-400 mb-2" />
            ) : (
              <XCircle className="h-8 w-8 text-red-500 dark:text-red-400 mb-2" />
            )}
            <p className="font-bold text-slate-800 dark:text-slate-200 text-lg">fact_moves</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider font-semibold">Facturas y Notas</p>
            <Badge variant="outline" className="bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-600">
              {movesCount !== undefined ? `${movesCount} registros` : "Error"}
            </Badge>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700 flex flex-col items-center text-center transition-colors duration-300">
            {lettersCount !== undefined && lettersCount > 0 ? (
              <CheckCircle className="h-8 w-8 text-green-500 dark:text-green-400 mb-2" />
            ) : lettersCount === 0 ? (
              <AlertCircle className="h-8 w-8 text-yellow-500 dark:text-yellow-400 mb-2" />
            ) : (
              <XCircle className="h-8 w-8 text-red-500 dark:text-red-400 mb-2" />
            )}
            <p className="font-bold text-slate-800 dark:text-slate-200 text-lg">fact_letters</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider font-semibold">Letras de Cambio</p>
            <Badge variant="outline" className="bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-600">
              {lettersCount !== undefined ? `${lettersCount} registros` : "Error"}
            </Badge>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700 flex flex-col items-center text-center transition-colors duration-300">
            {partnersCount !== undefined && partnersCount > 0 ? (
              <CheckCircle className="h-8 w-8 text-green-500 dark:text-green-400 mb-2" />
            ) : partnersCount === 0 ? (
              <AlertCircle className="h-8 w-8 text-yellow-500 dark:text-yellow-400 mb-2" />
            ) : (
              <XCircle className="h-8 w-8 text-red-500 dark:text-red-400 mb-2" />
            )}
            <p className="font-bold text-slate-800 dark:text-slate-200 text-lg">dim_partners</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider font-semibold">Clientes/Proveedores</p>
            <Badge variant="outline" className="bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-600">
              {partnersCount !== undefined ? `${partnersCount} registros` : "Error"}
            </Badge>
          </div>
        </div>
      </div>

      {/* Flask API Status */}
      <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm transition-colors duration-300">
        <h2 className="text-xl font-bold mb-6 text-[#714B67] dark:text-purple-400 flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Backend Flask API (Local)
        </h2>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700 flex flex-col items-center text-center transition-colors duration-300">
            {flaskHealth && !flaskError ? (
              <CheckCircle className="h-8 w-8 text-green-500 dark:text-green-400 mb-2" />
            ) : (
              <XCircle className="h-8 w-8 text-red-500 dark:text-red-400 mb-2" />
            )}
            <p className="font-bold text-slate-800 dark:text-slate-200 text-lg">Flask API</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider font-semibold">http://localhost:5000</p>
            <Badge className={cn(
              "font-bold",
              flaskHealth ? "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300" : "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
            )}>
              {flaskHealth ? "En línea" : "Desconectado"}
            </Badge>
          </div>

          {flaskHealth && (
            <>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700 flex flex-col items-center text-center transition-colors duration-300">
                {flaskHealth.services?.odoo === "connected" ? (
                  <CheckCircle className="h-8 w-8 text-green-500 dark:text-green-400 mb-2" />
                ) : (
                  <XCircle className="h-8 w-8 text-red-500 dark:text-red-400 mb-2" />
                )}
                <p className="font-bold text-slate-800 dark:text-slate-200 text-lg">Odoo ERP</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider font-semibold">XML-RPC (Odoo v17)</p>
                <Badge className={cn(
                  "font-bold",
                  flaskHealth.services?.odoo === "connected" ? "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300" : "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
                )}>
                  {flaskHealth.services?.odoo || "disconnected"}
                </Badge>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700 flex flex-col items-center text-center transition-colors duration-300">
                {flaskHealth.services?.supabase === "connected" ? (
                  <CheckCircle className="h-8 w-8 text-green-500 dark:text-green-400 mb-2" />
                ) : (
                  <XCircle className="h-8 w-8 text-red-500 dark:text-red-400 mb-2" />
                )}
                <p className="font-bold text-slate-800 dark:text-slate-200 text-lg">Supabase (desde Flask)</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider font-semibold">PostgreSQL Client</p>
                <Badge className={cn(
                  "font-bold",
                  flaskHealth.services?.supabase === "connected" ? "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300" : "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
                )}>
                  {flaskHealth.services?.supabase || "disconnected"}
                </Badge>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Recomendaciones */}
      {(movesCount === 0 || lettersCount === 0) && (
        <div className="bg-yellow-50 dark:bg-yellow-950/30 border border-yellow-200 dark:border-yellow-800 p-6 rounded-lg transition-colors duration-300">
          <h3 className="font-semibold text-yellow-900 dark:text-yellow-300 mb-2">⚠️ Tablas vacías detectadas</h3>
          <p className="text-sm text-yellow-800 dark:text-yellow-400 mb-3">
            Las tablas de Supabase no tienen datos. Ejecuta el ETL para sincronizar:
          </p>
          <pre className="bg-yellow-100 dark:bg-yellow-900/30 p-3 rounded text-xs text-yellow-900 dark:text-yellow-300">
            .\venv\Scripts\Activate.ps1{"\n"}
            python scripts/etl/etl_sync_threading.py
          </pre>
        </div>
      )}

      {flaskError && (
        <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 p-6 rounded-lg transition-colors duration-300">
          <h3 className="font-semibold text-blue-900 dark:text-blue-300 mb-2">ℹ️ Flask API no disponible</h3>
          <p className="text-sm text-blue-800 dark:text-blue-400 mb-3">
            El frontend funciona con Supabase directo. Para habilitar funciones avanzadas, inicia Flask:
          </p>
          <pre className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded text-xs text-blue-900 dark:text-blue-300">
            .\venv\Scripts\Activate.ps1{"\n"}
            python run.py
          </pre>
        </div>
      )}
    </div>
  )
}
