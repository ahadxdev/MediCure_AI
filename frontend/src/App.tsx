import React, { useState, useEffect } from 'react'
import { Sidebar, Header, NavigationTab } from './components/AppShell'
import { DashboardView } from './views/DashboardView'
import { InventoryView } from './views/InventoryView'
import { QuotesView } from './views/QuotesView'
import { SimulatorView } from './views/SimulatorView'
import { OrdersView } from './views/OrdersView'
import { AuditView } from './views/AuditView'
import { SettingsView } from './views/SettingsView'
import {
  InventoryItem,
  Supplier,
  QuotationRequest,
  Quotation,
  PurchaseOrder,
  AuditEvent,
  ScenarioOption,
} from './types'
import { api } from './services/api'
import { CheckCircle2 } from 'lucide-react'

export function App() {
  const [currentTab, setCurrentTab] = useState<NavigationTab>('dashboard')
  const [isLiveBackend, setIsLiveBackend] = useState<boolean>(false)
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [requests, setRequests] = useState<QuotationRequest[]>([])
  const [quotes, setQuotes] = useState<Quotation[]>([])
  const [orders, setOrders] = useState<PurchaseOrder[]>([])
  const [audit, setAudit] = useState<AuditEvent[]>([])
  const [notification, setNotification] = useState<string | null>(null)

  const showNotification = (msg: string) => {
    setNotification(msg)
    setTimeout(() => setNotification(null), 3500)
  }

  // Load initial dataset
  const loadData = async () => {
    const health = await api.checkHealth()
    setIsLiveBackend(health.isLive)

    const inv = await api.getInventory()
    setInventory(inv.items)

    const sup = await api.getSuppliers()
    setSuppliers(sup.items)

    const req = await api.getQuotationRequests()
    setRequests(req)

    const quo = await api.getQuotations()
    setQuotes(quo)

    const ord = await api.getPurchaseOrders()
    setOrders(ord)

    const aud = await api.getAuditTrail()
    setAudit(aud)
  }

  useEffect(() => {
    loadData()
  }, [])

  // Action Handlers
  const handleApproveAndSendRFQ = async (requestId: string) => {
    await api.approveQuotationRequest(requestId)
    await loadData()
    showNotification(`RFQ #${requestId} approved and dispatched to eligible suppliers via communications gateway.`)
  }

  const handleCreatePurchaseOrder = async (option: ScenarioOption, medicineName: string) => {
    await api.createPurchaseOrder({
      medicine_id: 'med-panadol-500',
      supplier_name: option.supplier_name,
      quantity: option.allocated_quantity,
      unit_price: option.unit_price,
      delivery_fee: option.delivery_fee,
      total_amount: option.total_cost,
      delivery_estimate_days: option.delivery_days,
    })
    await loadData()
    setCurrentTab('purchase_orders')
    showNotification(`Draft Purchase Order created for ${medicineName}! Please review and sign off.`)
  }

  const handleApprovePO = async (orderId: string) => {
    await api.signOffPurchaseOrder(orderId, true, 'Dr. Tariq (Lead Pharmacist)')
    await loadData()
    showNotification(`Purchase Order #${orderId} approved and committed successfully.`)
  }

  const handleRejectPO = async (orderId: string) => {
    await api.signOffPurchaseOrder(orderId, false, 'Dr. Tariq (Lead Pharmacist)')
    await loadData()
    showNotification(`Purchase Order #${orderId} rejected.`)
  }

  // Get Page Header Info
  const getHeaderInfo = () => {
    switch (currentTab) {
      case 'dashboard':
        return {
          title: 'Procurement Overview',
          subtitle: 'High-level operational health, shortage exposure, and pending procurement actions.',
        }
      case 'inventory':
        return {
          title: 'Inventory & Catalog',
          subtitle: 'Real-time usable stock, reorder levels, and average daily consumption rates.',
        }
      case 'shortage_radar':
        return {
          title: 'Shortage Early-Warning Radar',
          subtitle: 'Deterministic stockout predictions and coverage calculations for high-risk medicines.',
        }
      case 'quote_requests':
        return {
          title: 'Quotation Requests (RFQ)',
          subtitle: 'Automated RFQ generation with mandatory human approval before email dispatch.',
        }
      case 'quote_inbox':
        return {
          title: 'Quote Review & Inbox',
          subtitle: 'Structured quotation extraction, lead-time validations, and supplier comparison.',
        }
      case 'suppliers':
        return {
          title: 'Verified Suppliers',
          subtitle: 'Directory of registered pharmaceutical distributors in Pakistan.',
        }
      case 'simulator':
        return {
          title: 'Procurement Decision Simulator',
          subtitle: 'Deterministic multi-criteria optimization comparing lead times, landed costs, and MOQs.',
        }
      case 'purchase_orders':
        return {
          title: 'Purchase Orders & Approvals',
          subtitle: 'Formal purchasing commitments requiring explicit pharmacist authorization.',
        }
      case 'ai_activity':
      case 'audit_trail':
        return {
          title: 'Operational Audit & Decision History',
          subtitle: 'Immutable record of shortage assessments, AI extractions, and human sign-offs.',
        }
      case 'settings':
        return {
          title: 'Dispensary Settings',
          subtitle: 'Pharmacy location, safety thresholds, and integration connectivity.',
        }
      default:
        return { title: 'MediProcure AI', subtitle: 'Predict. Protect. Procure.' }
    }
  }

  const header = getHeaderInfo()

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        isLiveBackend={isLiveBackend}
      />

      {/* Main Content Area */}
      <main className="main-content">
        <Header
          title={header.title}
          subtitle={header.subtitle}
          actions={
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{
                fontSize: '11px',
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: isLiveBackend ? 'var(--color-soft-green)' : 'var(--color-warning-bg)',
                color: isLiveBackend ? 'var(--color-dark-green)' : 'var(--color-warning-amber)',
                fontWeight: 600,
              }}>
                {isLiveBackend ? 'Backend Connected' : 'Simulated Mode'}
              </span>
            </div>
          }
        />

        {/* Floating Toast Notification */}
        {notification && (
          <div style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            backgroundColor: 'var(--color-dark-green)',
            color: '#FFFFFF',
            padding: '12px 20px',
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-elevated)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            zIndex: 1000,
            fontSize: '13px',
            fontWeight: 600,
          }}>
            <CheckCircle2 size={18} />
            {notification}
          </div>
        )}

        {/* Tab Views */}
        <div className="page-body">
          {currentTab === 'dashboard' && (
            <DashboardView
              inventory={inventory}
              quotes={quotes}
              orders={orders}
              onNavigate={setCurrentTab}
            />
          )}

          {currentTab === 'inventory' && (
            <InventoryView
              items={inventory}
              onRefresh={loadData}
              onDraftRFQ={() => setCurrentTab('quote_requests')}
              isRadarOnly={false}
            />
          )}

          {currentTab === 'shortage_radar' && (
            <InventoryView
              items={inventory}
              onRefresh={loadData}
              onDraftRFQ={() => setCurrentTab('simulator')}
              isRadarOnly={true}
            />
          )}

          {(currentTab === 'quote_requests' || currentTab === 'quote_inbox' || currentTab === 'suppliers') && (
            <QuotesView
              requests={requests}
              quotes={quotes}
              suppliers={suppliers}
              onApproveAndSend={handleApproveAndSendRFQ}
              onSimulate={(med, q) => {
                setCurrentTab('simulator')
              }}
            />
          )}

          {currentTab === 'simulator' && (
            <SimulatorView
              quotes={quotes}
              onCreatePurchaseOrder={handleCreatePurchaseOrder}
            />
          )}

          {currentTab === 'purchase_orders' && (
            <OrdersView
              orders={orders}
              onApprovePO={handleApprovePO}
              onRejectPO={handleRejectPO}
            />
          )}

          {(currentTab === 'ai_activity' || currentTab === 'audit_trail') && (
            <AuditView events={audit} />
          )}

          {currentTab === 'settings' && (
            <SettingsView isLiveBackend={isLiveBackend} />
          )}
        </div>
      </main>
    </div>
  )
}

export default App
