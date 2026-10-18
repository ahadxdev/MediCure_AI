// MediProcure AI Core Types & Domain Models

export type ShortageStatus = 'critical' | 'high' | 'moderate' | 'low' | 'unknown'

export interface InventoryItem {
  medicine_id: string
  name: string
  generic_name: string | null
  category: string | null
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

export interface RecommendedMedicine {
  medicine_id: string
  name: string
  strength: string
  dosage_form: string
  pack_size: string
  usable_stock: number
  reorder_level: number
  avg_daily_demand: number | null
  coverage_days: number | null
  reasons: string[]
}

export interface CategoryRecommendation {
  category: string
  next_week_demand: number
  recent_weekly_average: number
  change_percent: number | null
  priority: 'order' | 'monitor'
  medicines: RecommendedMedicine[]
}

export interface CategoryRecommendations {
  model: string
  source: string
  latest_observation: string
  note: string
  categories: CategoryRecommendation[]
}

export interface MedicineInput {
  name: string
  generic_name: string | null
  category: string | null
  strength: string
  dosage_form: string
  pack_size: string
  usable_stock: number
  reorder_level: number
}

export interface Supplier {
  id: string
  name: string
  email: string
  phone: string | null
  address: string | null
  is_verified: boolean
  default_lead_time_days: number | null
}

export interface SupplierInput {
  name: string
  email: string
  phone: string | null
  address: string | null
  is_verified: boolean
  default_lead_time_days: number | null
}

export interface QuotationRequest {
  id: string
  medicine_id: string
  medicine_name: string
  required_quantity: number
  required_by_date: string
  delivery_location: string
  status: 'draft' | 'awaiting_approval' | 'approved' | 'sent' | 'simulated' | 'partially_sent' | 'reply_received' | 'cancelled'
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
  price: number | null
  currency: string
  price_unit: string | null
  quoted_quantity: number | null
  minimum_order_quantity: number | null
  delivery_days: number | null
  delivery_fee: number | null
  payment_terms: string | null
  valid_until: string | null
  review_status: 'pending' | 'validated' | 'needs_review' | 'incomplete' | 'conflicting' | 'expired' | 'rejected'
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
  supplier_name: string | null
  medicine_name: string | null
  pack_size: string | null
  quantity: number | null
  unit_price: number | null
  delivery_fee: number | null
  total_amount: number
  status: 'draft' | 'awaiting_approval' | 'approved' | 'dispatched' | 'cancelled'
  created_at: string
  approved_by?: string
  approved_at?: string
  delivery_estimate_days: number | null
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
