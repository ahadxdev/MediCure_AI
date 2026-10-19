import React, { useEffect, useState } from 'react'
import {
  Mail,
  Send,
  CheckCircle,
  ShieldCheck,
  Building2,
  AlertCircle,
  Inbox,
  ArrowRight,
  Plus,
  Pencil,
  Trash2,
} from 'lucide-react'
import { QuotationRequest, Quotation, Supplier, SupplierInput } from '../types'
import { StatusPill } from '../components/AppShell'

interface QuotesViewProps {
  requests: QuotationRequest[]
  quotes: Quotation[]
  suppliers: Supplier[]
  onApproveAndSend: (requestId: string) => void
  onSyncInbox: () => void
  onValidateQuote: (quotationId: string) => Promise<boolean>
  onSimulate: (medicineId: string) => void
  onSaveSupplier: (supplierId: string | null, payload: SupplierInput) => Promise<boolean>
  onDeleteSupplier: (supplierId: string) => Promise<boolean>
  initialTab: 'requests' | 'inbox' | 'suppliers'
}

export const QuotesView: React.FC<QuotesViewProps> = ({
  requests,
  quotes,
  suppliers,
  onApproveAndSend,
  onSyncInbox,
  onValidateQuote,
  onSimulate,
  onSaveSupplier,
  onDeleteSupplier,
  initialTab,
}) => {
  const [activeTab, setActiveTab] = useState<'requests' | 'inbox' | 'suppliers'>(initialTab)
  const [selectedQuote, setSelectedQuote] = useState<Quotation | null>(quotes[0] || null)
  const [supplierFormOpen, setSupplierFormOpen] = useState(false)
  const [confirmMedicineMatch, setConfirmMedicineMatch] = useState(false)
  const [validatingQuote, setValidatingQuote] = useState(false)
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null)
  const [supplierDraft, setSupplierDraft] = useState<SupplierInput>({
    name: '',
    email: '',
    phone: '',
    address: '',
    is_verified: true,
    default_lead_time_days: null,
  })

  useEffect(() => {
    if (!selectedQuote) {
      setSelectedQuote(quotes[0] || null)
      return
    }
    const updatedQuote = quotes.find((quote) => quote.id === selectedQuote.id)
    if (updatedQuote) setSelectedQuote(updatedQuote)
  }, [quotes, selectedQuote])

  const openSupplierForm = (supplier?: Supplier) => {
    setEditingSupplier(supplier || null)
    setSupplierDraft(supplier ? {
      name: supplier.name,
      email: supplier.email,
      phone: supplier.phone,
      address: supplier.address,
      is_verified: supplier.is_verified,
      default_lead_time_days: supplier.default_lead_time_days,
    } : {
      name: '',
      email: '',
      phone: '',
      address: '',
      is_verified: true,
      default_lead_time_days: null,
    })
    setSupplierFormOpen(true)
  }

  const saveSupplier = async (event: React.FormEvent) => {
    event.preventDefault()
    const saved = await onSaveSupplier(editingSupplier?.id || null, supplierDraft)
    if (saved) setSupplierFormOpen(false)
  }

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
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <button
                  onClick={onSyncInbox}
                  style={{
                    backgroundColor: 'var(--color-soft-green)',
                    color: 'var(--color-dark-green)',
                    fontSize: '12px',
                    fontWeight: 600,
                    padding: '6px 12px',
                    border: '1px solid rgba(19, 127, 87, 0.2)',
                  }}
                >
                  Sync Gmail Replies
                </button>
                <button
                  onClick={() => {
                    if (quotes[0]?.medicine_id) onSimulate(quotes[0].medicine_id)
                  }}
                  disabled={!quotes[0]?.medicine_id}
                  style={{
                    backgroundColor: 'var(--color-primary)',
                    color: '#FFFFFF',
                    fontSize: '12px',
                    fontWeight: 600,
                    padding: '6px 12px',
                    opacity: quotes[0]?.medicine_id ? 1 : 0.5,
                  }}
                >
                  Compare in Simulator &rarr;
                </button>
              </div>
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
                          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>MOQ: {q.minimum_order_quantity ?? 'Not stated'}</div>
                        </td>
                        <td style={{ padding: '12px 16px', color: 'var(--color-text-secondary)' }}>
                          <div>{q.medicine_name}</div>
                          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Offered: {q.quoted_quantity ?? 'Not stated'} packs</div>
                        </td>
                        <td style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 600, color: 'var(--color-dark-green)' }} className="tabular-nums">
                          {q.price === null ? 'Not stated' : `${q.currency} ${q.price}`}
                        </td>
                        <td style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--color-text-secondary)' }}>
                          {q.delivery_days === null ? 'Not stated' : `${q.delivery_days} Days`}
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
                  Supplier quoted: {selectedQuote.medicine_name}
                </div>
                {selectedQuote.requested_medicine_name && (
                  <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                    RFQ requested: {selectedQuote.requested_medicine_name}
                  </div>
                )}
              </div>

              {/* Discrepancy Warnings */}
              {(selectedQuote.warning_flags.length > 0 || (selectedQuote.mismatch_fields?.length ?? 0) > 0) && (
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
                    <div style={{ fontSize: '12px', fontWeight: 700, color: selectedQuote.review_status === 'validated' ? 'var(--color-dark-green)' : 'var(--color-warning-amber)' }}>
                      {selectedQuote.review_status === 'validated' ? 'Medicine match manually confirmed' : 'Quotation Anomaly Detected'}
                    </div>
                    {selectedQuote.mismatch_fields && selectedQuote.mismatch_fields.length > 0 && (
                      <div style={{ fontSize: '12px', color: 'var(--color-text-primary)', marginTop: '4px' }}>
                        {selectedQuote.review_status === 'validated'
                          ? 'A pharmacist confirmed this quoted product is acceptable for the requested medicine. Original differences remain visible: '
                          : 'RFQ mismatch: '}
                        {selectedQuote.mismatch_fields.map((field) => ({
                          medicine_name: 'product name',
                          dosage_form: 'dosage form',
                          pack_size: 'pack size',
                          strength: 'strength',
                        }[field] || field)).join(', ')}
                        {selectedQuote.review_status !== 'validated' && '. Correct the quote or explicitly confirm the match below.'}
                      </div>
                    )}
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
                    {selectedQuote.price === null ? 'Not stated' : `${selectedQuote.currency} ${selectedQuote.price}`}
                    {selectedQuote.price_unit && <span style={{ fontSize: '11px', fontWeight: 400 }}>/{selectedQuote.price_unit}</span>}
                  </div>
                </div>

                <div style={{ padding: '12px', backgroundColor: 'var(--color-surface-subtle)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Delivery Fee</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                    {selectedQuote.delivery_fee === null ? 'Not stated' : selectedQuote.delivery_fee > 0 ? `${selectedQuote.currency} ${selectedQuote.delivery_fee}` : 'Free Delivery'}
                  </div>
                </div>

                <div style={{ padding: '12px', backgroundColor: 'var(--color-surface-subtle)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Lead Time</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                    {selectedQuote.delivery_days === null ? 'Not stated' : `${selectedQuote.delivery_days} Days`}
                  </div>
                </div>

                <div style={{ padding: '12px', backgroundColor: 'var(--color-surface-subtle)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Quote Validity</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                    {selectedQuote.valid_until ? `Until ${selectedQuote.valid_until}` : 'Not stated'}
                  </div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                  Payment Terms
                </div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-primary)', backgroundColor: 'var(--color-surface-subtle)', padding: '8px 12px', borderRadius: 'var(--radius-md)' }}>
                  {selectedQuote.payment_terms || 'Not stated'}
                </div>
              </div>

              <div style={{ marginTop: 'auto', paddingTop: '12px', display: 'flex', gap: '10px' }}>
                {selectedQuote.review_status !== 'validated' && (selectedQuote.mismatch_fields?.length ?? 0) > 0 && (
                  <div style={{ width: '100%', padding: '12px', backgroundColor: 'var(--color-warning-bg)', borderRadius: 'var(--radius-md)' }}>
                    <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '12px', color: 'var(--color-text-primary)' }}>
                      <input
                        type="checkbox"
                        checked={confirmMedicineMatch}
                        onChange={(event) => setConfirmMedicineMatch(event.target.checked)}
                      />
                      I checked the supplier’s quotation and confirm it is for the requested medicine.
                    </label>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '6px' }}>
                      This confirms only the medicine match. A verified supplier, PKR price, delivery fee, available quantity, delivery time, and non-expired quote are still required.
                    </div>
                    <button
                      onClick={async () => {
                        setValidatingQuote(true)
                        const validated = await onValidateQuote(selectedQuote.id)
                        if (validated) setConfirmMedicineMatch(false)
                        setValidatingQuote(false)
                      }}
                      disabled={!confirmMedicineMatch || validatingQuote}
                      style={{ marginTop: '10px', backgroundColor: 'var(--color-primary)', color: '#FFFFFF', fontWeight: 600 }}
                    >
                      {validatingQuote ? 'Validating…' : 'Confirm match & validate quote'}
                    </button>
                  </div>
                )}
                <button
                  onClick={() => onSimulate(selectedQuote.medicine_id)}
                  disabled={!selectedQuote.medicine_id}
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <p style={{ fontSize: '13px' }}>Manage the supplier directory used for procurement communications.</p>
            <button
              onClick={() => openSupplierForm()}
              style={{ backgroundColor: 'var(--color-primary)', color: '#FFFFFF', fontWeight: 600 }}
            >
              <Plus size={14} />
              Add Supplier
            </button>
          </div>
          {suppliers.length === 0 ? (
            <div className="card" style={{ color: 'var(--color-text-muted)', textAlign: 'center' }}>No suppliers have been added.</div>
          ) : (
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
                  <div><strong>Phone:</strong> {s.phone || '—'}</div>
                  <div><strong>Address:</strong> {s.address || '—'}</div>
                  <div><strong>Standard Lead Time:</strong> {s.default_lead_time_days === null ? '—' : `${s.default_lead_time_days} days`}</div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '16px' }}>
                  <button onClick={() => openSupplierForm(s)} aria-label={`Edit ${s.name}`}>
                    <Pencil size={14} /> Edit
                  </button>
                  <button
                    onClick={async () => {
                      if (window.confirm(`Delete ${s.name}? Suppliers with quotation history cannot be deleted.`)) {
                        await onDeleteSupplier(s.id)
                      }
                    }}
                    aria-label={`Delete ${s.name}`}
                    style={{ color: 'var(--color-critical-red)' }}
                  >
                    <Trash2 size={14} /> Delete
                  </button>
                </div>
              </div>
              ))}
            </div>
          )}
        </div>
      )}

      {supplierFormOpen && (
        <div
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setSupplierFormOpen(false)
          }}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(23, 27, 25, 0.42)',
            display: 'grid',
            placeItems: 'center',
            padding: '20px',
            zIndex: 1100,
          }}
        >
          <form
            role="dialog"
            aria-modal="true"
            aria-labelledby="supplier-form-title"
            onSubmit={saveSupplier}
            className="card"
            style={{ width: 'min(540px, 100%)', display: 'flex', flexDirection: 'column', gap: '14px' }}
          >
            <h3 id="supplier-form-title">{editingSupplier ? 'Edit Supplier' : 'Add Supplier'}</h3>
            <label style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px', fontWeight: 600 }}>
              Supplier name
              <input
                required
                maxLength={255}
                value={supplierDraft.name}
                onChange={(event) => setSupplierDraft({ ...supplierDraft, name: event.target.value })}
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px', fontWeight: 600 }}>
              Email
              <input
                required
                type="email"
                maxLength={255}
                value={supplierDraft.email}
                onChange={(event) => setSupplierDraft({ ...supplierDraft, email: event.target.value })}
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px', fontWeight: 600 }}>
              Phone
              <input
                maxLength={50}
                value={supplierDraft.phone || ''}
                onChange={(event) => setSupplierDraft({ ...supplierDraft, phone: event.target.value || null })}
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px', fontWeight: 600 }}>
              Address
              <textarea
                rows={2}
                value={supplierDraft.address || ''}
                onChange={(event) => setSupplierDraft({ ...supplierDraft, address: event.target.value || null })}
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px', fontWeight: 600 }}>
              Default lead time (days)
              <input
                type="number"
                min="0"
                step="any"
                value={supplierDraft.default_lead_time_days ?? ''}
                onChange={(event) => setSupplierDraft({
                  ...supplierDraft,
                  default_lead_time_days: event.target.value ? Number(event.target.value) : null,
                })}
              />
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
              <input
                type="checkbox"
                checked={supplierDraft.is_verified}
                onChange={(event) => setSupplierDraft({ ...supplierDraft, is_verified: event.target.checked })}
                style={{ width: 'auto' }}
              />
              Verified supplier
            </label>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button type="button" onClick={() => setSupplierFormOpen(false)}>Cancel</button>
              <button type="submit" style={{ backgroundColor: 'var(--color-primary)', color: '#FFFFFF', fontWeight: 600 }}>
                {editingSupplier ? 'Save Changes' : 'Create Supplier'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
