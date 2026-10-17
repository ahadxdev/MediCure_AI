import React, { useState } from 'react'
import {
  Calculator,
  Truck,
  DollarSign,
  TrendingUp,
  CheckCircle2,
  AlertTriangle,
  FileCheck2,
  ArrowRight,
  ShieldAlert,
  Sliders,
} from 'lucide-react'
import { Quotation, ScenarioOption, PurchaseOrder } from '../types'
import { api } from '../services/api'

interface SimulatorViewProps {
  quotes: Quotation[]
  onCreatePurchaseOrder: (option: ScenarioOption, medicineName: string) => void
}

export const SimulatorView: React.FC<SimulatorViewProps> = ({
  quotes,
  onCreatePurchaseOrder,
}) => {
  const [selectedMedicine, setSelectedMedicine] = useState('Panadol 500mg Tablets')
  const [orderQuantity, setOrderQuantity] = useState<number>(40)
  const [budgetLimit, setBudgetLimit] = useState<number>(25000)
  const [leadTimeTolerance, setLeadTimeTolerance] = useState<number>(4)

  const medicineQuotes = quotes.filter((q) => q.medicine_name === selectedMedicine)
  const scenarios = api.simulateProcurement(selectedMedicine, orderQuantity, medicineQuotes)

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
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Select Medicine
            </label>
            <select
              value={selectedMedicine}
              onChange={(e) => setSelectedMedicine(e.target.value)}
              style={{ backgroundColor: '#FFFFFF' }}
            >
              <option value="Panadol 500mg Tablets">Panadol 500mg Tablets</option>
              <option value="Augmentin 625mg Tablets">Augmentin 625mg Tablets</option>
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
              onChange={(e) => setOrderQuantity(Number(e.target.value))}
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
              onChange={(e) => setBudgetLimit(Number(e.target.value))}
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
              onChange={(e) => setLeadTimeTolerance(Number(e.target.value))}
            />
          </div>
        </div>
      </div>

      {/* Evaluated Scenarios Grid */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '17px', fontWeight: 700 }}>Feasible Decision Options</h3>
          <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
            Comparing {medicineQuotes.length} validated quotations for {orderQuantity} packs
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          {scenarios.map((option, idx) => {
            const isRecommended = option.scenario_type === 'fastest'
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
                  onClick={() => onCreatePurchaseOrder(option, selectedMedicine)}
                  disabled={option.scenario_type === 'infeasible'}
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
                  Draft Purchase Order
                </button>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
