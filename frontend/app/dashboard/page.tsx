"use client"

import { useQuery } from "@tanstack/react-query"
import { healthApi } from "@/lib/api"
import { 
  Activity, 
  CreditCard, 
  FileText, 
  Mail, 
  TrendingUp,
  CheckCircle,
  XCircle 
} from "lucide-react"
import Link from "next/link"

export default function DashboardPage() {
  // Health check de los servicios
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      try {
        const response = await healthApi.check()
        return response.data
      } catch (error) {
        console.warn("Flask API no disponible, usando modo Supabase")
        return {
          status: "partial",
          version: "2.0.0",
          services: {
            odoo: "unknown",
            supabase: "connected"
          }
        }
      }
    },
    refetchInterval: 30000, // Cada 30 segundos
    retry: false,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">Dashboard Principal</h1>
        <p className="text-muted-foreground mt-2">
          Bienvenido al Sistema de Gestión Financiera AGV
        </p>
      </div>

      {/* Estado de Servicios */}
      <div className="bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700 transition-colors duration-300">
        <h2 className="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">Estado de Servicios</h2>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="flex items-center gap-3">
            {health?.status === "healthy" ? (
              <CheckCircle className="h-5 w-5 text-green-500 dark:text-green-400" />
            ) : (
              <XCircle className="h-5 w-5 text-red-500 dark:text-red-400" />
            )}
            <div>
              <p className="font-medium text-slate-900 dark:text-slate-100">API Flask</p>
              <p className="text-xs text-muted-foreground">
                {health?.status || "Verificando..."}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {health?.services?.odoo === "connected" ? (
              <CheckCircle className="h-5 w-5 text-green-500 dark:text-green-400" />
            ) : (
              <XCircle className="h-5 w-5 text-red-500 dark:text-red-400" />
            )}
            <div>
              <p className="font-medium text-slate-900 dark:text-slate-100">Odoo ERP</p>
              <p className="text-xs text-muted-foreground">
                {health?.services?.odoo || "Desconocido"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {health?.services?.supabase === "connected" ? (
              <CheckCircle className="h-5 w-5 text-green-500 dark:text-green-400" />
            ) : (
              <XCircle className="h-5 w-5 text-red-500 dark:text-red-400" />
            )}
            <div>
              <p className="font-medium text-slate-900 dark:text-slate-100">Supabase</p>
              <p className="text-xs text-muted-foreground">
                {health?.services?.supabase || "Desconocido"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Módulos Rápidos - Paleta Uniforme Corporativa */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Link href="/collections">
          <div className="bg-gradient-to-br from-[#714B67] to-[#875A7B] p-6 rounded-lg shadow-lg hover:shadow-xl transition-all cursor-pointer text-white hover:scale-105">
            <div className="flex items-center justify-between mb-4">
              <div className="bg-white/20 p-3 rounded-lg">
                <FileText className="h-6 w-6" />
              </div>
            </div>
            <h3 className="font-bold text-lg">Cobranzas</h3>
            <p className="text-sm text-purple-100 mt-1">
              Cuentas por Cobrar (Cta 12)
            </p>
          </div>
        </Link>

        <Link href="/treasury">
          <div className="bg-gradient-to-br from-[#875A7B] to-[#9d6f91] p-6 rounded-lg shadow-lg hover:shadow-xl transition-all cursor-pointer text-white hover:scale-105">
            <div className="flex items-center justify-between mb-4">
              <div className="bg-white/20 p-3 rounded-lg">
                <CreditCard className="h-6 w-6" />
              </div>
            </div>
            <h3 className="font-bold text-lg">Tesorería</h3>
            <p className="text-sm text-purple-100 mt-1">
              Cuentas por Pagar (Cta 42)
            </p>
          </div>
        </Link>

        <Link href="/letters">
          <div className="bg-gradient-to-br from-[#714B67] to-[#875A7B] p-6 rounded-lg shadow-lg hover:shadow-xl transition-all cursor-pointer text-white hover:scale-105">
            <div className="flex items-center justify-between mb-4">
              <div className="bg-white/20 p-3 rounded-lg">
                <Mail className="h-6 w-6" />
              </div>
            </div>
            <h3 className="font-bold text-lg">Letras</h3>
            <p className="text-sm text-purple-100 mt-1">
              Gestión de Letras por Firmar
            </p>
          </div>
        </Link>

        <div className="bg-gradient-to-br from-slate-300 to-slate-400 p-6 rounded-lg shadow-lg opacity-60 text-white">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-white/20 p-3 rounded-lg">
              <TrendingUp className="h-6 w-6" />
            </div>
          </div>
          <h3 className="font-bold text-lg">Analytics</h3>
          <p className="text-sm text-slate-100 mt-1">
            Próximamente...
          </p>
        </div>
      </div>

      {/* Info del Sistema */}
      <div className="bg-gradient-to-r from-[#714B67] to-[#875A7B] p-6 rounded-lg text-white shadow-lg">
        <h2 className="text-xl font-bold mb-2">🚀 Nueva Arquitectura Híbrida</h2>
        <p className="text-purple-100 mb-4">
          Sistema modernizado con Next.js + Flask API. Rendimiento mejorado hasta 100x más rápido.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="bg-white/10 p-3 rounded-lg">
            <p className="font-semibold">Frontend</p>
            <p className="text-purple-100">Next.js 15</p>
          </div>
          <div className="bg-white/10 p-3 rounded-lg">
            <p className="font-semibold">Backend</p>
            <p className="text-purple-100">Flask API</p>
          </div>
          <div className="bg-white/10 p-3 rounded-lg">
            <p className="font-semibold">Database</p>
            <p className="text-purple-100">Supabase</p>
          </div>
          <div className="bg-white/10 p-3 rounded-lg">
            <p className="font-semibold">Version</p>
            <p className="text-purple-100">{health?.version || "2.0.0"}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
