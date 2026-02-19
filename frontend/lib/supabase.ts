import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Tipos para las tablas
export type FactMove = {
  id: number
  name: string
  invoice_date: string
  amount_total: number
  amount_residual: number
  partner_id: number
  payment_state: string
  move_type: string
  state: string
  currency_id: number
  date: string
  invoice_date_due: string
}

export type FactLetter = {
  id: number
  boe_number: string
  state: string
  date: string
  due_date: string
  amount_total: number
  partner_id: number
  move_type: string
  bill_form_id: number | null
}

export type DimPartner = {
  id: number
  name: string
  vat: string | null
  state_name: string | null
  is_company: boolean
  email: string
  phone: string
}
