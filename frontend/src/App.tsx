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
  MedicineInput,
  Supplier,
  SupplierInput,
  QuotationRequest,
  Quotation,
  PurchaseOrder,
  AuditEvent,
  ScenarioOption,
  CategoryRecommendations,
  DemoSalesResult,
} from './types'
import { api } from './services/api'
import { AlertCircle, CheckCircle2 } from 'lucide-react'

export function App() {
  const [currentTab, setCurrentTab] = useState<NavigationTab>('dashboard')
  const [isLiveBackend, setIsLiveBackend] = useState<boolean>(false)
  const [gmailMode, setGmailMode] = useState('SIMULATED')
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [requests, setRequests] = useState<QuotationRequest[]>([])
  const [quotes, setQuotes] = useState<Quotation[]>([])
  const [orders, setOrders] = useState<PurchaseOrder[]>([])
  const [categoryRecommendations, setCategoryRecommendations] = useState<CategoryRecommendations | null>(null)
  const [categoryRecommendationsError, setCategoryRecommendationsError] = useState<string | null>(null)
  const [categoryRecommendationsLoading, setCategoryRecommendationsLoading] = useState(true)
  const [recommendedMedicineId, setRecommendedMedicineId] = useState<string | null>(null)
  const [demoSalesLoading, setDemoSalesLoading] = useState(false)
  const [simulatorMedicineId, setSimulatorMedicineId] = useState('')
  const [audit, setAudit] = useState<AuditEvent[]>([])
  const [notification, setNotification] = useState<string | null>(null)
  const [notificationIsError, setNotificationIsError] = useState(false)

  const showNotification = (msg: string, isError = false) => {
    setNotification(msg)
    setNotificationIsError(isError)
    setTimeout(() => setNotification(null), 3500)
  }

  const handleSaveMedicine = async (medicineId: string | null, payload: MedicineInput) => {
    try {
      if (medicineId) await api.updateMedicine(medicineId, payload)
      else await api.createMedicine(payload)
      await loadData()
      showNotification(medicineId ? 'Medicine updated.' : 'Medicine added.')
      return true
    } catch (error) {
      showNotification(`Could not save medicine: ${error instanceof Error ? error.message : 'Unknown error'}`, true)
      return false
    }
  }

  const handleDeleteMedicine = async (medicineId: string) => {
    try {
      await api.deleteMedicine(medicineId)
      await loadData()
      showNotification('Medicine deleted.')
      return true
    } catch (error) {
      showNotification(`Could not delete medicine: ${error instanceof Error ? error.message : 'Unknown error'}`, true)
      return false
    }
  }

  const handleCreateRFQ = async (request: {
    medicine_id: string
    required_quantity: number
    required_by_date: string | null
    delivery_location: string
  }) => {
    try {
      await api.createQuotationRequest(request)
      await loadData()
      setCurrentTab('quote_requests')
      showNotification('RFQ draft created. Review the recipient list and email before approving.')
      return true
    } catch (error) {
      showNotification(`Could not create RFQ: ${error instanceof Error ? error.message : 'Unknown error'}`, true)
      return false
    }
  }

  const handleAddDemoSales = async (): Promise<DemoSalesResult | null> => {
    setDemoSalesLoading(true)
    try {
      const result = await api.addDemoSalesData()
      await loadData()
      showNotification(
        result.generated_records
          ? `Added ${result.generated_records} clearly labeled synthetic sales records.`
          : 'No new sample sales added; eligible medicines already have demo data or need a supported category.',
      )
      return result
    } catch (error) {
      showNotification(`Could not add demo sales: ${error instanceof Error ? error.message : 'Unknown error'}`, true)
      return null
    } finally {
      setDemoSalesLoading(false)
    }
  }

  const handleSaveSupplier = async (supplierId: string | null, payload: SupplierInput) => {
    try {
      if (supplierId) await api.updateSupplier(supplierId, payload)
      else await api.createSupplier(payload)
      await loadData()
      showNotification(supplierId ? 'Supplier updated.' : 'Supplier added.')
      return true
    } catch (error) {
      showNotification(`Could not save supplier: ${error instanceof Error ? error.message : 'Unknown error'}`, true)
      return false
    }
  }

  const handleDeleteSupplier = async (supplierId: string) => {
    try {
      await api.deleteSupplier(supplierId)
      await loadData()
      showNotification('Supplier deleted.')
      return true
    } catch (error) {
      showNotification(`Could not delete supplier: ${error instanceof Error ? error.message : 'Unknown error'}`, true)
      return false
    }
  }

  const handleSaveSettings = async (payload: { dispensary_name: string; dispensary_city: string; reorder_threshold_days: number }) => {
    try {
      await api.updateSettings(payload)
      showNotification('Settings saved.')
      return true
    } catch (error) {
      showNotification(`Could not save settings: ${error instanceof Error ? error.message : 'Unknown error'}`, true)
      return false
    }
  }

  // Load initial dataset
  const loadData = async () => {
    const health = await api.checkHealth()
    setIsLiveBackend(health.isLive)
    setGmailMode(health.gmailMode)

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

    setCategoryRecommendationsLoading(true)
    try {
      setCategoryRecommendations(await api.getCategoryRecommendations())
      setCategoryRecommendationsError(null)
    } catch (error) {
      setCategoryRecommendationsError(error instanceof Error ? error.message : 'Unknown error')
    } finally {
      setCategoryRecommendationsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Action Handlers
  const handleApproveAndSendRFQ = async (requestId: string) => {
    try {
      const draft = await api.getQuotationDraft(requestId)
      const confirmed = window.confirm(
        `Review and approve this RFQ?\n\nMode: ${draft.mode}\nTo: ${draft.to.join(', ')}\nSubject: ${draft.subject}\n\n${draft.body}`,
      )
      if (!confirmed) return
      const result = await api.approveQuotationRequest(requestId)
      await loadData()
      showNotification(`${result.message} (${result.mode}).${result.error ? ` ${result.error}` : ''}`)
    } catch (error) {
      showNotification(`Could not dispatch RFQ: ${error instanceof Error ? error.message : 'Unknown error'}`, true)
    }
  }

  const handleSyncSupplierInbox = async () => {
    try {
      const result = await api.syncSupplierInbox()
      await loadData()
      showNotification(
        `Gmail ${result.mode}: scanned ${result.scanned}, imported ${result.imported}, duplicates ${result.duplicates}, ignored ${result.ignored}.`
      )
    } catch (error) {
      showNotification(`Could not sync supplier inbox: ${error instanceof Error ? error.message : 'Unknown error'}`, true)
    }
  }

  const handleCreatePurchaseOrder = async (option: ScenarioOption, medicineId: string, medicineName: string) => {
    try {
      if (option.scenario_type === 'split_order' && option.allocations?.length) {
        await api.createBulkPurchaseOrders(option.allocations.map((allocation) => ({
          medicine_id: medicineId,
          supplier_name: allocation.supplier_name,
          quantity: allocation.quantity,
          unit_price: allocation.unit_price,
          delivery_fee: allocation.delivery_fee,
          total_amount: allocation.quantity * allocation.unit_price + allocation.delivery_fee,
          delivery_estimate_days: option.delivery_days,
        })))
        await loadData()
        setCurrentTab('purchase_orders')
        showNotification(`Split draft purchase orders created for ${medicineName}.`)
        return
      }
      await api.createPurchaseOrder({
        medicine_id: medicineId,
        supplier_name: option.supplier_name,
        quantity: option.allocated_quantity,
        unit_price: option.unit_price,
        delivery_fee: option.delivery_fee,
        total_amount: option.total_cost,
        delivery_estimate_days: option.delivery_days,
      })
      await loadData()
      setCurrentTab('purchase_orders')
      showNotification(`Draft Purchase Order created for ${medicineName}. Review and sign off before commitment.`)
    } catch (error) {
      showNotification(`Could not create purchase order: ${error instanceof Error ? error.message : 'Unknown error'}`, true)
    }
  }

  const handleApprovePO = async (orderId: string) => {
    try {
      await api.signOffPurchaseOrder(orderId, true, 'Dr. Tariq (Lead Pharmacist)')
      await loadData()
      showNotification(`Purchase Order #${orderId} approved and committed successfully.`)
    } catch (error) {
      showNotification(`Could not approve purchase order: ${error instanceof Error ? error.message : 'Unknown error'}`, true)
    }
  }

  const handleRejectPO = async (orderId: string) => {
    try {
      await api.signOffPurchaseOrder(orderId, false, 'Dr. Tariq (Lead Pharmacist)')
      await loadData()
      showNotification(`Purchase Order #${orderId} rejected.`)
    } catch (error) {
      showNotification(`Could not reject purchase order: ${error instanceof Error ? error.message : 'Unknown error'}`, true)
    }
  }

  const handleOpenSimulator = (medicineId: string) => {
    setSimulatorMedicineId(medicineId)
    setCurrentTab('simulator')
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
              <span style={{
                fontSize: '11px',
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: gmailMode === 'LIVE' ? 'var(--color-soft-green)' : 'var(--color-warning-bg)',
                color: gmailMode === 'LIVE' ? 'var(--color-dark-green)' : 'var(--color-warning-amber)',
                fontWeight: 600,
              }}>
                Gmail {gmailMode}
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
            backgroundColor: notificationIsError ? 'var(--color-critical-red)' : 'var(--color-dark-green)',
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
            {notificationIsError ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
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
              categoryRecommendations={categoryRecommendations}
              categoryRecommendationsError={categoryRecommendationsError}
              categoryRecommendationsLoading={categoryRecommendationsLoading}
              onDraftRecommendedRFQ={(medicineId) => {
                setRecommendedMedicineId(medicineId)
                setCurrentTab('inventory')
              }}
              onAddDemoSales={handleAddDemoSales}
              demoSalesLoading={demoSalesLoading}
            />
          )}

          {currentTab === 'inventory' && (
            <InventoryView
              items={inventory}
              onRefresh={loadData}
              onCreateRFQ={handleCreateRFQ}
              onSaveMedicine={handleSaveMedicine}
              onDeleteMedicine={handleDeleteMedicine}
              recommendedMedicineId={recommendedMedicineId}
              onRecommendationHandled={() => setRecommendedMedicineId(null)}
              isRadarOnly={false}
            />
          )}

          {currentTab === 'shortage_radar' && (
            <InventoryView
              items={inventory}
              onRefresh={loadData}
              onCreateRFQ={handleCreateRFQ}
              onSaveMedicine={handleSaveMedicine}
              onDeleteMedicine={handleDeleteMedicine}
              isRadarOnly={true}
            />
          )}

          {(currentTab === 'quote_requests' || currentTab === 'quote_inbox' || currentTab === 'suppliers') && (
            <QuotesView
              key={currentTab}
              requests={requests}
              quotes={quotes}
              suppliers={suppliers}
              onApproveAndSend={handleApproveAndSendRFQ}
              onSyncInbox={handleSyncSupplierInbox}
              onSaveSupplier={handleSaveSupplier}
              onDeleteSupplier={handleDeleteSupplier}
              initialTab={currentTab === 'suppliers' ? 'suppliers' : currentTab === 'quote_requests' ? 'requests' : 'inbox'}
              onSimulate={handleOpenSimulator}
            />
          )}

          {currentTab === 'simulator' && (
            <SimulatorView
              inventory={inventory}
              initialMedicineId={simulatorMedicineId}
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
            <SettingsView isLiveBackend={isLiveBackend} gmailMode={gmailMode} onSaveSettings={handleSaveSettings} />
          )}
        </div>
      </main>
    </div>
  )
}

export default App
