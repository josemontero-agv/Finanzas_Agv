"use client"

/**
 * Pantalla de carga estándar para flujos de autenticación.
 * Mismo diseño en: guard de rutas protegidas (Validando sesión) y envío de login (Iniciando sesión).
 */
export function AuthLoadingScreen({ message = "Validando sesión..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 via-purple-50/30 to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 transition-all duration-300">
      <div className="animate-spin rounded-full h-12 w-12 border-2 border-[#714B67] dark:border-purple-400 border-t-transparent" />
      <p className="mt-4 text-lg font-semibold text-slate-700 dark:text-slate-300">{message}</p>
    </div>
  )
}
