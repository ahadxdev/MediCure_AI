// MediProcure AI Core Types & Domain Models

export type ShortageStatus = 'critical' | 'high' | 'moderate' | 'low' | 'unknown'

export interface InventoryItem {
  medicine_id: string
  name: string
  generic_name: string | null
  strength: string
  dosage_form: string
  pack_size: string
  usable_stock: number
  reorder_level: number
  avg_daily_demand: number
  coverage_days: number | null
  status: ShortageStatus
  last_counted_at: string | null
}

export interface Supplier {
  id: string
  name: string
  email: string
  phone: string
  address: string
  is_verified: boolean
  default_lead_time_days: number
}

export interface QuotationRequest {
  id: string
  medicine_id: string
  medicine_name: string
  required_quantity: number
  required_by_date: string
  delivery_location: string
  status: 'draft' | 'awaiting_approval' | 'approved' | 'sent' | 'reply_received' | 'cancelled'
  created_at: string
  approved_by?: string
  thread_id?: string
  email_subject?: string
  email_body?: string
}

export interface Quotation {
  id: string
  request_id?: string
  supplier_id: string
  supplier_name: string
  medicine_id: string
  medicine_name: string
  price: number
  currency: string
  price_unit: string
  quoted_quantity: number
  minimum_order_quantity: number
  delivery_days: number
  delivery_fee: number
  payment_terms: string
  valid_until: string
  review_status: 'pending' | 'validated' | 'incomplete' | 'conflicting' | 'expired' | 'rejected'
  warning_flags: string[]
  created_at: string
}

export interface ScenarioOption {
  scenario_type: 'cheapest' | 'fastest' | 'split_order' | 'infeasible'
  title: string
  supplier_name: string
  allocated_quantity: number
  unit_price: number
  delivery_fee: number
  total_cost: number
  delivery_days: number
  residual_shortage_days: number
  explanation: string
  feasibility_status: 'feasible' | 'warning' | 'infeasible'
}

export interface PurchaseOrder {
  id: string
  po_number: string
  supplier_name: string
  medicine_name: string
  pack_size: string
  quantity: number
  unit_price: number
  delivery_fee: number
  total_amount: number
  status: 'draft' | 'awaiting_approval' | 'approved' | 'dispatched' | 'cancelled'
  created_at: string
  approved_by?: string
  approved_at?: string
  delivery_estimate_days: number
  budget_impact_note?: string
}

export interface AuditEvent {
  id: string
  entity_type: string
  entity_id: string
  event_type: string
  actor: string
  timestamp: string
  description: string
  payload?: Record<string, any>
}
