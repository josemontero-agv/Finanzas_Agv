import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_FLASK_API_URL || 'http://localhost:5000'

export const flaskApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 120000, // 2 minutos para procesos largos como envío masivo de correos
})

// Tipos de respuesta
export interface ApiResponse<T> {
  success: boolean
  data: T
  count?: number
  message?: string
  summary?: {
    overall: {
      debit: number
      credit: number
      saldo: number
      saldo_total?: number
      count: number
      overdue_amount?: number
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
      count: number
      overdue_amount?: number
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
  customer?: string
  supplier?: string
  account_codes?: string
  sales_channel_id?: number
  doc_type_id?: number
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
}

export interface EmailResult {
  sent: number
  failed: number
  errors: string[]
}

export interface AuthLoginResponse {
  success: boolean
  message: string
  token?: string
  user?: string
  email?: string
}

export interface AuthUserInfoResponse {
  success: boolean
  username?: string
  email?: string
  message?: string
}

// Endpoints de Collections
export const collectionsApi = {
  getReport: (params: ReportParams) => 
    flaskApi.get<ApiResponse<CollectionLine[]>>('/api/v1/collections/report/account12', { params }),
  
  getFilterOptions: () =>
    flaskApi.get<ApiResponse<FilterOptions>>('/api/v1/collections/filter-options'),
}

// Endpoints de Treasury
export const treasuryApi = {
  getReport: (params: ReportParams) =>
    flaskApi.get<ApiResponse<TreasuryLine[]>>('/api/v1/treasury/report/account42', { params }),
}

// Endpoints de Letters
export const lettersApi = {
  getToAccept: () =>
    flaskApi.get<ApiResponse<Letter[]>>('/api/v1/letters/to-accept'),
  
  sendAcceptanceEmails: (letter_ids: number[]) =>
    flaskApi.post<ApiResponse<EmailResult>>('/api/v1/letters/send-acceptance', { letter_ids }),
}

// Endpoints de Auth
export const authApi = {
  login: (username: string, password: string, email?: string) =>
    flaskApi.post<AuthLoginResponse>('/api/v1/auth/login', { username, password, email }),

  getUserInfo: () =>
    flaskApi.get<AuthUserInfoResponse>('/api/v1/auth/user-info'),

  logout: () =>
    flaskApi.post('/api/v1/auth/logout'),
}

// Health check
export const healthApi = {
  check: () => flaskApi.get('/api/health'),
}
