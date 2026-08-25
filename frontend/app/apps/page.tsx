"use client"

import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import {
  AppWindow,
  CheckCircle2,
  LayoutGrid,
  Plus,
  Server,
  Users,
  XCircle,
} from "lucide-react"
import { authApi, appsApi, type AppPlatform, type AppUser } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ErrorFallback } from "@/components/error-fallback"

const CHART_PRIMARY = "#714B67"
const CHART_SECONDARY = "#875A7B"
const ROLE_COLORS: Record<string, string> = {
  admin: "#714B67",
  app_assistant: "#875A7B",
  user: "#A78B9B",
}

const ROLE_LABELS: Record<string, string> = {
  admin: "Admin",
  app_assistant: "Asistente",
  user: "Usuario",
}

function healthBadge(status?: string) {
  const s = (status || "unknown").toLowerCase()
  if (s === "ok") {
    return (
      <span className="inline-flex items-center gap-1 text-emerald-700 dark:text-emerald-400 text-xs font-medium">
        <CheckCircle2 className="h-3.5 w-3.5" /> Online
      </span>
    )
  }
  if (s === "down") {
    return (
      <span className="inline-flex items-center gap-1 text-red-700 dark:text-red-400 text-xs font-medium">
        <XCircle className="h-3.5 w-3.5" /> Offline
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 text-amber-700 dark:text-amber-400 text-xs font-medium">
      Desconocido
    </span>
  )
}

export default function AppsPage() {
  const router = useRouter()
  const queryClient = useQueryClient()

  const { data: authData, isLoading: authLoading } = useQuery({
    queryKey: ["auth", "user-info"],
    queryFn: async () => {
      const res = await authApi.getUserInfo()
      return res.data
    },
    staleTime: 60_000,
  })

  const roles = authData?.roles || []
  const isAdmin = roles.includes("admin")
  const isAppsOperator = isAdmin || roles.includes("app_assistant")

  useEffect(() => {
    if (!authLoading && authData?.success && !isAppsOperator) {
      router.replace("/collections")
    }
  }, [authLoading, authData, isAppsOperator, router])

  const {
    data: dashboard,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["apps", "dashboard"],
    queryFn: async () => {
      const res = await appsApi.getDashboard()
      return res.data.data
    },
    enabled: isAppsOperator,
    retry: 1,
  })

  const [userForm, setUserForm] = useState({
    email: "",
    display_name: "",
    role: "user",
    is_active: true,
  })
  const [editingEmail, setEditingEmail] = useState<string | null>(null)
  const [editDraft, setEditDraft] = useState<{ display_name: string; role: string }>({
    display_name: "",
    role: "user",
  })
  const [platformForm, setPlatformForm] = useState({
    name: "",
    slug: "",
    base_url: "",
    kind: "other",
    notes: "",
  })
  const [formError, setFormError] = useState<string | null>(null)
  const [formSuccess, setFormSuccess] = useState<string | null>(null)
  const [rowFeedback, setRowFeedback] = useState<{
    email: string
    type: "error" | "success"
    message: string
  } | null>(null)

  const apiErrorMessage = (err: unknown, fallback: string) =>
    (err as { response?: { data?: { message?: string } } })?.response?.data?.message ||
    fallback

  const startEdit = (u: AppUser) => {
    setFormError(null)
    setFormSuccess(null)
    setRowFeedback(null)
    setEditingEmail(u.email)
    setEditDraft({
      display_name: u.display_name || "",
      role: u.role || "user",
    })
  }

  const cancelEdit = () => {
    setEditingEmail(null)
    setRowFeedback(null)
  }

  const createUserMut = useMutation({
    mutationFn: async () => {
      const res = await appsApi.createUser({
        email: userForm.email,
        display_name: userForm.display_name || undefined,
        role: isAdmin ? userForm.role : "user",
        is_active: userForm.is_active,
      })
      return res.data
    },
    onSuccess: () => {
      setFormError(null)
      setFormSuccess("Usuario creado correctamente")
      setRowFeedback(null)
      setUserForm({ email: "", display_name: "", role: "user", is_active: true })
      void queryClient.invalidateQueries({ queryKey: ["apps", "dashboard"] })
    },
    onError: (err: unknown) => {
      setFormSuccess(null)
      setFormError(apiErrorMessage(err, "No se pudo crear el usuario"))
    },
  })

  const updateUserMut = useMutation({
    mutationFn: async (payload: { email: string; patch: Partial<AppUser>; action: string }) => {
      const res = await appsApi.updateUser(payload.email, payload.patch)
      return { data: res.data, email: payload.email, action: payload.action }
    },
    onSuccess: (result) => {
      setEditingEmail(null)
      setFormError(null)
      setFormSuccess(null)
      setRowFeedback({
        email: result.email,
        type: "success",
        message:
          result.action === "toggle"
            ? "Estado actualizado correctamente"
            : "Usuario actualizado correctamente",
      })
      void queryClient.invalidateQueries({ queryKey: ["apps", "dashboard"] })
    },
    onError: (err: unknown, variables) => {
      setFormSuccess(null)
      const msg = apiErrorMessage(err, "No se pudo actualizar el usuario")
      setFormError(msg)
      setRowFeedback({ email: variables.email, type: "error", message: msg })
    },
  })

  const createPlatformMut = useMutation({
    mutationFn: async () => {
      const res = await appsApi.createPlatform({
        name: platformForm.name,
        slug: platformForm.slug || platformForm.name.toLowerCase().replace(/\s+/g, "-"),
        base_url: platformForm.base_url || undefined,
        kind: platformForm.kind,
        notes: platformForm.notes || undefined,
      })
      return res.data
    },
    onSuccess: () => {
      setPlatformForm({ name: "", slug: "", base_url: "", kind: "other", notes: "" })
      void queryClient.invalidateQueries({ queryKey: ["apps", "dashboard"] })
    },
  })

  const rolesChart = useMemo(
    () =>
      (dashboard?.charts.roles_distribution || []).map((r) => ({
        ...r,
        label: ROLE_LABELS[r.role] || r.role,
      })),
    [dashboard]
  )

  if (authLoading || (!isAppsOperator && authData?.success)) {
    return (
      <div className="flex items-center justify-center min-h-[40vh] text-muted-foreground">
        Validando permisos...
      </div>
    )
  }

  if (!isAppsOperator) {
    return null
  }

  if (error) {
    return (
      <ErrorFallback
        error={error instanceof Error ? error : null}
        title="Error al cargar Aplicaciones"
        message="No se pudo obtener el inventario. Verifica que existan las tablas app_users y app_platforms en Supabase."
      />
    )
  }

  const kpis = dashboard?.kpis
  const platforms = dashboard?.platforms || []
  const users = dashboard?.users || []

  const onSubmitUser = (e: FormEvent) => {
    e.preventDefault()
    setFormError(null)
    setFormSuccess(null)
    setRowFeedback(null)
    createUserMut.mutate()
  }

  const onSubmitPlatform = (e: FormEvent) => {
    e.preventDefault()
    createPlatformMut.mutate()
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[#714B67] dark:text-purple-400">
            Aplicaciones
          </h1>
          <p className="text-muted-foreground dark:text-slate-400 mt-2">
            Inventario de plataformas, salud operativa y gestión de usuarios
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => void refetch()}
          className="border-[#714B67]/40 text-[#714B67]"
        >
          Actualizar
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Usuarios activos"
          value={kpis?.users_active ?? (isLoading ? "…" : 0)}
          icon={<Users className="h-5 w-5" />}
        />
        <KpiCard
          title="Usuarios inactivos"
          value={kpis?.users_inactive ?? (isLoading ? "…" : 0)}
          icon={<Users className="h-5 w-5 opacity-60" />}
        />
        <KpiCard
          title="Plataformas online"
          value={kpis?.platforms_ok ?? (isLoading ? "…" : 0)}
          icon={<Server className="h-5 w-5" />}
        />
        <KpiCard
          title="Plataformas offline"
          value={kpis?.platforms_down ?? (isLoading ? "…" : 0)}
          icon={<AppWindow className="h-5 w-5" />}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
            Distribución por rol
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={rolesChart}
                  dataKey="count"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={2}
                >
                  {rolesChart.map((entry) => (
                    <Cell key={entry.role} fill={ROLE_COLORS[entry.role] || CHART_PRIMARY} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
            Activos vs inactivos
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dashboard?.charts.users_active_inactive || []}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                <XAxis dataKey="status" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill={CHART_SECONDARY} radius={[4, 4, 0, 0]} name="Usuarios" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
            Estado de plataformas
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={(dashboard?.charts.platforms_health || []).map((p) => ({
                  ...p,
                  score: p.status === "ok" ? 1 : p.status === "down" ? 0 : 0.5,
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="score" fill={CHART_PRIMARY} name="Salud" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
            Altas de usuarios (por día)
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dashboard?.charts.users_created_by_day || []}>
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
                  name="Altas"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Catálogo de plataformas */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <LayoutGrid className="h-5 w-5 text-[#714B67]" />
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            Catálogo de plataformas
          </h2>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {platforms.map((p: AppPlatform) => (
            <a
              key={p.id}
              href={p.base_url || undefined}
              target={p.base_url ? "_blank" : undefined}
              rel={p.base_url ? "noreferrer" : undefined}
              className="block bg-white dark:bg-slate-800 p-5 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-[#875A7B]/60 transition-colors"
              onClick={(e) => {
                if (!p.base_url) e.preventDefault()
              }}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-semibold text-[#714B67] dark:text-purple-300">{p.name}</h3>
                  <p className="text-xs text-muted-foreground mt-1 uppercase tracking-wide">{p.kind}</p>
                </div>
                {healthBadge(p.health_status)}
              </div>
              {p.notes && (
                <p className="text-sm text-slate-600 dark:text-slate-300 mt-3 line-clamp-2">{p.notes}</p>
              )}
              {p.base_url && (
                <p className="text-xs text-[#875A7B] mt-3 truncate">{p.base_url}</p>
              )}
            </a>
          ))}
        </div>

        <form
          onSubmit={onSubmitPlatform}
          className="bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 grid gap-3 md:grid-cols-2 lg:grid-cols-5 items-end"
        >
          <Field label="Nombre">
            <Input
              value={platformForm.name}
              onChange={(e) => setPlatformForm((f) => ({ ...f, name: e.target.value }))}
              required
            />
          </Field>
          <Field label="Slug">
            <Input
              value={platformForm.slug}
              onChange={(e) => setPlatformForm((f) => ({ ...f, slug: e.target.value }))}
              placeholder="mi-app"
            />
          </Field>
          <Field label="URL">
            <Input
              value={platformForm.base_url}
              onChange={(e) => setPlatformForm((f) => ({ ...f, base_url: e.target.value }))}
              placeholder="https://..."
            />
          </Field>
          <Field label="Tipo">
            <select
              className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={platformForm.kind}
              onChange={(e) => setPlatformForm((f) => ({ ...f, kind: e.target.value }))}
            >
              <option value="other">Otra</option>
              <option value="odoo">Odoo</option>
              <option value="finanzas_agv">Finanzas AGV</option>
            </select>
          </Field>
          <Button
            type="submit"
            className="bg-[#714B67] hover:bg-[#875A7B]"
            disabled={createPlatformMut.isPending}
          >
            <Plus className="h-4 w-4 mr-1" />
            Registrar
          </Button>
        </form>
      </section>

      {/* Gestión de usuarios */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-[#714B67]" />
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            Gestión de personas
          </h2>
        </div>

        {formError && (
          <p
            role="alert"
            className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-md px-3 py-2"
          >
            {formError}
          </p>
        )}
        {formSuccess && (
          <p
            role="status"
            className="text-sm text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 rounded-md px-3 py-2"
          >
            {formSuccess}
          </p>
        )}

        <form
          onSubmit={onSubmitUser}
          className="bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 grid gap-3 md:grid-cols-2 lg:grid-cols-5 items-end"
        >
          <Field label="Email">
            <Input
              type="email"
              value={userForm.email}
              onChange={(e) => setUserForm((f) => ({ ...f, email: e.target.value }))}
              required
              placeholder="nombre@agrovetmarket.com"
            />
          </Field>
          <Field label="Nombre">
            <Input
              value={userForm.display_name}
              onChange={(e) => setUserForm((f) => ({ ...f, display_name: e.target.value }))}
            />
          </Field>
          <Field label="Rol">
            <select
              className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={userForm.role}
              onChange={(e) => setUserForm((f) => ({ ...f, role: e.target.value }))}
              disabled={!isAdmin}
            >
              <option value="user">Usuario</option>
              {isAdmin && <option value="app_assistant">Asistente de aplicaciones</option>}
            </select>
          </Field>
          <Field label="Estado">
            <select
              className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={userForm.is_active ? "1" : "0"}
              onChange={(e) =>
                setUserForm((f) => ({ ...f, is_active: e.target.value === "1" }))
              }
            >
              <option value="1">Activo</option>
              <option value="0">Inactivo</option>
            </select>
          </Field>
          <Button
            type="submit"
            className="bg-[#714B67] hover:bg-[#875A7B]"
            disabled={createUserMut.isPending}
          >
            <Plus className="h-4 w-4 mr-1" />
            Alta
          </Button>
        </form>

        <div className="bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted-foreground border-b border-slate-200 dark:border-slate-700">
                <th className="py-2 pr-2">Email</th>
                <th className="py-2 pr-2">Nombre</th>
                <th className="py-2 pr-2">Rol</th>
                <th className="py-2 pr-2">Estado</th>
                <th className="py-2 pr-2">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u: AppUser) => {
                const editing = editingEmail === u.email
                const isProtected = Boolean(u.is_protected) || u.role === "admin"
                const canEdit =
                  !isProtected &&
                  (isAdmin || (roles.includes("app_assistant") && u.role === "user"))
                const feedback =
                  rowFeedback?.email === u.email ? rowFeedback : null
                const busy =
                  updateUserMut.isPending &&
                  updateUserMut.variables?.email === u.email
                return (
                  <tr
                    key={u.email}
                    className="border-b border-slate-100 dark:border-slate-700/60 last:border-0"
                  >
                    <td className="py-2 pr-2 font-medium align-top">{u.email}</td>
                    <td className="py-2 pr-2 align-top">
                      {editing ? (
                        <Input
                          value={editDraft.display_name}
                          onChange={(e) =>
                            setEditDraft((d) => ({
                              ...d,
                              display_name: e.target.value,
                            }))
                          }
                          className="h-8"
                          disabled={busy}
                        />
                      ) : (
                        u.display_name || "—"
                      )}
                    </td>
                    <td className="py-2 pr-2 align-top">
                      {editing && isAdmin ? (
                        <select
                          value={editDraft.role}
                          onChange={(e) =>
                            setEditDraft((d) => ({ ...d, role: e.target.value }))
                          }
                          className="h-8 rounded-md border border-input bg-background px-2 text-sm"
                          disabled={busy}
                        >
                          <option value="user">Usuario</option>
                          <option value="app_assistant">Asistente</option>
                        </select>
                      ) : (
                        ROLE_LABELS[u.role] || u.role
                      )}
                    </td>
                    <td className="py-2 pr-2 align-top">
                      {u.is_active ? (
                        <span className="text-emerald-700 dark:text-emerald-400">Activo</span>
                      ) : (
                        <span className="text-slate-500">Inactivo</span>
                      )}
                    </td>
                    <td className="py-2 pr-2 align-top">
                      {isProtected ? (
                        <span className="text-xs font-medium text-amber-700 dark:text-amber-400">
                          Protegido
                        </span>
                      ) : !canEdit ? (
                        <span className="text-xs text-muted-foreground">—</span>
                      ) : editing ? (
                        <div className="space-x-2 whitespace-nowrap">
                          <Button
                            size="sm"
                            className="bg-[#714B67] hover:bg-[#875A7B] h-8"
                            disabled={busy}
                            onClick={() =>
                              updateUserMut.mutate({
                                email: u.email,
                                action: "edit",
                                patch: {
                                  display_name: editDraft.display_name,
                                  ...(isAdmin ? { role: editDraft.role } : {}),
                                },
                              })
                            }
                          >
                            {busy ? "Guardando…" : "Guardar"}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8"
                            disabled={busy}
                            onClick={cancelEdit}
                          >
                            Cancelar
                          </Button>
                        </div>
                      ) : (
                        <div className="space-x-2 whitespace-nowrap">
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8"
                            disabled={busy}
                            onClick={() => startEdit(u)}
                          >
                            Editar
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8"
                            disabled={busy}
                            onClick={() =>
                              updateUserMut.mutate({
                                email: u.email,
                                action: "toggle",
                                patch: { is_active: !u.is_active },
                              })
                            }
                          >
                            {busy
                              ? "Actualizando…"
                              : u.is_active
                                ? "Desactivar"
                                : "Activar"}
                          </Button>
                        </div>
                      )}
                      {feedback && (
                        <p
                          role={feedback.type === "error" ? "alert" : "status"}
                          className={`mt-1 text-xs ${
                            feedback.type === "error"
                              ? "text-red-600 dark:text-red-400"
                              : "text-emerald-700 dark:text-emerald-400"
                          }`}
                        >
                          {feedback.message}
                        </p>
                      )}
                    </td>
                  </tr>
                )
              })}
              {!users.length && !isLoading && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-muted-foreground">
                    Sin usuarios registrados en app_users
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function KpiCard({
  title,
  value,
  icon,
}: {
  title: string
  value: string | number
  icon: ReactNode
}) {
  return (
    <div className="bg-white dark:bg-slate-800 p-5 rounded-lg border border-slate-200 dark:border-slate-700">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{title}</p>
        <div className="text-[#714B67] dark:text-purple-400">{icon}</div>
      </div>
      <p className="text-2xl font-bold mt-2 text-slate-900 dark:text-slate-100">{value}</p>
    </div>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="w-full">
      <label className="text-xs font-medium text-slate-600 dark:text-slate-300">{label}</label>
      <div className="mt-1">{children}</div>
    </div>
  )
}
