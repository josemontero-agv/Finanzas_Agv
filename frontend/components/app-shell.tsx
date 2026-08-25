"use client"

import { usePathname, useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { useEffect, useRef } from "react"
import { Sidebar } from "@/components/sidebar"
import { AuthLoadingScreen } from "@/components/auth-loading-screen"
import { authApi } from "@/lib/api"
import { trackPageView } from "@/lib/analytics"
import { ReactNode } from "react"

type AppShellProps = {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname()
  const router = useRouter()
  const isLoginRoute = pathname === "/login"
  const lastPathRef = useRef<string | null>(null)

  const {
    data: authData,
    isLoading: isAuthLoading,
    isError: isAuthError,
    error: authError,
  } = useQuery({
    queryKey: ["auth", "user-info"],
    queryFn: async () => {
      const res = await authApi.getUserInfo()
      return res.data
    },
    retry: false,
    staleTime: 60_000,
    enabled: !isLoginRoute,
  })

  useEffect(() => {
    if (!isLoginRoute && isAuthError && authError && (authError as { response?: { status?: number } })?.response?.status === 401) {
      router.replace("/login")
    }
  }, [isLoginRoute, isAuthError, authError, router])

  useEffect(() => {
    if (isLoginRoute || !authData?.success || !pathname) return
    if (lastPathRef.current === pathname) return
    lastPathRef.current = pathname
    trackPageView(pathname)
  }, [pathname, authData?.success, isLoginRoute])

  if (isLoginRoute) {
    return (
      <main className="min-h-screen p-4 md:p-8 bg-gradient-to-br from-slate-50 via-purple-50/30 to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 transition-all duration-300">
        {children}
      </main>
    )
  }

  if (isAuthLoading || (isAuthError && (authError as { response?: { status?: number } })?.response?.status === 401)) {
    return <AuthLoadingScreen message="Validando sesión..." />
  }

  if (isAuthError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 via-purple-50/30 to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
        <p className="text-lg font-semibold text-red-600 dark:text-red-400">No se pudo validar la sesión.</p>
        <button
          type="button"
          onClick={() => router.replace("/login")}
          className="mt-4 px-4 py-2 rounded-lg bg-[#714B67] dark:bg-purple-600 text-white hover:opacity-90"
        >
          Ir a inicio de sesión
        </button>
      </div>
    )
  }

  if (!authData?.success) {
    return <AuthLoadingScreen message="Validando sesión..." />
  }

  const roles = authData.roles || []
  const isAdmin = roles.includes("admin")
  const canManageApps = isAdmin || roles.includes("app_assistant")

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar isAdmin={isAdmin} canManageApps={canManageApps} />
      <main className="flex-1 overflow-y-auto p-4 md:p-8 bg-gradient-to-br from-slate-50 via-purple-50/30 to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 transition-all duration-300">
        {children}
      </main>
    </div>
  )
}
