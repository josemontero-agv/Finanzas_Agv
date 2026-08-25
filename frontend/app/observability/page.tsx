"use client"

import { useEffect, useMemo, useState, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { Activity, CalendarDays, LogIn, ShieldAlert, Users } from "lucide-react"
import { authApi, analyticsApi, type AnalyticsEvent, type UserAdminAction } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ErrorFallback } from "@/components/error-fallback"

const CHART_PRIMARY = "#714B67"
const CHART_SECONDARY = "#875A7B"

function limaDate(d: Date): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Lima",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(d)
}

function defaultRange() {
  const to = new Date()
  const from = new Date()
  from.setDate(to.getDate() - 30)
  return { from: limaDate(from), to: limaDate(to) }
}

const EVENT_LABELS: Record<string, string> = {
  user_login_success: "Login",
  user_login_failure: "Login fallido",
  user_logout: "Logout",
  page_view: "Vista de página",
  user_created: "Alta de usuario",
  user_updated: "Edición de usuario",
  user_toggled: "Activación / desactivación",
}

function eventLabel(name?: string): string {
  if (!name) return "—"
  return EVENT_LABELS[name] || name
}

function formatLima(iso?: string): string {
  if (!iso) return "—"
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return "—"
  return d.toLocaleString("es-PE", { timeZone: "America/Lima" })
}

function eventDetail(ev: AnalyticsEvent): string {
  const payload = ev.payload || {}
  if (ev.event_name === "page_view") {
    return String(payload.path || ev.path || payload.module || "—")
  }
  if (ev.event_name === "user_login_failure") {
    return String(payload.error_code || "—")
  }
  if (ev.event_name === "user_created") {
    return `${payload.target_email || ""} · rol ${payload.role || "?"} · ${
      payload.is_active ? "activo" : "inactivo"
    }`.trim()
  }
  if (ev.event_name === "user_toggled") {
    return `${payload.target_email || ""} · ${payload.is_active ? "activo" : "inactivo"}`.trim()
  }
  if (ev.event_name === "user_updated") {
    return adminActionDetail({
      event_name: ev.event_name,
      target_email: String(payload.target_email || ""),
      payload,
    })
  }
  return "—"
}

function adminActionDetail(action: UserAdminAction): string {
  const payload = action.payload || {}
  if (action.event_name === "user_created") {
    return `rol ${payload.role || "?"} · ${payload.is_active ? "activo" : "inactivo"}`
  }
  if (action.event_name === "user_toggled") {
    return payload.is_active ? "activado" : "desactivado"
  }
  if (action.event_name === "user_updated") {
    const fields = Array.isArray(payload.fields) ? payload.fields.join(", ") : ""
    const oldVal = payload.old && typeof payload.old === "object" ? JSON.stringify(payload.old) : ""
    const newVal = payload.new && typeof payload.new === "object" ? JSON.stringify(payload.new) : ""
    if (fields) return `${fields}: ${oldVal} → ${newVal}`
  }
  return "—"
}

export default function ObservabilityPage() {
  const router = useRouter()
  const defaults = useMemo(() => defaultRange(), [])
  const [from, setFrom] = useState(defaults.from)
  const [to, setTo] = useState(defaults.to)
  const [applied, setApplied] = useState(defaults)

  const { data: authData, isLoading: authLoading } = useQuery({
    queryKey: ["auth", "user-info"],
    queryFn: async () => {
      const res = await authApi.getUserInfo()
      return res.data
    },
    staleTime: 60_000,
  })

  const isAdmin = (authData?.roles || []).includes("admin")

  useEffect(() => {
    if (!authLoading && authData?.success && !isAdmin) {
      router.replace("/collections")
    }
  }, [authLoading, authData, isAdmin, router])

  const {
    data: summary,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["analytics", "summary", applied.from, applied.to],
    queryFn: async () => {
      const res = await analyticsApi.getSummary({ from: applied.from, to: applied.to })
      return res.data.data
    },
    enabled: isAdmin,
    retry: 1,
  })

  if (authLoading || (!isAdmin && authData?.success)) {
    return (
      <div className="flex items-center justify-center min-h-[40vh] text-muted-foreground">
        Validando permisos...
      </div>
    )
  }

  if (!isAdmin) {
    return null
  }

  if (error) {
    return (
      <ErrorFallback
        error={error instanceof Error ? error : null}
        title="Error al cargar Observabilidad"
        message="No se pudieron obtener los agregados de uso. Verifica que la tabla user_activity_logs exista en Supabase."
      />
    )
  }

  const kpis = summary?.kpis
  const loginsByHour = summary?.logins_by_hour || []
  const loginsByDay = summary?.logins_by_day || []
  const topUsers = summary?.top_users || []
  const topModules = summary?.top_modules || []
  const recentEvents = summary?.recent_events || []
  const adminActions = summary?.user_admin_actions || []

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[#714B67] dark:text-purple-400">
            Observabilidad
          </h1>
          <p className="text-muted-foreground dark:text-slate-400 mt-2">
            Uso de la aplicación: logins, personas, horarios y módulos visitados
          </p>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 flex flex-col md:flex-row gap-3 items-end">
        <div className="flex-1 w-full">
          <label className="text-xs font-medium text-slate-600 dark:text-slate-300">Desde</label>
          <Input
            type="date"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
            className="mt-1"
          />
        </div>
        <div className="flex-1 w-full">
          <label className="text-xs font-medium text-slate-600 dark:text-slate-300">Hasta</label>
          <Input
            type="date"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            className="mt-1"
          />
        </div>
        <Button
          className="bg-[#714B67] hover:bg-[#875A7B] dark:bg-purple-600 dark:hover:bg-purple-700"
          onClick={() => {
            setApplied({ from, to })
            void refetch()
          }}
        >
          Aplicar rango
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <KpiCard
          title="Usuarios únicos"
          value={kpis?.unique_users ?? (isLoading ? "…" : 0)}
          icon={<Users className="h-5 w-5" />}
        />
        <KpiCard
          title="Logins"
          value={kpis?.total_logins ?? (isLoading ? "…" : 0)}
          icon={<LogIn className="h-5 w-5" />}
        />
        <KpiCard
          title="Logins fallidos"
          value={kpis?.failed_logins ?? (isLoading ? "…" : 0)}
          icon={<ShieldAlert className="h-5 w-5" />}
        />
        <KpiCard
          title="Page views"
          value={kpis?.total_page_views ?? (isLoading ? "…" : 0)}
          icon={<Activity className="h-5 w-5" />}
        />
        <KpiCard
          title="Días activos"
          value={kpis?.active_days ?? (isLoading ? "…" : 0)}
          icon={<CalendarDays className="h-5 w-5" />}
        />
      </div>

      {!isLoading && kpis?.total_logins === 0 && (
        <div
          role="status"
          className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-100"
        >
          Sin eventos de login registrados en el rango. Los logins previos a la
          telemetría no se recuperan. Cierra sesión y vuelve a entrar para generar
          eventos; luego actualiza el rango o recarga esta página.
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-1">
            Logins por hora
          </h2>
          <p className="text-xs text-muted-foreground mb-4">Hora local America/Lima</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={loginsByHour}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill={CHART_PRIMARY} name="Logins" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-1">
            Logins por día
          </h2>
          <p className="text-xs text-muted-foreground mb-4">Día calendario America/Lima</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={loginsByDay}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} minTickGap={24} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke={CHART_SECONDARY}
                  strokeWidth={2}
                  dot={false}
                  name="Logins"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
            Top usuarios (por logins)
          </h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted-foreground border-b border-slate-200 dark:border-slate-700">
                <th className="py-2 pr-2">Email</th>
                <th className="py-2 pr-2">Logins</th>
                <th className="py-2">Última actividad</th>
              </tr>
            </thead>
            <tbody>
              {topUsers.length === 0 && (
                <tr>
                  <td colSpan={3} className="py-4 text-muted-foreground">
                    Sin datos en el rango seleccionado
                  </td>
                </tr>
              )}
              {topUsers.map((u) => (
                <tr key={u.email} className="border-b border-slate-100 dark:border-slate-700/60">
                  <td className="py-2 pr-2 text-slate-900 dark:text-slate-100">{u.email}</td>
                  <td className="py-2 pr-2">{u.login_count}</td>
                  <td className="py-2 text-muted-foreground">
                    {u.last_seen ? new Date(u.last_seen).toLocaleString("es-PE") : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
            Top módulos (page views)
          </h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted-foreground border-b border-slate-200 dark:border-slate-700">
                <th className="py-2 pr-2">Módulo</th>
                <th className="py-2">Vistas</th>
              </tr>
            </thead>
            <tbody>
              {topModules.length === 0 && (
                <tr>
                  <td colSpan={2} className="py-4 text-muted-foreground">
                    Sin datos en el rango seleccionado
                  </td>
                </tr>
              )}
              {topModules.map((m) => (
                <tr key={m.module} className="border-b border-slate-100 dark:border-slate-700/60">
                  <td className="py-2 pr-2 text-slate-900 dark:text-slate-100 capitalize">{m.module}</td>
                  <td className="py-2">{m.views}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto">
        <h2 className="text-lg font-semibold text-[#714B67] dark:text-purple-400 mb-1">
          Actividad reciente
        </h2>
        <p className="text-xs text-muted-foreground mb-4">
          Últimos eventos de uso (logins, vistas, altas y cambios de personas)
        </p>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-muted-foreground border-b border-slate-200 dark:border-slate-700">
              <th className="py-2 pr-2">Fecha</th>
              <th className="py-2 pr-2">Usuario</th>
              <th className="py-2 pr-2">Evento</th>
              <th className="py-2">Detalle</th>
            </tr>
          </thead>
          <tbody>
            {recentEvents.length === 0 && (
              <tr>
                <td colSpan={4} className="py-4 text-muted-foreground">
                  Sin eventos en el rango seleccionado
                </td>
              </tr>
            )}
            {recentEvents.map((ev, idx) => (
              <tr
                key={`${ev.created_at}-${ev.event_name}-${idx}`}
                className="border-b border-slate-100 dark:border-slate-700/60"
              >
                <td className="py-2 pr-2 whitespace-nowrap text-muted-foreground">
                  {formatLima(ev.created_at)}
                </td>
                <td className="py-2 pr-2 text-slate-900 dark:text-slate-100">
                  {ev.user_email || "—"}
                </td>
                <td className="py-2 pr-2">{eventLabel(ev.event_name)}</td>
                <td className="py-2 text-muted-foreground">{eventDetail(ev)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto">
        <h2 className="text-lg font-semibold text-[#714B67] dark:text-purple-400 mb-1">
          Auditoría de personas
        </h2>
        <p className="text-xs text-muted-foreground mb-4">
          Quién dio de alta, cambió rol o activó/desactivó usuarios
        </p>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-muted-foreground border-b border-slate-200 dark:border-slate-700">
              <th className="py-2 pr-2">Fecha</th>
              <th className="py-2 pr-2">Quién</th>
              <th className="py-2 pr-2">Acción</th>
              <th className="py-2 pr-2">Persona</th>
              <th className="py-2">Detalle</th>
            </tr>
          </thead>
          <tbody>
            {adminActions.length === 0 && (
              <tr>
                <td colSpan={5} className="py-4 text-muted-foreground">
                  Sin altas, ediciones ni desactivaciones en el rango
                </td>
              </tr>
            )}
            {adminActions.map((action, idx) => (
              <tr
                key={`${action.created_at}-${action.target_email}-${idx}`}
                className="border-b border-slate-100 dark:border-slate-700/60"
              >
                <td className="py-2 pr-2 whitespace-nowrap text-muted-foreground">
                  {formatLima(action.created_at)}
                </td>
                <td className="py-2 pr-2 text-slate-900 dark:text-slate-100">
                  {action.actor_email || "—"}
                </td>
                <td className="py-2 pr-2">{eventLabel(action.event_name)}</td>
                <td className="py-2 pr-2">{action.target_email || "—"}</td>
                <td className="py-2 text-muted-foreground">{adminActionDetail(action)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function KpiCard({
  title,
  value,
  icon,
}: {
  title: string
  value: number | string
  icon: ReactNode
}) {
  return (
    <div className="bg-gradient-to-br from-[#714B67] to-[#875A7B] p-5 rounded-lg shadow-lg text-white">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-purple-100">{title}</p>
        <div className="bg-white/20 p-2 rounded-lg">{icon}</div>
      </div>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  )
}
