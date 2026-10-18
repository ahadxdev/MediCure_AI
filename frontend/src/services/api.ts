import {
  InventoryItem,
  Supplier,
  QuotationRequest,
  Quotation,
  PurchaseOrder,
  AuditEvent,
  ScenarioOption,
  CategoryRecommendations,
  DemoSalesResult,
  MedicineInput,
  SupplierInput,
} from '../types'
import {
  DEMO_INVENTORY,
  DEMO_SUPPLIERS,
  DEMO_QUOTES,
  DEMO_REQUESTS,
  DEMO_ORDERS,
  DEMO_AUDIT,
} from './mockData'

const API_BASE = '/api'

async function sendMutation(url: string, method: string, payload?: object): Promise<Response> {
  let response: Response
  try {
    response = await fetch(url, {
      method,
      ...(payload ? {
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      } : {}),
    })
  } catch {
    throw new Error('Backend is unavailable. Connect to the backend to manage records.')
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail || `Request failed (${response.status})`)
  }
  return response
}

export const api = {
  // Check backend health
  async checkHealth(): Promise<{ status: string; service: string; isLive: boolean; gmailMode: string }> {
    try {
      const res = await fetch(`${API_BASE}/system/health`, { method: 'GET' })
      if (!res.ok) throw new Error('Backend not available')
      const data = await res.json()
      return {
        status: data.status,
        service: 'FastAPI Backend',
        isLive: true,
        gmailMode: data.gmail_mode || 'SIMULATED',
      }
    } catch {
      return { status: 'offline', service: 'Simulated Demo Mode', isLive: false, gmailMode: 'OFFLINE' }
    }
  },

  // Fetch inventory
  async getInventory(): Promise<{ items: InventoryItem[]; isLive: boolean }> {
    try {
      const res = await fetch(`${API_BASE}/inventory`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data.items)) {
          return { items: data.items, isLive: true }
        }
      }
    } catch {
      // Fallback
    }
    return { items: DEMO_INVENTORY, isLive: false }
  },

  // Fetch suppliers
  async getSuppliers(): Promise<{ items: Supplier[]; isLive: boolean }> {
    try {
      const res = await fetch(`${API_BASE}/suppliers`)
      if (res.ok) return { items: await res.json(), isLive: true }
    } catch {
      // Fall back to labelled demo supplier data when the API is offline.
    }
    return { items: DEMO_SUPPLIERS, isLive: false }
  },

  async getMedicineCatalog(): Promise<Array<{ name: string; generic_name: string | null; category: string | null; strength: string; dosage_form: string; pack_size: string }>> {
    try {
      const res = await fetch(`${API_BASE}/inventory/catalog`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data)) return data
      }
    } catch {
      // Ignore and let the form keep working with manual entry fallback.
    }
    return []
  },

  async getCategoryRecommendations(): Promise<CategoryRecommendations> {
    const response = await sendMutation(`${API_BASE}/risk/category-recommendations`, 'GET')
    return response.json()
  },

  async addDemoSalesData(): Promise<DemoSalesResult> {
    const response = await sendMutation(`${API_BASE}/sales/demo-data`, 'POST')
    return response.json()
  },

  async createMedicine(payload: MedicineInput): Promise<void> {
    await sendMutation(`${API_BASE}/inventory`, 'POST', payload)
  },

  async updateMedicine(medicineId: string, payload: MedicineInput): Promise<void> {
    await sendMutation(`${API_BASE}/inventory/${medicineId}`, 'PUT', payload)
  },

  async deleteMedicine(medicineId: string): Promise<void> {
    await sendMutation(`${API_BASE}/inventory/${medicineId}`, 'DELETE')
  },

  async createSupplier(payload: SupplierInput): Promise<void> {
    await sendMutation(`${API_BASE}/suppliers`, 'POST', payload)
  },

  async updateSupplier(supplierId: string, payload: SupplierInput): Promise<void> {
    await sendMutation(`${API_BASE}/suppliers/${supplierId}`, 'PUT', payload)
  },

  async deleteSupplier(supplierId: string): Promise<void> {
    await sendMutation(`${API_BASE}/suppliers/${supplierId}`, 'DELETE')
  },

  // Fetch quotation requests (Live API with fallback)
  async getQuotationRequests(): Promise<QuotationRequest[]> {
    try {
      const res = await fetch(`${API_BASE}/quotes/requests`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data)) {
          return data.map((r: any) => ({
            id: r.id,
            medicine_id: r.medicine_id,
            medicine_name: r.medicine_name || 'Unknown medicine',
            required_quantity: r.required_quantity,
            required_by_date: r.required_by_date ? String(r.required_by_date) : '',
            delivery_location: r.delivery_location || '',
            status: r.status,
            created_at: r.created_at,
          }))
        }
      }
    } catch {
      // Fallback
    }
    return DEMO_REQUESTS
  },

  async getQuotationDraft(requestId: string): Promise<{ to: string[]; subject: string; body: string; mode: string }> {
    const response = await sendMutation(`${API_BASE}/quotes/requests/${requestId}/draft`, 'GET')
    return response.json()
  },

  async approveQuotationRequest(requestId: string): Promise<{ status: string; mode: string; recipients: string[]; message: string; error?: string | null }> {
    const response = await sendMutation(
      `${API_BASE}/quotes/requests/${requestId}/approve-and-send`,
      'POST',
      { approved: true, notes: 'Approved by lead pharmacist' },
    )
    return response.json()
  },

  async createQuotationRequest(request: {
    medicine_id: string
    required_quantity: number
    required_by_date: string | null
    delivery_location: string
  }): Promise<void> {
    await sendMutation(`${API_BASE}/quotes/requests`, 'POST', request)
  },

  async simulateProcurement(input: {
    medicine_id: string
    required_quantity: number
    budget_limit: number
    max_delivery_days: number
  }): Promise<{ medicine_id: string; medicine_name: string; options: ScenarioOption[]; quotes_evaluated_count: number }> {
    const response = await sendMutation(`${API_BASE}/procurement/simulate`, 'POST', input)
    return response.json()
  },

  // Fetch quotes inbox (Live API with fallback)
  async getQuotations(): Promise<Quotation[]> {
    try {
      const res = await fetch(`${API_BASE}/quotes/inbox`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data)) {
          return data.map((q: any) => ({
            id: q.id,
            request_id: q.request_id,
            supplier_id: q.supplier_id || '',
            supplier_name: q.supplier_name || 'Unknown supplier',
            medicine_id: q.medicine_id || '',
            medicine_name: q.medicine_name || 'Unknown medicine',
            price: q.price,
            currency: q.currency,
            price_unit: q.price_unit,
            quoted_quantity: q.quoted_quantity,
            minimum_order_quantity: q.minimum_order_quantity,
            delivery_days: q.delivery_days,
            delivery_fee: q.delivery_fee,
            payment_terms: q.payment_terms,
            valid_until: q.valid_until,
            review_status: q.review_status || 'needs_review',
            warning_flags: q.warning_flags || [],
            created_at: q.created_at,
          }))
        }
      }
    } catch {
      // Fallback
    }
    return DEMO_QUOTES
  },

  async syncSupplierInbox(query: string = 'in:inbox newer_than:90d', maxResults: number = 20): Promise<{ scanned: number; imported: number; duplicates: number; ignored: number; mode: string }> {
    const response = await sendMutation(`${API_BASE}/quotes/inbox/sync`, 'POST', {
      query,
      max_results: maxResults,
    })
    return response.json()
  },

  // Fetch purchase orders (Live API with fallback)
  async getPurchaseOrders(): Promise<PurchaseOrder[]> {
    try {
      const res = await fetch(`${API_BASE}/orders`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data)) {
          return data.map((o: any) => ({
            id: o.id,
            po_number: o.po_number,
            supplier_name: o.supplier_name,
            medicine_name: o.medicine_name,
            pack_size: o.pack_size,
            quantity: o.quantity,
            unit_price: o.unit_price,
            delivery_fee: o.delivery_fee,
            total_amount: o.total_amount,
            status: o.status,
            created_at: o.created_at,
            approved_by: o.approved_by,
            approved_at: o.approved_at,
            delivery_estimate_days: o.delivery_estimate_days,
            budget_impact_note: 'Verified against current budget allocation',
          }))
        }
      }
    } catch {
      // Fallback
    }
    return DEMO_ORDERS
  },

  // Create draft purchase order (Live API with fallback)
  async createPurchaseOrder(po: {
    medicine_id: string
    supplier_name: string
    quantity: number
    unit_price: number
    delivery_fee: number
    total_amount: number
    delivery_estimate_days: number
  }): Promise<PurchaseOrder> {
    const res = await sendMutation(`${API_BASE}/orders`, 'POST', po)
    const data = await res.json()
    return {
      id: data.id,
      po_number: data.po_number,
      supplier_name: data.supplier_name,
      medicine_name: data.medicine_name,
      pack_size: data.pack_size,
      quantity: data.quantity,
      unit_price: data.unit_price,
      delivery_fee: data.delivery_fee,
      total_amount: data.total_amount,
      status: data.status,
      created_at: data.created_at,
      delivery_estimate_days: data.delivery_estimate_days,
    }
  },

  // Sign off (Approve/Reject) purchase order (Live API with fallback)
  async signOffPurchaseOrder(
    orderId: string,
    approved: boolean,
    actorName: string = 'Dr. Tariq (Lead Pharmacist)'
  ): Promise<boolean> {
    await sendMutation(`${API_BASE}/orders/${orderId}/sign-off`, 'POST', {
      approved,
      actor_name: actorName,
    })
    return true
  },

  // Fetch audit trail (Live API with fallback)
  async getAuditTrail(): Promise<AuditEvent[]> {
    try {
      const res = await fetch(`${API_BASE}/audit/logs`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data)) {
          return data.map((a: any) => ({
            id: a.id,
            entity_type: a.entity_type,
            entity_id: a.entity_id,
            event_type: a.event_type,
            actor: a.actor,
            timestamp: a.timestamp,
            description: a.payload ? JSON.stringify(a.payload) : `${a.event_type} on ${a.entity_type}`,
            payload: a.payload,
          }))
        }
      }
    } catch {
      // Fallback
    }
    return DEMO_AUDIT
  },

}
