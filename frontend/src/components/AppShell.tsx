import React from 'react'
import {
  LayoutDashboard,
  Package2,
  AlertTriangle,
  Building2,
  Mail,
  Inbox,
  Calculator,
  ShoppingCart,
  Bot,
  FileText,
  Settings,
  CheckCircle2,
  XCircle,
  HelpCircle,
} from 'lucide-react'
import { ShortageStatus } from '../types'

export type NavigationTab =
  | 'dashboard'
  | 'inventory'
  | 'shortage_radar'
  | 'suppliers'
  | 'quote_requests'
  | 'quote_inbox'
  | 'simulator'
  | 'purchase_orders'
  | 'ai_activity'
  | 'audit_trail'
  | 'settings'

interface SidebarProps {
  currentTab: NavigationTab
  onSelectTab: (tab: NavigationTab) => void
  isLiveBackend: boolean
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, isLiveBackend }) => {
  const navSections = [
    {
      label: 'OVERVIEW',
      items: [
        { id: 'dashboard' as NavigationTab, label: 'Dashboard', icon: LayoutDashboard },
      ],
    },
    {
      label: 'INVENTORY',
      items: [
        { id: 'inventory' as NavigationTab, label: 'Inventory Catalog', icon: Package2 },
        { id: 'shortage_radar' as NavigationTab, label: 'Shortage Radar', icon: AlertTriangle, badge: '2 Critical' },
      ],
    },
    {
      label: 'PROCUREMENT',
      items: [
        { id: 'suppliers' as NavigationTab, label: 'Suppliers', icon: Building2 },
        { id: 'quote_requests' as NavigationTab, label: 'Quote Requests (RFQ)', icon: Mail, badge: '1 Approval' },
        { id: 'quote_inbox' as NavigationTab, label: 'Quote Inbox', icon: Inbox },
        { id: 'simulator' as NavigationTab, label: 'Procurement Simulator', icon: Calculator },
        { id: 'purchase_orders' as NavigationTab, label: 'Purchase Orders', icon: ShoppingCart, badge: '1 Draft' },
      ],
    },
    {
      label: 'OPERATIONS',
      items: [
        { id: 'ai_activity' as NavigationTab, label: 'AI Activity & Logs', icon: Bot },
        { id: 'audit_trail' as NavigationTab, label: 'Audit Trail', icon: FileText },
      ],
    },
    {
      label: 'SYSTEM',
      items: [
        { id: 'settings' as NavigationTab, label: 'System Settings', icon: Settings },
      ],
    },
  ]

  return (
    <aside style={{
      width: '260px',
      backgroundColor: '#FFFFFF',
      borderRight: '1px solid var(--color-border)',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      userSelect: 'none',
      minHeight: '100vh',
    }}>
      {/* Brand Header */}
      <div style={{
        padding: '24px 20px 20px',
        borderBottom: '1px solid var(--color-border-subtle)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          backgroundColor: 'var(--color-primary)',
          color: '#FFFFFF',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 700,
          fontSize: '18px',
          boxShadow: '0 2px 6px rgba(85, 184, 63, 0.35)',
        }}>
          M
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '16px', letterSpacing: '-0.02em', color: 'var(--color-text-primary)' }}>
            MediProcure <span style={{ color: 'var(--color-primary)' }}>AI</span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 500 }}>
            Predict. Protect. Procure.
          </div>
        </div>
      </div>

      {/* Navigation List */}
      <nav style={{ flex: 1, padding: '16px 12px', overflowY: 'auto' }}>
        {navSections.map((sec, i) => (
          <div key={i} style={{ marginBottom: '20px' }}>
            <div style={{
              fontSize: '10px',
              fontWeight: 700,
              color: 'var(--color-text-muted)',
              padding: '4px 12px 8px',
              letterSpacing: '0.06em',
            }}>
              {sec.label}
            </div>
            {sec.items.map((item) => {
              const Icon = item.icon
              const isActive = currentTab === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-md)',
                    border: 'none',
                    backgroundColor: isActive ? 'var(--color-pale-green)' : 'transparent',
                    color: isActive ? 'var(--color-dark-green)' : 'var(--color-text-secondary)',
                    fontWeight: isActive ? 600 : 500,
                    marginBottom: '2px',
                    transition: 'all 0.15s ease',
                    textAlign: 'left',
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = 'var(--color-surface-hover)'
                      e.currentTarget.style.color = 'var(--color-text-primary)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = 'transparent'
                      e.currentTarget.style.color = 'var(--color-text-secondary)'
                    }
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Icon size={17} color={isActive ? 'var(--color-primary)' : 'currentColor'} strokeWidth={isActive ? 2.2 : 1.8} />
                    <span style={{ fontSize: '13px' }}>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      borderRadius: 'var(--radius-full)',
                      backgroundColor: isActive ? 'rgba(85, 184, 63, 0.2)' : 'var(--color-surface-hover)',
                      color: isActive ? 'var(--color-dark-green)' : 'var(--color-text-secondary)',
                      fontWeight: 600,
                    }}>
                      {item.badge}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Backend & Environment Status Footer */}
      <div style={{
        padding: '16px',
        borderTop: '1px solid var(--color-border-subtle)',
        backgroundColor: 'var(--color-surface-subtle)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isLiveBackend ? 'var(--color-primary)' : 'var(--color-warning-amber)',
            display: 'inline-block',
          }} />
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {isLiveBackend ? 'Live API Connected' : 'Simulated Demo Mode'}
          </span>
        </div>
        <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', lineHeight: '1.4' }}>
          Dispensary: Shifa Central Pharmacy, Islamabad
        </div>
      </div>
    </aside>
  )
}

interface HeaderProps {
  title: string
  subtitle: string
  actions?: React.ReactNode
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, actions }) => {
  return (
    <header style={{
      padding: '20px 36px',
      backgroundColor: '#FFFFFF',
      borderBottom: '1px solid var(--color-border)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '16px',
    }}>
      <div>
        <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
          {title}
        </h1>
        <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
          {subtitle}
        </p>
      </div>
      {actions && <div>{actions}</div>}
    </header>
  )
}

export const StatusPill: React.FC<{ status: ShortageStatus | string; label?: string }> = ({ status, label }) => {
  const getStyle = () => {
    switch (status) {
      case 'critical':
        return { bg: 'var(--color-critical-bg)', text: 'var(--color-critical-red)', icon: XCircle }
      case 'high':
        return { bg: 'var(--color-warning-bg)', text: 'var(--color-warning-amber)', icon: AlertTriangle }
      case 'moderate':
        return { bg: '#FEFCE8', text: '#A16207', icon: AlertTriangle }
      case 'low':
      case 'safe':
      case 'approved':
      case 'validated':
        return { bg: 'var(--color-soft-green)', text: 'var(--color-dark-green)', icon: CheckCircle2 }
      case 'unknown':
      default:
        return { bg: 'var(--color-surface-hover)', text: 'var(--color-text-secondary)', icon: HelpCircle }
    }
  }

  const { bg, text, icon: Icon } = getStyle()
  const displayLabel = label || status.replace('_', ' ')

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '5px',
      padding: '3px 8px',
      borderRadius: 'var(--radius-full)',
      fontSize: '11px',
      fontWeight: 600,
      backgroundColor: bg,
      color: text,
      textTransform: 'capitalize',
    }}>
      <Icon size={12} strokeWidth={2.2} />
      {displayLabel}
    </span>
  )
}
