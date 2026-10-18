import React from 'react'
import {
  AlertTriangle,
  Clock,
  MailCheck,
  FileCheck2,
  TrendingDown,
  ArrowRight,
  ShieldAlert,
  Info,
  Calendar,
  Sparkles,
} from 'lucide-react'
import { InventoryItem, Quotation, PurchaseOrder } from '../types'
import { StatusPill } from '../components/AppShell'

interface DashboardViewProps {
  inventory: InventoryItem[]
  quotes: Quotation[]
  orders: PurchaseOrder[]
  onNavigate: (tab: any) => void
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  inventory,
  quotes,
  orders,
  onNavigate,
}) => {
  const criticalItems = inventory.filter((i) => i.status === 'critical' || i.status === 'high')
  const pendingApprovals = orders.filter((o) => o.status === 'awaiting_approval')
  const pendingQuotes = quotes.filter((q) => q.review_status === 'pending')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* ROW 1: 4 TOP KPI CARDS */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '16px',
      }}>
        {/* KPI 1 */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text-secondary)' }}>
                Medicines at Risk
              </div>
              <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--color-critical-red)', marginTop: '4px' }}>
                {criticalItems.length}
              </div>
            </div>
            <div style={{
              padding: '10px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-critical-bg)',
              color: 'var(--color-critical-red)',
            }}>
              <AlertTriangle size={20} />
            </div>
          </div>
          <div style={{
            marginTop: '16px',
            fontSize: '12px',
            color: 'var(--color-text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span>2 Critical (&lt;4 days), 1 High risk</span>
            <button
              onClick={() => onNavigate('shortage_radar')}
              style={{ padding: '0', background: 'none', border: 'none', color: 'var(--color-primary)', fontWeight: 600, fontSize: '12px' }}
            >
              Radar &rarr;
            </button>
          </div>
        </div>

        {/* KPI 2 */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text-secondary)' }}>
                Avg Stock Coverage
              </div>
              <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: '4px' }}>
                7.4 <span style={{ fontSize: '16px', fontWeight: 500, color: 'var(--color-text-secondary)' }}>Days</span>
              </div>
            </div>
            <div style={{
              padding: '10px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-info-bg)',
              color: 'var(--color-info-blue)',
            }}>
              <Clock size={20} />
            </div>
          </div>
          <div style={{
            marginTop: '16px',
            fontSize: '12px',
            color: 'var(--color-text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span>Based on 30-day velocity</span>
            <button
              onClick={() => onNavigate('inventory')}
              style={{ padding: '0', background: 'none', border: 'none', color: 'var(--color-primary)', fontWeight: 600, fontSize: '12px' }}
            >
              Catalog &rarr;
            </button>
          </div>
        </div>

        {/* KPI 3 */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text-secondary)' }}>
                Active Quotations
              </div>
              <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: '4px' }}>
                {quotes.length}
              </div>
            </div>
            <div style={{
              padding: '10px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-pale-green)',
              color: 'var(--color-dark-green)',
            }}>
              <MailCheck size={20} />
            </div>
          </div>
          <div style={{
            marginTop: '16px',
            fontSize: '12px',
            color: 'var(--color-text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span>3 Verified Suppliers</span>
            <button
              onClick={() => onNavigate('quote_inbox')}
              style={{ padding: '0', background: 'none', border: 'none', color: 'var(--color-primary)', fontWeight: 600, fontSize: '12px' }}
            >
              Quotes &rarr;
            </button>
          </div>
        </div>

        {/* KPI 4 */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text-secondary)' }}>
                Pending Sign-Offs
              </div>
              <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--color-warning-amber)', marginTop: '4px' }}>
                {pendingApprovals.length}
              </div>
            </div>
            <div style={{
              padding: '10px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-warning-bg)',
              color: 'var(--color-warning-amber)',
            }}>
              <FileCheck2 size={20} />
            </div>
          </div>
          <div style={{
            marginTop: '16px',
            fontSize: '12px',
            color: 'var(--color-text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span>1 Draft PO requires signature</span>
            <button
              onClick={() => onNavigate('purchase_orders')}
              style={{ padding: '0', background: 'none', border: 'none', color: 'var(--color-primary)', fontWeight: 600, fontSize: '12px' }}
            >
              Review PO &rarr;
            </button>
          </div>
        </div>
      </div>

      {/* ROW 2: CALM CLINICAL SHORTAGE INTELLIGENCE PANEL (Signature Reference) */}
      <div style={{
        background: 'linear-gradient(135deg, var(--color-pale-green) 0%, #FFFFFF 100%)',
        border: '1px solid rgba(85, 184, 63, 0.3)',
        borderRadius: 'var(--radius-lg)',
        padding: '24px 28px',
        boxShadow: 'var(--shadow-card)',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ maxWidth: '680px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                backgroundColor: 'rgba(85, 184, 63, 0.2)',
                color: 'var(--color-dark-green)',
                borderRadius: 'var(--radius-full)',
                fontSize: '11px',
                fontWeight: 700,
                letterSpacing: '0.04em',
              }}>
                <Sparkles size={13} />
                OPERATIONAL INTELLIGENCE
              </span>
              <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                Evaluated deterministically at 22:00 PKT
              </span>
            </div>

            <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-dark-green)', marginBottom: '8px' }}>
              Stockout Warning: Panadol 500mg requires urgent replenishment
            </h2>

            <p style={{ fontSize: '13px', color: 'var(--color-text-primary)', lineHeight: '1.6', marginBottom: '14px' }}>
              Current usable inventory is down to <strong>15 packs</strong> against a daily dispense rate of 5 packs/day.
              Estimated stockout in <strong>3.0 days</strong>. Validated quotation available from <strong>Premier Sales & Distribution</strong> at PKR 480/pack with a 2-day lead time.
            </p>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
              <button
                onClick={() => onNavigate('simulator')}
                style={{
                  backgroundColor: 'var(--color-primary)',
                  color: '#FFFFFF',
                  padding: '9px 18px',
                  fontWeight: 600,
                  boxShadow: '0 2px 4px rgba(85, 184, 63, 0.3)',
                }}
              >
                Open Procurement Simulator
                <ArrowRight size={15} />
              </button>

              <button
                onClick={() => onNavigate('quote_inbox')}
                style={{
                  backgroundColor: '#FFFFFF',
                  color: 'var(--color-dark-green)',
                  border: '1px solid var(--color-border)',
                  padding: '9px 16px',
                  fontWeight: 600,
                }}
              >
                Compare 3 Supplier Quotes
              </button>
            </div>
          </div>

          <div style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: '16px',
            minWidth: '220px',
            boxShadow: 'var(--shadow-subtle)',
          }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
              Calculated Timing
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                <span style={{ color: 'var(--color-text-secondary)' }}>Stock Depletion:</span>
                <span style={{ fontWeight: 600, color: 'var(--color-critical-red)' }}>In 3 Days</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                <span style={{ color: 'var(--color-text-secondary)' }}>Fastest Delivery:</span>
                <span style={{ fontWeight: 600, color: 'var(--color-dark-green)' }}>2 Days (Premier)</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                <span style={{ color: 'var(--color-text-secondary)' }}>Stockout Avoided?</span>
                <span style={{ fontWeight: 700, color: 'var(--color-dark-green)' }}>Yes (+1 day buffer)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ROW 3 & 4: CRITICAL RADAR PREVIEW & RECENT QUOTATIONS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '20px' }}>
        {/* Critical Inventory Attention */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Urgent Replenishment Radar</h3>
            <button
              onClick={() => onNavigate('shortage_radar')}
              style={{ padding: '0', background: 'none', border: 'none', color: 'var(--color-primary)', fontWeight: 600, fontSize: '12px' }}
            >
              View All ({criticalItems.length})
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {criticalItems.map((item) => (
              <div
                key={item.medicine_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px',
                  backgroundColor: 'var(--color-surface-subtle)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-border-subtle)',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-text-primary)' }}>
                    {item.name}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                    Stock: {item.usable_stock} | Daily Demand: {item.avg_daily_demand}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: item.status === 'critical' ? 'var(--color-critical-red)' : 'var(--color-warning-amber)' }}>
                      {item.coverage_days ? `${item.coverage_days} Days` : 'Stockout'}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>coverage</div>
                  </div>
                  <StatusPill status={item.status} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quotations Awaiting Action */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Supplier Offers (Validated Quotes)</h3>
            <button
              onClick={() => onNavigate('quote_inbox')}
              style={{ padding: '0', background: 'none', border: 'none', color: 'var(--color-primary)', fontWeight: 600, fontSize: '12px' }}
            >
              Full Inbox &rarr;
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {quotes.slice(0, 3).map((q) => (
              <div
                key={q.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px',
                  backgroundColor: 'var(--color-surface-subtle)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-border-subtle)',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-text-primary)' }}>
                    {q.supplier_name}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                    {q.medicine_name} • {q.quoted_quantity ?? 'Not stated'} packs offered
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-dark-green)' }}>
                    {q.price === null ? 'Price not stated' : `${q.currency} ${q.price.toLocaleString()}`}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                    Delivery: {q.delivery_days === null ? 'Not stated' : `${q.delivery_days} days`}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ROW 5: DATA INTEGRITY & AUDIT SAFETY NOTICE */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '14px 18px',
        backgroundColor: '#FFFFFF',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
      }}>
        <ShieldAlert size={18} color="var(--color-primary)" />
        <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', flex: 1 }}>
          <strong>Human-in-the-Loop Safeguards Active:</strong> All outbound quotation emails and draft purchase orders require explicit pharmacist authorization. Calculations are executed strictly using deterministic Python logic.
        </div>
        <button
          onClick={() => onNavigate('audit_trail')}
          style={{ padding: '6px 12px', backgroundColor: 'var(--color-surface-hover)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)', fontSize: '12px' }}
        >
          Inspect Audit Trail
        </button>
      </div>
    </div>
  )
}
