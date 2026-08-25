import axios from 'axios'
import { assertLettersModuleEnabled } from '@/lib/feature-flags'

const DEFAULT_FLASK_API_URL = 'http://localhost:5000'

/** Normaliza NEXT_PUBLIC_FLASK_API_URL para redirects y baseURL absolutos. */
export function normalizeFlaskApiUrl(url?: string | null): string {
  const trimmed = (url ?? '').trim()
  if (!trimmed) {
    return DEFAULT_FLASK_API_URL
  }
  const withProtocol = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`
  return withProtocol.replace(/\/+$/, '')
}

export const FLASK_API_URL = normalizeFlaskApiUrl(process.env.NEXT_PUBLIC_FLASK_API_URL)

const API_BASE_URL = FLASK_API_URL

export const flaskApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 120000, // 2 minutos para procesos largos como envío masivo de correos
})

// Redirigir a login ante 401 (sesión expirada o no autenticado), salvo si la petición era al login
// o si ya estamos en /login (evita bucle: la propia página de login llama getUserInfo y recibe 401)
flaskApi.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const url = error.config?.url ?? ''
    const alreadyOnLogin = typeof window !== 'undefined' && window.location.pathname.startsWith('/login')
    if (status === 401 && typeof url === 'string' && !url.includes('auth/login') && !alreadyOnLogin) {
      window.location.replace('/login')
    }
    return Promise.reject(error)
  }
)

// Tipos de respuesta
export interface ApiResponse<T> {
  success: boolean
  data: T
  count?: number
  shown_count?: number
  message?: string
  summary?: {
    overall: {
      debit: number
      credit: number
      saldo: number
      saldo_total?: number
      amount_total?: number
      count: number
      overdue_amount?: number
      overdue_count?: number
      pending_cutoff?: number
      paid_after_cutoff?: number
    }
    by_account: Array<{
      account_code: string
      account_name: string
      debit: number
      credit: number
      saldo: number
      saldo_total?: number
      amount_total?: number
      count: number
      overdue_amount?: number
      overdue_count?: number
      pending_cutoff?: number
      paid_after_cutoff?: number
    }>
  }
}

// Tipos para reportes
export interface ReportParams {
  date_from?: string
  date_to?: string
  date_cutoff?: string
  date_cutoff_start?: string
  customer?: string
  sub_channel?: string
  payment_method?: string
  supplier?: string
  account_codes?: string
  sales_channel_id?: number
  doc_type_id?: number
  doc_number?: string
  payment_state?: string
  include_reconciled?: boolean
  summary_only?: boolean
  limit?: number
}

export interface CollectionLine {
  payment_state: string
  invoice_date: string
  date: string // Fecha contabilización
  l10n_latam_document_type_id: string
  move_name: string
  l10n_latam_boe_number?: string // Letra
  invoice_origin: string
  'account_id/code': string
  'account_id/name': string
  partner_vat?: string
  partner_name?: string
  partner_id?: string
  currency_id: string
  amount_total?: number // Total en soles
  amount_currency?: number // Total en moneda origen
  amount_residual_with_retention?: number // Saldo en soles
  amount_residual_signed?: number // Saldo firmado (Odoo)
  amount_residual_historical?: number // Pendiente al corte
  paid_after_cutoff?: number // Pagado después corte
  date_maturity: string
  dias_vencido: number
  estado_deuda: string
  antiguedad: string
  ref: string // Referencia
  invoice_payment_term_id?: string // Condición Pago
  narration?: string // Descripción
  invoice_user_name?: string // Vendedor
  partner_state?: string // Provincia
  partner_district?: string // Distrito
  partner_country_code?: string // Código País
  partner_country_name?: string // País
  partner_groups?: string // Grupos
  sub_channel_id?: string // Sub Canal
  sales_channel_name?: string // Canal de Venta
  sales_type_name?: string // Tipo de Venta
}

export interface TreasuryLine {
  move_name: string
  ref: string
  payment_state: string
  invoice_date: string
  invoice_date_due: string
  supplier_name: string
  supplier_vat: string
  currency_id: string
  amount_total: number
  amount_residual: number
  dias_vencido: number
  estado_deuda: string
  antiguedad: string
}

export interface Letter {
  id: number
  number: string
  acceptor_id: string
  vat: string
  amount: number
  currency: string
  due_date: string
  date: string // Fecha Emision Letra
  invoice_date?: string // Fecha Factura
  status_calc: string
  customer_email: string
  customer_name: string
  salesperson: string
  city: string
  ref_docs: string // Factura(s)
  invoice_origin: string
  state: string
}

export interface FilterOptions {
  sales_channels: Array<{ id: number; name: string }>
  document_types: Array<{ id: number; name: string }>
  sub_channels: Array<{ value: string; name: string }>
  payment_methods: Array<{ id: number; name: string }>
}

export interface EmailResult {
  sent: number
  failed: number
  errors: string[]
}

export interface AuthUserInfoResponse {
  success: boolean
  username?: string
  email?: string
  roles?: string[]
  message?: string
}

export interface AnalyticsSummary {
  kpis: {
    unique_users: number
    total_logins: number
    failed_logins?: number
    logouts?: number
    total_page_views: number
    active_days: number
  }
  logins_by_hour: Array<{ hour: number; count: number }>
  logins_by_day: Array<{ date: string; count: number }>
  top_users: Array<{ email: string; login_count: number; last_seen?: string }>
  top_modules: Array<{ module: string; views: number }>
  recent_events?: AnalyticsEvent[]
  user_admin_actions?: UserAdminAction[]
  range?: { from: string; to: string; timezone?: string }
}

export interface AnalyticsEvent {
  created_at?: string
  user_email?: string
  username?: string
  event_category?: string
  event_name?: string
  payload?: Record<string, unknown>
  path?: string
}

export interface UserAdminAction {
  created_at?: string
  actor_email?: string
  event_name?: string
  target_email?: string
  payload?: Record<string, unknown>
}

// Endpoints de Collections
export const collectionsApi = {
  getReport: (params: ReportParams) => 
    flaskApi.get<ApiResponse<CollectionLine[]>>('/api/v1/collections/report/account12', { params }),
  
  getFilterOptions: (params?: Partial<ReportParams>) =>
    flaskApi.get<ApiResponse<FilterOptions>>('/api/v1/collections/filter-options', { params }),
}

// Endpoints de Treasury
export const treasuryApi = {
  getReport: (params: ReportParams) =>
    flaskApi.get<ApiResponse<TreasuryLine[]>>('/api/v1/treasury/report/account42', { params }),
}

// Endpoints de Letters (bloqueados en cliente si el feature flag está apagado)
export const lettersApi = {
  getToAccept: () => {
    assertLettersModuleEnabled()
    return flaskApi.get<ApiResponse<Letter[]>>('/api/v1/letters/to-accept')
  },

  sendAcceptanceEmails: (letter_ids: number[]) => {
    assertLettersModuleEnabled()
    return flaskApi.post<ApiResponse<EmailResult>>('/api/v1/letters/send-acceptance', { letter_ids })
  },
}

// Endpoints de Auth (login exclusivo con Google OAuth2, manejado por navegación del navegador)
export const authApi = {
  getUserInfo: () =>
    flaskApi.get<AuthUserInfoResponse>('/api/v1/auth/user-info'),

  logout: () =>
    flaskApi.post('/api/v1/auth/logout'),
}

// Endpoints de Analytics / Observabilidad
export const analyticsApi = {
  getSummary: (params?: { from?: string; to?: string }) =>
    flaskApi.get<{ success: boolean; data: AnalyticsSummary; message?: string }>(
      '/api/v1/analytics/summary',
      { params }
    ),
}

export interface AppUser {
  email: string
  display_name?: string | null
  role: string
  is_active: boolean
  is_protected?: boolean
  created_by?: string | null
  created_at?: string
  updated_at?: string
}

export interface AppPlatform {
  id: string
  name: string
  slug: string
  base_url?: string | null
  kind: string
  is_active: boolean
  sort_order?: number
  notes?: string | null
  health_status?: string
  health_checked_at?: string
  created_at?: string
  updated_at?: string
}

export interface AppsDashboard {
  kpis: {
    users_total: number
    users_active: number
    users_inactive: number
    users_by_role: {
      admin: number
      app_assistant: number
      user: number
    }
    platforms_total: number
    platforms_active: number
    platforms_ok: number
    platforms_degraded: number
    platforms_down: number
    platforms_unknown: number
  }
  charts: {
    roles_distribution: Array<{ role: string; count: number }>
    users_active_inactive: Array<{ status: string; count: number }>
    platforms_health: Array<{ name: string; status: string; value: number }>
    users_created_by_day: Array<{ date: string; count: number }>
  }
  platforms: AppPlatform[]
  users: AppUser[]
}

// Centro de aplicaciones (admin + app_assistant)
export const appsApi = {
  getDashboard: () =>
    flaskApi.get<{ success: boolean; data: AppsDashboard; message?: string }>(
      '/api/v1/apps/dashboard'
    ),

  listPlatforms: () =>
    flaskApi.get<{ success: boolean; data: AppPlatform[] }>('/api/v1/apps/platforms'),

  createPlatform: (body: {
    name: string
    slug: string
    base_url?: string
    kind?: string
    notes?: string
    is_active?: boolean
    sort_order?: number
  }) => flaskApi.post<{ success: boolean; data: AppPlatform }>('/api/v1/apps/platforms', body),

  updatePlatform: (id: string, body: Partial<AppPlatform>) =>
    flaskApi.patch<{ success: boolean; data: AppPlatform }>(`/api/v1/apps/platforms/${id}`, body),

  listUsers: () =>
    flaskApi.get<{ success: boolean; data: AppUser[] }>('/api/v1/apps/users'),

  createUser: (body: {
    email: string
    display_name?: string
    role?: string
    is_active?: boolean
  }) => flaskApi.post<{ success: boolean; data: AppUser }>('/api/v1/apps/users', body),

  updateUser: (email: string, body: Partial<AppUser>) =>
    flaskApi.patch<{ success: boolean; data: AppUser }>(
      `/api/v1/apps/users/${encodeURIComponent(email)}`,
      body
    ),
}

// Health check
export const healthApi = {
  check: () => flaskApi.get('/api/health'),
}
