import React, { useState } from 'react'
import {
  Mail,
  Send,
  CheckCircle,
  Clock,
  ShieldCheck,
  Building2,
  FileCheck2,
  AlertCircle,
  Inbox,
  ArrowRight,
  Sparkles,
} from 'lucide-react'
import { QuotationRequest, Quotation, Supplier } from '../types'
import { StatusPill } from '../components/AppShell'

interface QuotesViewProps {
  requests: QuotationRequest[]
  quotes: Quotation[]
  suppliers: Supplier[]
  onApproveAndSend: (requestId: string) => void
  onSimulate: (medicineName: string, quotes: Quotation[]) => void
}

export const QuotesView: React.FC<QuotesViewProps> = ({
  requests,
  quotes,
  suppliers,
  onApproveAndSend,
  onSimulate,
}) => {
  const [activeTab, setActiveTab] = useState<'requests' | 'inbox' | 'suppliers'>('inbox')
  const [selectedQuote, setSelectedQuote] = useState<Quotation | null>(quotes[0] || null)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
        <button
          onClick={() => setActiveTab('inbox')}
          style={{
            backgroundColor: activeTab === 'inbox' ? 'var(--color-primary)' : '#FFFFFF',
            color: activeTab === 'inbox' ? '#FFFFFF' : 'var(--color-text-secondary)',
            border: activeTab === 'inbox' ? 'none' : '1px solid var(--color-border)',
            fontWeight: 600,
          }}
        >
          <Inbox size={15} />
          Quote Inbox ({quotes.length})
        </button>

        <button
          onClick={() => setActiveTab('requests')}
          style={{
            backgroundColor: activeTab === 'requests' ? 'var(--color-primary)' : '#FFFFFF',
            color: activeTab === 'requests' ? '#FFFFFF' : 'var(--color-text-secondary)',
            border: activeTab === 'requests' ? 'none' : '1px solid var(--color-border)',
            fontWeight: 600,
          }}
        >
          <Mail size={15} />
          Quote Requests (RFQ) ({requests.length})
        </button>

        <button
          onClick={() => setActiveTab('suppliers')}
          style={{
            backgroundColor: activeTab === 'suppliers' ? 'var(--color-primary)' : '#FFFFFF',
            color: activeTab === 'suppliers' ? '#FFFFFF' : 'var(--color-text-secondary)',
            border: activeTab === 'suppliers' ? 'none' : '1px solid var(--color-border)',
            fontWeight: 600,
          }}
        >
          <Building2 size={15} />
          Verified Suppliers ({suppliers.length})
        </button>
      </div>

      {/* 1. QUOTE INBOX & COMPARISON VIEW */}
      {activeTab === 'inbox' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1.2fr) minmax(360px, 1fr)', gap: '20px' }}>
          {/* Quotes List Table */}
          <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Supplier Offers (Parsed via Gmail)</h3>
                <p style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Structured quote extraction with anomaly detection</p>
              </div>
              <button
                onClick={() => onSimulate('Panadol 500mg Tablets', quotes)}
                style={{
                  backgroundColor: 'var(--color-primary)',
                  color: '#FFFFFF',
                  fontSize: '12px',
                  fontWeight: 600,
                  padding: '6px 12px',
                }}
              >
                Compare in Simulator &rarr;
              </button>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                <thead>
                  <tr style={{ backgroundColor: 'var(--color-surface-subtle)', borderBottom: '1px solid var(--color-border)' }}>
                    <th style={{ padding: '10px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Supplier</th>
                    <th style={{ padding: '10px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Medicine</th>
                    <th style={{ padding: '10px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', textAlign: 'right' }}>Price</th>
                    <th style={{ padding: '10px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', textAlign: 'right' }}>Lead Time</th>
                    <th style={{ padding: '10px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Validation</th>
                  </tr>
                </thead>
                <tbody>
                  {quotes.map((q) => {
                    const isSelected = selectedQuote?.id === q.id
                    return (
                      <tr
                        key={q.id}
                        onClick={() => setSelectedQuote(q)}
                        style={{
                          backgroundColor: isSelected ? 'var(--color-pale-green)' : 'transparent',
                          borderBottom: '1px solid var(--color-border-subtle)',
                          cursor: 'pointer',
                          transition: 'background-color 0.15s ease',
                        }}
                      >
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{q.supplier_name}</div>
                          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>MOQ: {q.minimum_order_quantity}</div>
                        </td>
                        <td style={{ padding: '12px 16px', color: 'var(--color-text-secondary)' }}>
                          <div>{q.medicine_name}</div>
                          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Offered: {q.quoted_quantity} packs</div>
                        </td>
                        <td style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 600, color: 'var(--color-dark-green)' }} className="tabular-nums">
                          PKR {q.price}
                        </td>
                        <td style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--color-text-secondary)' }}>
                          {q.delivery_days} Days
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <StatusPill status={q.review_status} />
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Selected Quote Detail & Discrepancy Breakdown */}
          {selectedQuote ? (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                    Quote Breakdown #{selectedQuote.id}
                  </span>
                  <StatusPill status={selectedQuote.review_status} />
                </div>
                <h3 style={{ fontSize: '18px', fontWeight: 700, marginTop: '6px', color: 'var(--color-text-primary)' }}>
                  {selectedQuote.supplier_name}
                </h3>
                <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                  Target Product: {selectedQuote.medicine_name}
                </div>
              </div>

              {/* Discrepancy Warnings */}
              {selectedQuote.warning_flags.length > 0 && (
                <div style={{
                  padding: '12px 16px',
                  backgroundColor: 'var(--color-warning-bg)',
                  border: '1px solid rgba(200, 137, 25, 0.3)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px',
                }}>
                  <AlertCircle size={18} color="var(--color-warning-amber)" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-warning-amber)' }}>
                      Quotation Anomaly Detected
                    </div>
                    {selectedQuote.warning_flags.map((flag, idx) => (
                      <div key={idx} style={{ fontSize: '12px', color: 'var(--color-text-primary)', marginTop: '2px' }}>
                        • {flag}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Metrics Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                <div style={{ padding: '12px', backgroundColor: 'var(--color-surface-subtle)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Unit Price</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-dark-green)', marginTop: '2px' }}>
                    PKR {selectedQuote.price} <span style={{ fontSize: '11px', fontWeight: 400 }}>/{selectedQuote.price_unit}</span>
                  </div>
                </div>

                <div style={{ padding: '12px', backgroundColor: 'var(--color-surface-subtle)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Delivery Fee</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                    {selectedQuote.delivery_fee > 0 ? `PKR ${selectedQuote.delivery_fee}` : 'Free Delivery'}
                  </div>
                </div>

                <div style={{ padding: '12px', backgroundColor: 'var(--color-surface-subtle)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Lead Time</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                    {selectedQuote.delivery_days} Days
                  </div>
                </div>

                <div style={{ padding: '12px', backgroundColor: 'var(--color-surface-subtle)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Quote Validity</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                    Until {selectedQuote.valid_until}
                  </div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                  Payment Terms
                </div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-primary)', backgroundColor: 'var(--color-surface-subtle)', padding: '8px 12px', borderRadius: 'var(--radius-md)' }}>
                  {selectedQuote.payment_terms}
                </div>
              </div>

              <div style={{ marginTop: 'auto', paddingTop: '12px', display: 'flex', gap: '10px' }}>
                <button
                  onClick={() => onSimulate(selectedQuote.medicine_name, quotes)}
                  style={{
                    flex: 1,
                    backgroundColor: 'var(--color-primary)',
                    color: '#FFFFFF',
                    fontWeight: 600,
                  }}
                >
                  Evaluate in Simulator
                  <ArrowRight size={15} />
                </button>
              </div>
            </div>
          ) : (
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)' }}>
              Select a supplier quote to inspect details
            </div>
          )}
        </div>
      )}

      {/* 2. QUOTE REQUESTS (RFQ) & HUMAN-IN-THE-LOOP APPROVAL */}
      {activeTab === 'requests' && (
        <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)' }}>
            <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Quotation Requests (RFQs)</h3>
            <p style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
              Human-in-the-loop: Outbound quotation emails are paused until explicitly approved by the pharmacist.
            </p>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--color-surface-subtle)', borderBottom: '1px solid var(--color-border)' }}>
                  <th style={{ padding: '12px 18px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Target Medicine</th>
                  <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', textAlign: 'right' }}>Req. Quantity</th>
                  <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Needed By</th>
                  <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Delivery Location</th>
                  <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Status</th>
                  <th style={{ padding: '12px 18px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', textAlign: 'right' }}>Pharmacist Action</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((r) => (
                  <tr key={r.id} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    <td style={{ padding: '14px 18px' }}>
                      <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{r.medicine_name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Ref #{r.id}</div>
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 600 }} className="tabular-nums">
                      {r.required_quantity} packs
                    </td>
                    <td style={{ padding: '14px 16px', color: 'var(--color-text-secondary)' }}>
                      {r.required_by_date}
                    </td>
                    <td style={{ padding: '14px 16px', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
                      {r.delivery_location}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <StatusPill status={r.status} />
                    </td>
                    <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                      {r.status === 'awaiting_approval' ? (
                        <button
                          onClick={() => onApproveAndSend(r.id)}
                          style={{
                            padding: '6px 14px',
                            backgroundColor: 'var(--color-primary)',
                            color: '#FFFFFF',
                            fontSize: '12px',
                            fontWeight: 600,
                          }}
                        >
                          <Send size={13} />
                          Approve & Send (Gmail)
                        </button>
                      ) : (
                        <span style={{ fontSize: '12px', color: 'var(--color-dark-green)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <CheckCircle size={14} /> Approved & Sent
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3. VERIFIED SUPPLIERS VIEW */}
      {activeTab === 'suppliers' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          {suppliers.map((s) => (
            <div key={s.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ fontWeight: 700, fontSize: '16px', color: 'var(--color-text-primary)' }}>
                  {s.name}
                </div>
                {s.is_verified && (
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: 'var(--color-soft-green)',
                    color: 'var(--color-dark-green)',
                    fontSize: '11px',
                    fontWeight: 600,
                  }}>
                    <ShieldCheck size={13} /> Verified
                  </span>
                )}
              </div>

              <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px', color: 'var(--color-text-secondary)' }}>
                <div><strong>Email:</strong> {s.email}</div>
                <div><strong>Phone:</strong> {s.phone}</div>
                <div><strong>Address:</strong> {s.address}</div>
                <div><strong>Standard Lead Time:</strong> {s.default_lead_time_days} days</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
