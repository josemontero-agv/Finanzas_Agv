"use client"

import { Suspense, useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Image from "next/image"
import { authApi, FLASK_API_URL } from "@/lib/api"
import { AuthLoadingScreen } from "@/components/auth-loading-screen"

const ERROR_MESSAGES: Record<string, string> = {
  not_allowed: "Tu cuenta de Google no está autorizada para acceder a Finanzas AGV.",
  google_auth_failed: "No se pudo completar el inicio de sesión con Google. Intenta nuevamente.",
}

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [isLoading, setIsLoading] = useState(false)

  const error = searchParams.get("error")
  const errorMessage = error ? ERROR_MESSAGES[error] || "No se pudo iniciar sesión" : ""

  useEffect(() => {
    const verifySession = async () => {
      try {
        const response = await authApi.getUserInfo()
        if (response.data.success) {
          router.replace("/collections")
        }
      } catch {
        // Sin sesión activa: usuario permanece en login.
      }
    }

    verifySession()
  }, [router])

  if (isLoading) {
    return <AuthLoadingScreen message="Iniciando sesión..." />
  }

  const handleGoogleLogin = () => {
    setIsLoading(true)
    window.location.href = `${FLASK_API_URL}/api/v1/auth/google`
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl p-8">
        <div className="mb-6 text-center">
          <div className="flex justify-center mb-5">
            <Image
              src="/docs/assets/logo-agrovet.png"
              alt="Agrovet Market"
              width={290}
              height={90}
              priority
              className="h-auto w-auto max-w-[290px]"
            />
          </div>
          <h1 className="text-2xl font-black text-[#714B67] dark:text-purple-400">Acceso Finanzas AGV</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
            Ingresa con tu cuenta corporativa de Google
          </p>
        </div>

        {errorMessage && (
          <div className="mb-4 rounded-lg border border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300 text-sm px-3 py-2">
            {errorMessage}
          </div>
        )}

        <button
          type="button"
          onClick={handleGoogleLogin}
          className="w-full flex items-center justify-center gap-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-semibold py-3 px-4 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M23.49 12.27c0-.79-.07-1.54-.19-2.27H12v4.51h6.47c-.29 1.48-1.14 2.73-2.4 3.58v2.97h3.86c2.26-2.09 3.56-5.17 3.56-8.79z"
            />
            <path
              fill="#34A853"
              d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.86-2.97c-1.08.72-2.46 1.16-4.07 1.16-3.13 0-5.78-2.11-6.73-4.96H1.27v3.09C3.25 21.3 7.31 24 12 24z"
            />
            <path
              fill="#FBBC05"
              d="M5.27 14.32c-.24-.72-.38-1.49-.38-2.32s.14-1.6.38-2.32V6.59H1.27A11.96 11.96 0 000 12c0 1.93.46 3.76 1.27 5.41z"
            />
            <path
              fill="#EA4335"
              d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.7 1.27 6.59l4 3.09c.95-2.85 3.6-4.93 6.73-4.93z"
            />
          </svg>
          Iniciar sesión con Google
        </button>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<AuthLoadingScreen message="Cargando..." />}>
      <LoginForm />
    </Suspense>
  )
}
