"use client"

import { FormEvent, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import axios from "axios"
import Image from "next/image"
import { authApi } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")

  useEffect(() => {
    const verifySession = async () => {
      try {
        const response = await authApi.getUserInfo()
        if (response.data.success) {
          router.replace("/letters")
        }
      } catch {
        // Sin sesión activa: usuario permanece en login.
      }
    }

    verifySession()
  }, [router])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setErrorMessage("")
    setIsLoading(true)

    try {
      const response = await authApi.login(username, password)
      if (response.data.success) {
        router.replace("/letters")
        return
      }

      setErrorMessage(response.data.message || "No se pudo iniciar sesión")
    } catch (error) {
      if (axios.isAxiosError(error)) {
        setErrorMessage(error.response?.data?.message || "Credenciales inválidas")
      } else {
        setErrorMessage("Error inesperado al iniciar sesión")
      }
    } finally {
      setIsLoading(false)
    }
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
          <h1 className="text-2xl font-black text-[#714B67] dark:text-purple-400">Acceso Letras AGV</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
            Ingresa con tu usuario de Odoo
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Usuario</label>
            <Input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="usuario o correo corporativo"
              autoComplete="username"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Contraseña</label>
            <Input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="******"
              autoComplete="current-password"
              required
            />
          </div>

          {errorMessage && (
            <div className="rounded-lg border border-red-300 bg-red-50 text-red-700 text-sm px-3 py-2">
              {errorMessage}
            </div>
          )}

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full bg-[#714B67] hover:bg-[#5a3c52] text-white font-bold"
          >
            {isLoading ? "Validando..." : "Ingresar"}
          </Button>
        </form>
      </div>
    </div>
  )
}
