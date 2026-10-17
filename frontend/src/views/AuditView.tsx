import React from 'react'
import {
  FileText,
  Bot,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Terminal,
  Activity,
  Layers,
} from 'lucide-react'
import { AuditEvent } from '../types'

interface AuditViewProps {
  events: AuditEvent[]
}

export const AuditView: React.FC<AuditViewProps> = ({ events }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Info Banner */}
      <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            padding: '10px',
            backgroundColor: 'var(--color-pale-green)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-dark-green)',
          }}>
            <Activity size={22} />
          </div>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Deterministic Audit Log & Decision Trace</h3>
            <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
              Immutable record of shortage assessments, AI extractions, human approvals, and order dispatches.
            </p>
          </div>
        </div>

        <div style={{
          padding: '6px 12px',
          backgroundColor: 'var(--color-surface-subtle)',
          borderRadius: 'var(--radius-full)',
          fontSize: '12px',
          fontWeight: 600,
          color: 'var(--color-dark-green)',
        }}>
          5 Verified Records Logged
        </div>
      </div>

      {/* Audit Event Timeline */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Chronological Event Stream</h3>
        </div>

        <div style={{ padding: '8px 20px' }}>
          {events.map((evt, idx) => (
            <div
              key={evt.id}
              style={{
                display: 'flex',
                gap: '16px',
                padding: '16px 0',
                borderBottom: idx === events.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
              }}
            >
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  backgroundColor: evt.actor.includes('Pharmacist') ? 'var(--color-pale-green)' : 'var(--color-surface-hover)',
                  color: evt.actor.includes('Pharmacist') ? 'var(--color-dark-green)' : 'var(--color-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  {evt.actor.includes('Pharmacist') ? <ShieldCheck size={15} /> : <Bot size={15} />}
                </div>
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-full)',
                      backgroundColor: 'var(--color-surface-hover)',
                      color: 'var(--color-text-secondary)',
                    }}>
                      {evt.event_type.replace(/_/g, ' ')}
                    </span>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                      {evt.actor}
                    </span>
                  </div>

                  <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                    {new Date(evt.timestamp).toLocaleString()}
                  </span>
                </div>

                <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '6px', lineHeight: '1.5' }}>
                  {evt.description}
                </div>

                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                  Target Entity: <code>{evt.entity_type}</code> ({evt.entity_id})
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
