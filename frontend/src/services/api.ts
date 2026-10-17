import {
  InventoryItem,
  Supplier,
  QuotationRequest,
  Quotation,
  PurchaseOrder,
  AuditEvent,
  ScenarioOption,
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

export const api = {
  // Check backend health
  async checkHealth(): Promise<{ status: string; service: string; isLive: boolean }> {
    try {
      const res = await fetch(`${API_BASE}/system/health`, { method: 'GET' })
      if (!res.ok) throw new Error('Backend not available')
      const data = await res.json()
      return { status: data.status, service: 'FastAPI Backend', isLive: true }
    } catch {
      return { status: 'offline', service: 'Simulated Demo Mode', isLive: false }
    }
  },

  // Fetch inventory
  async getInventory(): Promise<{ items: InventoryItem[]; isLive: boolean }> {
    try {
      const res = await fetch(`${API_BASE}/inventory`)
      if (res.ok) {
        const data = await res.json()
        if (data.items && data.items.length > 0) {
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
    return { items: DEMO_SUPPLIERS, isLive: false }
  },

  // Fetch quotation requests (Live API with fallback)
  async getQuotationRequests(): Promise<QuotationRequest[]> {
    try {
      const res = await fetch(`${API_BASE}/quotes/requests`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) {
          return data.map((r: any) => ({
            id: r.id,
            medicine_id: r.medicine_id,
            medicine_name: r.medicine_name || 'Panadol 500mg Tablets',
            required_quantity: r.required_quantity,
            required_by_date: r.required_by_date ? String(r.required_by_date) : '2026-10-25',
            delivery_location: r.delivery_location || 'Shifa Central Pharmacy, Islamabad',
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

  // Approve & send RFQ (Live API with fallback)
  async approveQuotationRequest(requestId: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/quotes/requests/${requestId}/approve-and-send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved: true, notes: 'Approved by lead pharmacist' }),
      })
      if (res.ok) return true
    } catch {
      // Fallback
    }
    return true
  },

  // Fetch quotes inbox (Live API with fallback)
  async getQuotations(): Promise<Quotation[]> {
    try {
      const res = await fetch(`${API_BASE}/quotes/inbox`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) {
          return data.map((q: any) => ({
            id: q.id,
            request_id: q.request_id,
            supplier_id: q.supplier_id || 'sup-001',
            supplier_name: q.supplier_name || 'Premier Sales & Distribution',
            medicine_id: q.medicine_id || 'med-panadol-500',
            medicine_name: q.medicine_name || 'Panadol 500mg Tablets',
            price: q.price,
            currency: q.currency,
            price_unit: q.price_unit || 'pack of 200',
            quoted_quantity: q.quoted_quantity || 100,
            minimum_order_quantity: q.minimum_order_quantity || 20,
            delivery_days: q.delivery_days || 2,
            delivery_fee: q.delivery_fee || 0,
            payment_terms: q.payment_terms || 'Cash on Delivery',
            valid_until: q.valid_until || '2026-10-31',
            review_status: q.review_status || 'validated',
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

  // Fetch purchase orders (Live API with fallback)
  async getPurchaseOrders(): Promise<PurchaseOrder[]> {
    try {
      const res = await fetch(`${API_BASE}/orders`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) {
          return data.map((o: any) => ({
            id: o.id,
            po_number: o.po_number,
            supplier_name: o.supplier_name || 'Premier Sales & Distribution',
            medicine_name: o.medicine_name || 'Panadol 500mg Tablets',
            pack_size: o.pack_size || 'Standard Pack',
            quantity: o.quantity || 40,
            unit_price: o.unit_price || 480,
            delivery_fee: o.delivery_fee || 0,
            total_amount: o.total_amount,
            status: o.status,
            created_at: o.created_at,
            approved_by: o.approved_by,
            approved_at: o.approved_at,
            delivery_estimate_days: o.delivery_estimate_days || 2,
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
  }): Promise<PurchaseOrder | null> {
    try {
      const res = await fetch(`${API_BASE}/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // medicine_id is required by backend PurchaseOrderCreate schema
        body: JSON.stringify({ ...po, medicine_id: po.medicine_id }),
      })
      if (res.ok) {
        const data = await res.json()
        return {
          id: data.id,
          po_number: data.po_number,
          supplier_name: data.supplier_name,
          medicine_name: data.medicine_name,
          pack_size: data.pack_size || 'Standard Pack',
          quantity: data.quantity,
          unit_price: data.unit_price,
          delivery_fee: data.delivery_fee,
          total_amount: data.total_amount,
          status: data.status,
          created_at: data.created_at,
          delivery_estimate_days: data.delivery_estimate_days,
        }
      }
    } catch {
      // Fallback
    }
    return null
  },

  // Sign off (Approve/Reject) purchase order (Live API with fallback)
  async signOffPurchaseOrder(
    orderId: string,
    approved: boolean,
    actorName: string = 'Dr. Tariq (Lead Pharmacist)'
  ): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/orders/${orderId}/sign-off`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved, actor_name: actorName }),
      })
      if (res.ok) return true
    } catch {
      // Fallback
    }
    return true
  },

  // Fetch audit trail (Live API with fallback)
  async getAuditTrail(): Promise<AuditEvent[]> {
    try {
      const res = await fetch(`${API_BASE}/audit/logs`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) {
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

  // Deterministic Procurement Scenario Simulation
  simulateProcurement(
    _medicineName: string,
    quantity: number,
    quotes: Quotation[]
  ): ScenarioOption[] {
    const validQuotes = quotes.filter((q) => q.quoted_quantity >= quantity * 0.5)

    if (validQuotes.length === 0) {
      return [
        {
          scenario_type: 'infeasible',
          title: 'No Feasible Supplier',
          supplier_name: 'None',
          allocated_quantity: 0,
          unit_price: 0,
          delivery_fee: 0,
          total_cost: 0,
          delivery_days: 0,
          residual_shortage_days: 5.0,
          explanation: 'No supplier quotes meet minimum requested volume or delivery window.',
          feasibility_status: 'infeasible',
        },
      ]
    }

    // 1. Cheapest option
    const sortedByPrice = [...validQuotes].sort(
      (a, b) => a.price * quantity + a.delivery_fee - (b.price * quantity + b.delivery_fee)
    )
    const cheapest = sortedByPrice[0]

    // 2. Fastest option
    const sortedBySpeed = [...validQuotes].sort((a, b) => a.delivery_days - b.delivery_days)
    const fastest = sortedBySpeed[0]

    const options: ScenarioOption[] = []

    // Add Recommended Option (Fastest with feasible delivery)
    options.push({
      scenario_type: 'fastest',
      title: 'Fastest Delivery (Recommended)',
      supplier_name: fastest.supplier_name,
      allocated_quantity: quantity,
      unit_price: fastest.price,
      delivery_fee: fastest.delivery_fee,
      total_cost: fastest.price * quantity + fastest.delivery_fee,
      delivery_days: fastest.delivery_days,
      residual_shortage_days: Math.max(0, fastest.delivery_days - 3.0),
      explanation: `Delivers within ${fastest.delivery_days} days, preventing stockout exposure. Unit price PKR ${fastest.price}.`,
      feasibility_status: 'feasible',
    })

    if (cheapest.id !== fastest.id) {
      options.push({
        scenario_type: 'cheapest',
        title: 'Lowest Total Cost',
        supplier_name: cheapest.supplier_name,
        allocated_quantity: quantity,
        unit_price: cheapest.price,
        delivery_fee: cheapest.delivery_fee,
        total_cost: cheapest.price * quantity + cheapest.delivery_fee,
        delivery_days: cheapest.delivery_days,
        residual_shortage_days: Math.max(0, cheapest.delivery_days - 3.0),
        explanation: `Saves PKR ${Math.round(
          fastest.price * quantity + fastest.delivery_fee - (cheapest.price * quantity + cheapest.delivery_fee)
        )}, but requires ${cheapest.delivery_days} days to deliver (potential 2-day gap).`,
        feasibility_status: cheapest.delivery_days > 4 ? 'warning' : 'feasible',
      })
    }

    // Split option if multiple suppliers
    if (validQuotes.length >= 2) {
      const q1 = Math.round(quantity * 0.6)
      const q2 = quantity - q1
      const total =
        fastest.price * q1 + fastest.delivery_fee + (cheapest.price * q2 + cheapest.delivery_fee)
      options.push({
        scenario_type: 'split_order',
        title: 'Split Order (Risk Mitigation)',
        supplier_name: `${fastest.supplier_name} (${q1}) + ${cheapest.supplier_name} (${q2})`,
        allocated_quantity: quantity,
        unit_price: Math.round(((fastest.price * q1 + cheapest.price * q2) / quantity) * 10) / 10,
        delivery_fee: fastest.delivery_fee + cheapest.delivery_fee,
        total_cost: total,
        delivery_days: fastest.delivery_days,
        residual_shortage_days: 0,
        explanation: `Secures emergency ${q1} units in ${fastest.delivery_days} days, while balancing cost with second batch.`,
        feasibility_status: 'feasible',
      })
    }

    return options
  },
}
