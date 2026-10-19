import React, { useState } from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  FileCheck2,
  Sliders,
} from 'lucide-react'
import { InventoryItem, Quotation, ScenarioOption, Supplier } from '../types'
import { api } from '../services/api'

interface SimulatorViewProps {
  inventory: InventoryItem[]
  quotes: Quotation[]
  suppliers: Supplier[]
  initialMedicineId: string
  onCreatePurchaseOrder: (option: ScenarioOption, medicineId: string, medicineName: string) => void
}

const normalizeMedicineName = (value: string | null | undefined) =>
  (value ?? '').toLocaleLowerCase().replace(/[^a-z0-9]/g, '')

const hasUsableQuote = (
  quote: Quotation,
  medicine: InventoryItem,
  verifiedSupplierIds: Set<string>,
) => {
  const medicineMatches = quote.medicine_id === medicine.medicine_id
    || normalizeMedicineName(quote.medicine_name) === normalizeMedicineName(medicine.name)
  const expiry = quote.valid_until
  const quoteIsCurrent = !expiry || (
    /^\d{4}-\d{2}-\d{2}$/.test(expiry)
    && expiry >= new Date().toISOString().slice(0, 10)
  )

  return quote.review_status === 'validated'
    && verifiedSupplierIds.has(quote.supplier_id)
    && medicineMatches
    && quote.price !== null
    && quote.price > 0
    && quote.currency.toUpperCase() === 'PKR'
    && quote.delivery_fee !== null
    && quote.quoted_quantity !== null
    && quote.delivery_days !== null
    && quote.delivery_days >= 0
    && quoteIsCurrent
}

export const SimulatorView: React.FC<SimulatorViewProps> = ({
  inventory,
  quotes,
  suppliers,
  initialMedicineId,
  onCreatePurchaseOrder,
}) => {
  const verifiedSupplierIds = new Set(suppliers.filter((supplier) => supplier.is_verified).map((supplier) => supplier.id))
  const medicineWithQuote = inventory.find((medicine) =>
    quotes.some((quote) => hasUsableQuote(quote, medicine, verifiedSupplierIds)),
  )
  const [selectedMedicineId, setSelectedMedicineId] = useState(initialMedicineId)
  const [orderQuantity, setOrderQuantity] = useState<number>(40)
  const [budgetLimit, setBudgetLimit] = useState<number>(25000)
  const [leadTimeTolerance, setLeadTimeTolerance] = useState<number>(4)
  const [demandSurgePercent, setDemandSurgePercent] = useState<number>(0)
  const [supplierDelayDays, setSupplierDelayDays] = useState<number>(0)
  const [scenarios, setScenarios] = useState<ScenarioOption[]>([])
  const [quotesEvaluated, setQuotesEvaluated] = useState(0)
  const [scenarioQuantity, setScenarioQuantity] = useState<number | null>(null)
  const [simulationComplete, setSimulationComplete] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const activeMedicineId = inventory.some((item) => item.medicine_id === selectedMedicineId)
    ? selectedMedicineId
    : medicineWithQuote?.medicine_id || inventory[0]?.medicine_id || ''
  const selectedMedicine = inventory.find((item) => item.medicine_id === activeMedicineId)
  const selectedQuoteCount = selectedMedicine
    ? quotes.filter((quote) => hasUsableQuote(quote, selectedMedicine, verifiedSupplierIds)).length
    : 0
  const quoteNeedsReview = selectedMedicine
    ? quotes.find((quote) =>
      quote.medicine_id === selectedMedicine.medicine_id
      && quote.review_status !== 'validated'
      && quote.warning_flags.includes('request_mismatch'),
    )
    : undefined
  const mismatchLabels = quoteNeedsReview?.mismatch_fields?.map((field) => ({
    medicine_name: 'product name',
    dosage_form: 'dosage form',
    pack_size: 'pack size',
    strength: 'strength',
  }[field] || field))

  const clearSimulation = () => {
    setScenarios([])
    setQuotesEvaluated(0)
    setScenarioQuantity(null)
    setSimulationComplete(false)
    setError(null)
  }

  const runSimulation = async () => {
    if (!activeMedicineId) {
      setError('Select a medicine before running the procurement simulation.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const result = await api.simulateProcurement({
        medicine_id: activeMedicineId,
        required_quantity: orderQuantity,
        budget_limit: budgetLimit,
        max_delivery_days: leadTimeTolerance,
        demand_surge_percent: demandSurgePercent,
        supplier_delay_days: supplierDelayDays,
      })
      setScenarios(result.options)
      setQuotesEvaluated(result.quotes_evaluated_count)
      setScenarioQuantity(result.required_quantity)
      setSimulationComplete(true)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Procurement simulation failed.')
      setScenarios([])
      setQuotesEvaluated(0)
      setScenarioQuantity(null)
      setSimulationComplete(false)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Simulation Controls Card */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <div style={{
            padding: '8px',
            backgroundColor: 'var(--color-pale-green)',
            color: 'var(--color-dark-green)',
            borderRadius: 'var(--radius-md)',
          }}>
            <Sliders size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Procurement Scenario Engine</h3>
            <p style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
              Deterministic trade-off optimizer balancing lead times, total landed costs, and MOQ constraints.
            </p>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Demand Surge (%)
            </label>
            <input type="number" min={0} max={500} value={demandSurgePercent} disabled={loading} onChange={(e) => {
              setDemandSurgePercent(Number(e.target.value))
              clearSimulation()
            }} />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Supplier Delay (Days)
            </label>
            <input type="number" min={0} max={365} value={supplierDelayDays} disabled={loading} onChange={(e) => {
              setSupplierDelayDays(Number(e.target.value))
              clearSimulation()
            }} />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Select Medicine
            </label>
            <select
              value={activeMedicineId}
              disabled={loading}
              onChange={(e) => {
                setSelectedMedicineId(e.target.value)
                clearSimulation()
              }}
              style={{ backgroundColor: '#FFFFFF' }}
            >
              {inventory.map((medicine) => (
                <option key={medicine.medicine_id} value={medicine.medicine_id}>{medicine.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Required Quantity (Packs)
            </label>
            <input
              type="number"
              min={10}
              max={500}
              step={5}
              value={orderQuantity}
              disabled={loading}
              onChange={(e) => {
                setOrderQuantity(Number(e.target.value))
                clearSimulation()
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Available Budget (PKR)
            </label>
            <input
              type="number"
              min={5000}
              max={100000}
              step={1000}
              value={budgetLimit}
              disabled={loading}
              onChange={(e) => {
                setBudgetLimit(Number(e.target.value))
                clearSimulation()
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Stockout Deadline (Days)
            </label>
            <input
              type="number"
              min={1}
              max={14}
              value={leadTimeTolerance}
              disabled={loading}
              onChange={(e) => {
                setLeadTimeTolerance(Number(e.target.value))
                clearSimulation()
              }}
            />
          </div>
        </div>
        <button
          onClick={runSimulation}
          disabled={!activeMedicineId || loading}
          style={{ marginTop: '16px', backgroundColor: 'var(--color-primary)', color: '#FFFFFF', fontWeight: 600 }}
        >
          {loading ? 'Calculating…' : 'Run Procurement Simulation'}
        </button>
      </div>

      {/* Evaluated Scenarios Grid */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '17px', fontWeight: 700 }}>Decision Options</h3>
          <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
            Comparing {quotesEvaluated} validated quotations for {scenarioQuantity ?? orderQuantity} packs
          </span>
        </div>

        {error && <div className="card" role="alert" style={{ color: 'var(--color-critical-red)' }}>{error}</div>}
        {!error && !simulationComplete && scenarios.length === 0 && (
          <div className="card" style={{ color: 'var(--color-text-muted)' }}>
            {selectedMedicine && selectedQuoteCount === 0
              ? quoteNeedsReview
                ? `A supplier quote exists for this RFQ, but it is marked needs review${mismatchLabels?.length ? ` because the ${mismatchLabels.join(', ')} do not match` : ''}. Supplier quoted: ${quoteNeedsReview.medicine_name}; RFQ requested: ${quoteNeedsReview.requested_medicine_name || selectedMedicine.name}. Get a corrected quote or create a matching RFQ before comparing.`
                : `No current validated PKR quotes with known delivery fees are available for ${selectedMedicine.name}. Choose a medicine with eligible quotes, or sync supplier replies and validate a quote first. Gmail LIVE indicates email connectivity; it does not mean a matching quote has been received.`
              : `Run the simulation to compare ${selectedQuoteCount} eligible validated supplier quote(s).`}
          </div>
        )}
        {!error && simulationComplete && scenarios.length === 0 && (
          <div className="card" role="status" style={{ color: 'var(--color-text-muted)' }}>
            {quotesEvaluated === 0
              ? quoteNeedsReview
                ? `A quote exists for this RFQ, but it cannot be compared because it needs review${mismatchLabels?.length ? `: ${mismatchLabels.join(', ')} mismatch` : ''}. Supplier quoted: ${quoteNeedsReview.medicine_name}; RFQ requested: ${quoteNeedsReview.requested_medicine_name || selectedMedicine?.name}. Request a corrected quote or create a matching RFQ.`
                : `No current validated PKR quotations with known delivery fees and complete pricing and delivery details were found for ${selectedMedicine?.name ?? 'this medicine'}. Verify the quote is matched to this medicine, the supplier is verified, and required quote details are present.`
              : `${quotesEvaluated} validated quotations were checked, but none can cover ${scenarioQuantity ?? orderQuantity} packs in a valid single- or split-supplier order.`}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          {scenarios.map((option, idx) => {
            const isRecommended = option.scenario_type === 'fastest' && option.feasibility_status === 'feasible'
            const isOverBudget = option.total_cost > budgetLimit
            const isStockoutRisk = option.delivery_days > leadTimeTolerance

            return (
              <div
                key={idx}
                className="card"
                style={{
                  border: isRecommended ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
                  backgroundColor: isRecommended ? 'linear-gradient(180deg, var(--color-pale-green) 0%, #FFFFFF 30%)' : '#FFFFFF',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: isRecommended ? '0 4px 12px rgba(85, 184, 63, 0.15)' : 'var(--shadow-card)',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      padding: '3px 8px',
                      borderRadius: 'var(--radius-full)',
                      backgroundColor: isRecommended ? 'var(--color-soft-green)' : 'var(--color-surface-hover)',
                      color: isRecommended ? 'var(--color-dark-green)' : 'var(--color-text-secondary)',
                    }}>
                      {option.title}
                    </span>

                    {isRecommended && (
                      <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-dark-green)', display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                        <CheckCircle2 size={13} /> BEST FIT
                      </span>
                    )}
                  </div>

                  <h4 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: '4px' }}>
                    {option.supplier_name}
                  </h4>

                  <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: '1.5', marginBottom: '16px' }}>
                    {option.explanation}
                  </p>

                  {/* Financial & Delivery Metrics */}
                  <div style={{
                    backgroundColor: 'var(--color-surface-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '14px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                    marginBottom: '16px',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                      <span style={{ color: 'var(--color-text-secondary)' }}>Total Landed Cost:</span>
                      <strong style={{ color: isOverBudget ? 'var(--color-critical-red)' : 'var(--color-text-primary)' }} className="tabular-nums">
                        PKR {option.total_cost.toLocaleString()}
                      </strong>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                      <span style={{ color: 'var(--color-text-secondary)' }}>Normalized Unit Price:</span>
                      <span style={{ fontWeight: 600 }} className="tabular-nums">PKR {option.unit_price} / pack</span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                      <span style={{ color: 'var(--color-text-secondary)' }}>Delivery Fee:</span>
                      <span style={{ fontWeight: 500 }} className="tabular-nums">
                        {option.delivery_fee > 0 ? `PKR ${option.delivery_fee}` : 'Free Delivery'}
                      </span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', borderTop: '1px solid var(--color-border-subtle)', paddingTop: '6px' }}>
                      <span style={{ color: 'var(--color-text-secondary)' }}>Lead Time:</span>
                      <strong style={{ color: isStockoutRisk ? 'var(--color-critical-red)' : 'var(--color-dark-green)' }}>
                        {option.delivery_days} Days
                      </strong>
                    </div>
                  </div>

                  {/* Risk & Safety Notice */}
                  {isStockoutRisk && (
                    <div style={{
                      fontSize: '11px',
                      color: 'var(--color-critical-red)',
                      backgroundColor: 'var(--color-critical-bg)',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      marginBottom: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}>
                      <AlertTriangle size={14} />
                      Warning: Delivery exceeds stockout timeline by {option.delivery_days - leadTimeTolerance} day(s).
                    </div>
                  )}
                </div>

                <button
                  onClick={() => selectedMedicine && onCreatePurchaseOrder(option, activeMedicineId, selectedMedicine.name)}
                  disabled={option.scenario_type === 'infeasible' || option.feasibility_status === 'infeasible'}
                  style={{
                    backgroundColor: isRecommended ? 'var(--color-primary)' : '#FFFFFF',
                    color: isRecommended ? '#FFFFFF' : 'var(--color-text-primary)',
                    border: isRecommended ? 'none' : '1px solid var(--color-border)',
                    padding: '10px 16px',
                    fontWeight: 600,
                    width: '100%',
                  }}
                >
                  <FileCheck2 size={15} />
                  {option.scenario_type === 'split_order' ? 'Draft Split Purchase Orders' : 'Draft Purchase Order'}
                </button>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
