import React, { useState, useEffect } from 'react'
import { Search, RefreshCw, Plus, Pencil, Trash2 } from 'lucide-react'
import { InventoryItem, MedicineInput } from '../types'
import { StatusPill } from '../components/AppShell'

type CatalogMedicine = {
  name: string
  generic_name: string | null
  category: string | null
  strength: string
  dosage_form: string
  pack_size: string
}

interface InventoryViewProps {
  items: InventoryItem[]
  onRefresh: () => void
  onCreateRFQ: (request: {
    medicine_id: string
    required_quantity: number
    required_by_date: string | null
    delivery_location: string
  }) => Promise<boolean>
  onSaveMedicine: (medicineId: string | null, payload: MedicineInput) => Promise<boolean>
  onDeleteMedicine: (medicineId: string) => Promise<boolean>
  recommendedMedicineId?: string | null
  onRecommendationHandled?: () => void
  isRadarOnly?: boolean
}

export const InventoryView: React.FC<InventoryViewProps> = ({
  items,
  onRefresh,
  onCreateRFQ,
  onSaveMedicine,
  onDeleteMedicine,
  recommendedMedicineId = null,
  onRecommendationHandled,
  isRadarOnly = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [editingMedicine, setEditingMedicine] = useState<InventoryItem | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [catalog, setCatalog] = useState<CatalogMedicine[]>([])
  const [rfqMedicine, setRfqMedicine] = useState<InventoryItem | null>(
    () => items.find((item) => item.medicine_id === recommendedMedicineId) ?? null,
  )
  const [rfqQuantity, setRfqQuantity] = useState(1)
  const [rfqDate, setRfqDate] = useState('')
  const [rfqLocation, setRfqLocation] = useState('Central Pharmacy, Islamabad')
  const [draft, setDraft] = useState<MedicineInput>({
    name: '',
    generic_name: '',
    category: null,
    strength: '',
    dosage_form: '',
    pack_size: '',
    usable_stock: 0,
    reorder_level: 0,
  })

  useEffect(() => {
    const loadCatalog = async () => {
      try {
        const response = await fetch('/api/inventory/catalog')
        if (!response.ok) return
        const data = await response.json()
        if (Array.isArray(data)) setCatalog(data)
      } catch {
        setCatalog([])
      }
    }
    loadCatalog()
  }, [])

  const applySelectedMedicine = (selectedName: string) => {
    const selected = catalog.find((item) => item.name.toLowerCase() === selectedName.toLowerCase())
    if (!selected) return
    setDraft((current) => ({
      ...current,
      name: selected.name,
      generic_name: selected.generic_name ?? current.generic_name,
      category: selected.category ?? current.category,
      strength: selected.strength,
      dosage_form: selected.dosage_form,
      pack_size: selected.pack_size,
    }))
  }

  const openForm = (medicine?: InventoryItem) => {
    setEditingMedicine(medicine || null)
    setDraft(medicine ? {
      name: medicine.name,
      generic_name: medicine.generic_name,
      category: medicine.category,
      strength: medicine.strength,
      dosage_form: medicine.dosage_form,
      pack_size: medicine.pack_size,
      usable_stock: medicine.usable_stock,
      reorder_level: medicine.reorder_level,
    } : {
      name: '',
      generic_name: '',
      category: null,
      strength: '',
      dosage_form: '',
      pack_size: '',
      usable_stock: 0,
      reorder_level: 0,
    })
    setFormOpen(true)
  }

  const saveMedicine = async (event: React.FormEvent) => {
    event.preventDefault()
    const saved = await onSaveMedicine(editingMedicine?.medicine_id || null, draft)
    if (saved) setFormOpen(false)
  }

  const closeRFQ = () => {
    setRfqMedicine(null)
    onRecommendationHandled?.()
  }

  const createRFQ = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!rfqMedicine) return
    const created = await onCreateRFQ({
      medicine_id: rfqMedicine.medicine_id,
      required_quantity: rfqQuantity,
      required_by_date: rfqDate || null,
      delivery_location: rfqLocation,
    })
    if (created) closeRFQ()
  }

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
          {!isRadarOnly && (
            <button
              onClick={() => openForm()}
              style={{ backgroundColor: 'var(--color-primary)', color: '#FFFFFF', fontWeight: 600 }}
            >
              <Plus size={14} />
              Add Medicine
            </button>
          )}
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
                  {isRadarOnly ? 'Action' : 'Catalog Actions'}
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
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px', flexWrap: 'wrap' }}>
                        <button
                          onClick={() => setRfqMedicine(item)}
                          style={{
                            padding: '6px 10px',
                            backgroundColor: item.status === 'critical' || item.status === 'high' ? 'var(--color-primary)' : 'var(--color-surface-hover)',
                            border: item.status === 'critical' || item.status === 'high' ? 'none' : '1px solid var(--color-border)',
                            color: item.status === 'critical' || item.status === 'high' ? '#FFFFFF' : 'var(--color-text-primary)',
                            fontSize: '12px',
                            fontWeight: 600,
                          }}
                        >
                          {item.status === 'critical' || item.status === 'high' ? 'Draft RFQ' : 'Create RFQ'}
                        </button>
                        {!isRadarOnly && (
                          <>
                            <button
                              onClick={() => openForm(item)}
                              aria-label={`Edit ${item.name}`}
                              style={{ padding: '6px 8px', color: 'var(--color-text-secondary)' }}
                            >
                              <Pencil size={14} />
                            </button>
                            <button
                              onClick={async () => {
                                if (window.confirm(`Delete ${item.name}? Medicines linked to sales or quotation history cannot be deleted.`)) {
                                  await onDeleteMedicine(item.medicine_id)
                                }
                              }}
                              aria-label={`Delete ${item.name}`}
                              style={{ padding: '6px 8px', color: 'var(--color-critical-red)' }}
                            >
                              <Trash2 size={14} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {formOpen && (
          <div
            role="presentation"
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) setFormOpen(false)
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
              aria-labelledby="medicine-form-title"
              onSubmit={saveMedicine}
              className="card"
              style={{ width: 'min(620px, 100%)', display: 'flex', flexDirection: 'column', gap: '14px' }}
            >
              <h3 id="medicine-form-title">{editingMedicine ? 'Edit Medicine' : 'Add Medicine'}</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
                <label style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px', fontWeight: 600 }}>
                  Select medicine
                  <select
                    value={draft.name}
                    onChange={(event) => {
                      const selectedName = event.target.value
                      setDraft({ ...draft, name: selectedName })
                      if (selectedName) applySelectedMedicine(selectedName)
                    }}
                  >
                    <option value="">Manual entry</option>
                    {catalog.map((item) => (
                      <option key={item.name} value={item.name}>{item.name}</option>
                    ))}
                  </select>
                </label>
                <label style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px', fontWeight: 600 }}>
                  Category
                  <input
                    type="text"
                    value={draft.category || ''}
                    onChange={(event) => setDraft({ ...draft, category: event.target.value || null })}
                  />
                </label>
                {([
                  ['generic_name', 'Generic name', 'text'],
                  ['strength', 'Strength', 'text'],
                  ['dosage_form', 'Dosage form', 'text'],
                  ['pack_size', 'Pack size', 'text'],
                ] as const).map(([field, label, type]) => (
                  <label key={field} style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px', fontWeight: 600 }}>
                    {label}
                    <input
                      type={type}
                      required={field !== 'generic_name'}
                      value={draft[field] || ''}
                      onChange={(event) => setDraft({ ...draft, [field]: event.target.value || (field === 'generic_name' ? null : '') })}
                    />
                  </label>
                ))}
                {([
                  ['usable_stock', 'Usable stock'],
                  ['reorder_level', 'Reorder level'],
                ] as const).map(([field, label]) => (
                  <label key={field} style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px', fontWeight: 600 }}>
                    {label}
                    <input
                      type="number"
                      min="0"
                      step="any"
                      required
                      value={draft[field]}
                      onChange={(event) => setDraft({ ...draft, [field]: Number(event.target.value) })}
                    />
                  </label>
                ))}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button type="button" onClick={() => setFormOpen(false)}>Cancel</button>
                <button type="submit" style={{ backgroundColor: 'var(--color-primary)', color: '#FFFFFF', fontWeight: 600 }}>
                  {editingMedicine ? 'Save Changes' : 'Create Medicine'}
                </button>
              </div>
            </form>
          </div>
        )}
        {rfqMedicine && (
          <div
            role="presentation"
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) closeRFQ()
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
              aria-labelledby="rfq-form-title"
              onSubmit={createRFQ}
              className="card"
              style={{ width: 'min(540px, 100%)', display: 'flex', flexDirection: 'column', gap: '14px' }}
            >
              <h3 id="rfq-form-title">Draft RFQ: {rfqMedicine.name}</h3>
              <p style={{ fontSize: '12px' }}>Creating the draft does not send email. You will review the recipients and draft before approval.</p>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px', fontWeight: 600 }}>
                Required quantity (packs)
                <input
                  type="number"
                  min="1"
                  step="any"
                  required
                  value={rfqQuantity}
                  onChange={(event) => setRfqQuantity(Number(event.target.value))}
                />
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px', fontWeight: 600 }}>
                Required by date
                <input type="date" value={rfqDate} onChange={(event) => setRfqDate(event.target.value)} />
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px', fontWeight: 600 }}>
                Delivery location
                <input required value={rfqLocation} onChange={(event) => setRfqLocation(event.target.value)} />
              </label>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button type="button" onClick={closeRFQ}>Cancel</button>
                <button type="submit" style={{ backgroundColor: 'var(--color-primary)', color: '#FFFFFF', fontWeight: 600 }}>
                  Create RFQ Draft
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  )
}
