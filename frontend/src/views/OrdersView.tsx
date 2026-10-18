import React from 'react'
import {
  CheckCircle,
  ShieldCheck,
  Building,
} from 'lucide-react'
import { PurchaseOrder } from '../types'
import { StatusPill } from '../components/AppShell'

interface OrdersViewProps {
  orders: PurchaseOrder[]
  onApprovePO: (id: string) => void
  onRejectPO: (id: string) => void
}

export const OrdersView: React.FC<OrdersViewProps> = ({
  orders,
  onApprovePO,
  onRejectPO,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Human Safeguard Banner */}
      <div style={{
        padding: '16px 20px',
        backgroundColor: '#FFFFFF',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        flexWrap: 'wrap',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            padding: '10px',
            backgroundColor: 'var(--color-pale-green)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-dark-green)',
          }}>
            <ShieldCheck size={22} />
          </div>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700 }}>Human-in-the-Loop Safeguards Active</h3>
            <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
              No purchase orders are placed automatically. Explicit pharmacist approval and digital signature are mandatory to commit orders.
            </p>
          </div>
        </div>
      </div>

      {/* Orders Table */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Purchase Orders & Draft Commitments</h3>
          <p style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
            Generated from simulation decisions and awaiting human sign-off
          </p>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--color-surface-subtle)', borderBottom: '1px solid var(--color-border)' }}>
                <th style={{ padding: '12px 18px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>PO Number & Supplier</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Medicine & Pack</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', textAlign: 'right' }}>Quantity</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', textAlign: 'right' }}>Total Amount</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Est. Lead Time</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Status</th>
                <th style={{ padding: '12px 18px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', textAlign: 'right' }}>Approval Action</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((po) => (
                <tr key={po.id} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <td style={{ padding: '14px 18px' }}>
                    <div style={{ fontWeight: 700, color: 'var(--color-text-primary)' }}>{po.po_number}</div>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Building size={12} /> {po.supplier_name || 'Not stated'}
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px', color: 'var(--color-text-secondary)' }}>
                    <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{po.medicine_name || 'Not stated'}</div>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>{po.pack_size || 'Not stated'}</div>
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 600 }} className="tabular-nums">
                    {po.quantity === null ? 'Not stated' : `${po.quantity} packs`}
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 700, color: 'var(--color-dark-green)' }} className="tabular-nums">
                    PKR {po.total_amount.toLocaleString()}
                  </td>
                  <td style={{ padding: '14px 16px', color: 'var(--color-text-secondary)' }}>
                    {po.delivery_estimate_days === null ? 'Not stated' : `${po.delivery_estimate_days} Days`}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <StatusPill status={po.status} />
                  </td>
                  <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                    {po.status === 'awaiting_approval' ? (
                      <div style={{ display: 'inline-flex', gap: '6px' }}>
                        <button
                          onClick={() => onApprovePO(po.id)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: 'var(--color-primary)',
                            color: '#FFFFFF',
                            fontSize: '12px',
                            fontWeight: 600,
                          }}
                        >
                          <CheckCircle size={13} />
                          Approve Sign-off
                        </button>
                        <button
                          onClick={() => onRejectPO(po.id)}
                          style={{
                            padding: '6px 10px',
                            backgroundColor: '#FFFFFF',
                            border: '1px solid var(--color-border)',
                            color: 'var(--color-critical-red)',
                            fontSize: '12px',
                          }}
                        >
                          Reject
                        </button>
                      </div>
                    ) : (
                        <div style={{ textAlign: 'right', fontSize: '12px', color: 'var(--color-dark-green)', fontWeight: 600 }}>
                          {po.approved_by ? `Approved by ${po.approved_by}` : 'No approval recorded'}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
