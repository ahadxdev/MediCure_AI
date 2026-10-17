import React, { useState } from 'react'
import { Search, Filter, AlertTriangle, ArrowUpDown, RefreshCw, CheckCircle, HelpCircle } from 'lucide-react'
import { InventoryItem } from '../types'
import { StatusPill } from '../components/AppShell'

interface InventoryViewProps {
  items: InventoryItem[]
  onRefresh: () => void
  onDraftRFQ: (item: InventoryItem) => void
  isRadarOnly?: boolean
}

export const InventoryView: React.FC<InventoryViewProps> = ({
  items,
  onRefresh,
  onDraftRFQ,
  isRadarOnly = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('all')

  const displayedItems = items
    .filter((item) => {
      if (isRadarOnly) {
        return item.status === 'critical' || item.status === 'high' || item.status === 'moderate'
      }
      return true
    })
    .filter((item) => {
      const matchesSearch =
        item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.generic_name && item.generic_name.toLowerCase().includes(searchTerm.toLowerCase()))
      const matchesFilter = filterStatus === 'all' || item.status === filterStatus
      return matchesSearch && matchesFilter
    })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Search and Filter Controls */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '12px',
        flexWrap: 'wrap',
      }}>
        <div style={{ position: 'relative', width: '320px', maxWidth: '100%' }}>
          <Search size={16} color="var(--color-text-muted)" style={{ position: 'absolute', left: '12px', top: '10px' }} />
          <input
            type="text"
            placeholder="Search medicine or generic formulation..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ paddingLeft: '36px' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            style={{ width: 'auto', backgroundColor: '#FFFFFF' }}
          >
            <option value="all">All Risk Levels</option>
            <option value="critical">Critical (&lt;4 days)</option>
            <option value="high">High Risk (4-7 days)</option>
            <option value="moderate">Moderate Risk</option>
            <option value="low">Safe Stock</option>
            <option value="unknown">Insufficient Data</option>
          </select>

          <button
            onClick={onRefresh}
            style={{
              backgroundColor: '#FFFFFF',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-secondary)',
            }}
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>
      </div>

      {/* Main Inventory & Radar Table */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--color-surface-subtle)', borderBottom: '1px solid var(--color-border)' }}>
                <th style={{ padding: '12px 18px', fontWeight: 600, color: 'var(--color-text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>
                  Medicine & Generic
                </th>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--color-text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>
                  Dosage & Pack
                </th>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--color-text-muted)', fontSize: '11px', textTransform: 'uppercase', textAlign: 'right' }}>
                  Usable Stock
                </th>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--color-text-muted)', fontSize: '11px', textTransform: 'uppercase', textAlign: 'right' }}>
                  Reorder Level
                </th>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--color-text-muted)', fontSize: '11px', textTransform: 'uppercase', textAlign: 'right' }}>
                  Daily Demand
                </th>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--color-text-muted)', fontSize: '11px', textTransform: 'uppercase', textAlign: 'right' }}>
                  Coverage
                </th>
                <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--color-text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>
                  Risk Status
                </th>
                <th style={{ padding: '12px 18px', fontWeight: 600, color: 'var(--color-text-muted)', fontSize: '11px', textTransform: 'uppercase', textAlign: 'right' }}>
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {displayedItems.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ padding: '36px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                    No medicine catalog records found matching current criteria.
                  </td>
                </tr>
              ) : (
                displayedItems.map((item, idx) => (
                  <tr
                    key={item.medicine_id}
                    style={{
                      borderBottom: idx === displayedItems.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                      transition: 'background-color 0.1s ease',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--color-surface-hover)')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <td style={{ padding: '14px 18px' }}>
                      <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{item.name}</div>
                      <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>{item.generic_name || '—'}</div>
                    </td>
                    <td style={{ padding: '14px 16px', color: 'var(--color-text-secondary)' }}>
                      <div>{item.dosage_form} • {item.strength}</div>
                      <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>{item.pack_size}</div>
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 600, color: 'var(--color-text-primary)' }} className="tabular-nums">
                      {item.usable_stock}
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right', color: 'var(--color-text-secondary)' }} className="tabular-nums">
                      {item.reorder_level}
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right', color: 'var(--color-text-secondary)' }} className="tabular-nums">
                      {item.avg_daily_demand > 0 ? `${item.avg_daily_demand} / day` : '0 (No Sales)'}
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 600 }} className="tabular-nums">
                      {item.coverage_days !== null ? (
                        <span style={{ color: item.coverage_days < 4 ? 'var(--color-critical-red)' : item.coverage_days < 7 ? 'var(--color-warning-amber)' : 'var(--color-dark-green)' }}>
                          {item.coverage_days} Days
                        </span>
                      ) : (
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '12px' }}>Insufficient Data</span>
                      )}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <StatusPill status={item.status} />
                    </td>
                    <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                      {item.status === 'critical' || item.status === 'high' ? (
                        <button
                          onClick={() => onDraftRFQ(item)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: 'var(--color-primary)',
                            color: '#FFFFFF',
                            fontSize: '12px',
                            fontWeight: 600,
                          }}
                        >
                          Draft RFQ
                        </button>
                      ) : (
                        <button
                          onClick={() => onDraftRFQ(item)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: 'var(--color-surface-hover)',
                            border: '1px solid var(--color-border)',
                            color: 'var(--color-text-primary)',
                            fontSize: '12px',
                          }}
                        >
                          Reorder
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
