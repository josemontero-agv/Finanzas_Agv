"use client"

import { AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ErrorFallbackProps {
  error?: Error | null
  resetError?: () => void
  title?: string
  message?: string
}

export function ErrorFallback({ 
  error, 
  resetError,
  title = "Error al cargar datos",
  message 
}: ErrorFallbackProps) {
  return (
    <div className="flex items-center justify-center h-full min-h-[400px]">
      <div className="text-center max-w-md">
        <AlertCircle className="mx-auto h-12 w-12 text-red-500 dark:text-red-400" />
        <h2 className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
        <p className="text-sm text-muted-foreground mt-2">
          {message || error?.message || "Ocurrió un error inesperado"}
        </p>
        
        {error && (
          <details className="mt-4 text-left">
            <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
              Ver detalles técnicos
            </summary>
            <pre className="mt-2 text-xs bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 p-3 rounded overflow-auto max-h-40">
              {error.stack || error.message}
            </pre>
          </details>
        )}
        
        {resetError && (
          <Button
            onClick={resetError}
            className="mt-4"
            size="sm"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Reintentar
          </Button>
        )}
        
        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg text-left transition-colors duration-300">
          <p className="text-xs font-semibold text-blue-900 dark:text-blue-300 mb-2">💡 Sugerencias:</p>
          <ul className="text-xs text-blue-800 dark:text-blue-400 space-y-1">
            <li>• Verifica que el backend Flask esté corriendo en puerto 5000</li>
            <li>• Revisa que Supabase tenga datos sincronizados</li>
            <li>• Ejecuta el ETL: <code className="bg-blue-100 dark:bg-blue-900/30 px-1 rounded">python scripts/etl/etl_sync_threading.py</code></li>
          </ul>
        </div>
      </div>
    </div>
  )
}
