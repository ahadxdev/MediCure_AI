import React, { useState } from 'react'
import { Settings as SettingsIcon, Shield, Mail, Database, Bell, CheckCircle2 } from 'lucide-react'

interface SettingsViewProps {
  isLiveBackend: boolean
  gmailMode: string
  onToggleBackendMode?: () => void
}

export const SettingsView: React.FC<SettingsViewProps> = ({ isLiveBackend, gmailMode }) => {
  const [reorderThreshold, setReorderThreshold] = useState<number>(4)
  const [dispensaryName, setDispensaryName] = useState('Shifa Central Pharmacy')
  const [dispensaryCity, setDispensaryCity] = useState('Islamabad')
  const [saved, setSaved] = useState(false)

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  return (
    <div style={{ maxWidth: '800px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <form onSubmit={handleSave} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: '12px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Dispensary & Procurement Parameters</h3>
          <p style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
            Configure default shortage risk thresholds and pharmacy branch details
          </p>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
            Dispensary Facility Name
          </label>
          <input
            type="text"
            value={dispensaryName}
            onChange={(e) => setDispensaryName(e.target.value)}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
            Delivery Location / City
          </label>
          <input
            type="text"
            value={dispensaryCity}
            onChange={(e) => setDispensaryCity(e.target.value)}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
            Shortage Risk Critical Threshold (Coverage Days)
          </label>
          <input
            type="number"
            min={1}
            max={14}
            value={reorderThreshold}
            onChange={(e) => setReorderThreshold(Number(e.target.value))}
          />
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
            Medicines with coverage below this threshold will automatically be flagged as Critical on the Shortage Radar.
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '10px' }}>
          <button
            type="submit"
            style={{
              backgroundColor: 'var(--color-primary)',
              color: '#FFFFFF',
              fontWeight: 600,
              padding: '10px 20px',
            }}
          >
            Save Settings
          </button>

          {saved && (
            <span style={{ fontSize: '13px', color: 'var(--color-dark-green)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle2 size={16} /> Preferences Saved Successfully
            </span>
          )}
        </div>
      </form>

      {/* Integration Status Card */}
      <div className="card">
        <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '12px' }}>System Integrations</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', backgroundColor: 'var(--color-surface-subtle)', borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Database size={16} color="var(--color-primary)" />
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>FastAPI Backend Gateway</div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>http://127.0.0.1:8000/api</div>
              </div>
            </div>
            <span style={{ fontSize: '12px', fontWeight: 600, color: isLiveBackend ? 'var(--color-dark-green)' : 'var(--color-warning-amber)' }}>
              {isLiveBackend ? 'Online (Connected)' : 'Demo Fallback'}
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', backgroundColor: 'var(--color-surface-subtle)', borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Mail size={16} color="var(--color-primary)" />
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>Gmail API Integration</div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Simulated / Live OAuth Dispatcher</div>
              </div>
            </div>
            <span style={{
              fontSize: '12px',
              fontWeight: 600,
              color: gmailMode === 'LIVE' ? 'var(--color-dark-green)' : 'var(--color-warning-amber)',
            }}>
              {gmailMode} Mode
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
