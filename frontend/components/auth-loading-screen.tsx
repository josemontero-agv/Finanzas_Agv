"use client"

/**
 * Única pantalla de carga de la app: fondo oscuro, spinner morado, texto centrado.
 * Se usa en: guard de sesión, login, y carga de Letras (con mensaje + subtítulo).
 */
export function AuthLoadingScreen({
  message = "Validando sesión...",
  subtitle,
}: {
  message?: string
  subtitle?: string
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#1A1A2E]">
      <div className="animate-spin rounded-full h-12 w-12 border-2 border-purple-400 border-t-transparent" />
      <p className="mt-4 text-lg font-semibold text-white">{message}</p>
      {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
    </div>
  )
}
