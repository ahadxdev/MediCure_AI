import React from 'react'
import {
  AlertTriangle,
  Archive,
  ArrowLeft,
  BarChart3,
  Bell,
  Bot,
  Building2,
  Calculator,
  CheckCircle2,
  FileText,
  HelpCircle,
  Inbox,
  LayoutDashboard,
  Mail,
  Package2,
  Settings,
  ShoppingCart,
  Sparkles,
  Users,
  XCircle,
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
      label: 'WORKSPACE',
      items: [{ id: 'dashboard' as NavigationTab, label: 'Overview', icon: LayoutDashboard }],
    },
    {
      label: 'INVENTORY',
      items: [
        { id: 'inventory' as NavigationTab, label: 'Medicine catalog', icon: Package2 },
        { id: 'shortage_radar' as NavigationTab, label: 'Shortage radar', icon: AlertTriangle, badge: '2' },
      ],
    },
    {
      label: 'PROCUREMENT',
      items: [
        { id: 'suppliers' as NavigationTab, label: 'Suppliers', icon: Building2 },
        { id: 'quote_requests' as NavigationTab, label: 'RFQ drafts', icon: Mail, badge: '1' },
        { id: 'quote_inbox' as NavigationTab, label: 'Quote inbox', icon: Inbox },
        { id: 'simulator' as NavigationTab, label: 'Decision simulator', icon: Calculator },
        { id: 'purchase_orders' as NavigationTab, label: 'Purchase orders', icon: ShoppingCart, badge: '1' },
      ],
    },
    {
      label: 'AUDIT & AI',
      items: [
        { id: 'ai_activity' as NavigationTab, label: 'AI activity', icon: Bot },
        { id: 'audit_trail' as NavigationTab, label: 'Audit trail', icon: FileText },
      ],
    },
  ]

  return (
    <aside className="app-sidebar">
      <div className="brand-lockup">
        <div className="brand-mark" aria-hidden="true">M</div>
        <div>
          <div className="brand-name">Medi<span>Procure</span></div>
          <div className="brand-caption">Pharmacy workspace</div>
        </div>
      </div>

      <div className="workspace-switcher">
        <div className="workspace-switcher-icon"><Archive size={15} /></div>
        <div>
          <span className="workspace-label">Current workspace</span>
          <strong>Shifa Central Pharmacy</strong>
        </div>
        <BarChart3 size={15} className="workspace-chevron" />
      </div>

      <nav className="sidebar-nav" aria-label="Primary navigation">
        <button className="back-link" type="button" onClick={() => onSelectTab('dashboard')}>
          <ArrowLeft size={14} /> Workspace overview
        </button>
        {navSections.map((section) => (
          <div className="nav-section" key={section.label}>
            <div className="nav-section-label">{section.label}</div>
            {section.items.map((item) => {
              const Icon = item.icon
              const isActive = currentTab === item.id
              return (
                <button
                  className={`nav-item${isActive ? ' is-active' : ''}`}
                  key={item.id}
                  type="button"
                  onClick={() => onSelectTab(item.id)}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <span className="nav-item-content"><Icon size={16} strokeWidth={isActive ? 2.2 : 1.8} />{item.label}</span>
                  {item.badge && <span className="nav-badge">{item.badge}</span>}
                </button>
              )
            })}
          </div>
        ))}
        <div className="nav-section nav-section-last">
          <div className="nav-section-label">SYSTEM</div>
          <button className={`nav-item${currentTab === 'settings' ? ' is-active' : ''}`} type="button" onClick={() => onSelectTab('settings')}>
            <span className="nav-item-content"><Settings size={16} />System settings</span>
          </button>
        </div>
      </nav>

      <div className="sidebar-shortcuts">
        <div className="shortcut-card shortcut-card-olive" onClick={() => onSelectTab('shortage_radar')} role="button" tabIndex={0}>
          <div className="shortcut-card-top"><AlertTriangle size={15} /><span>Risk watch</span><ArrowLeft size={13} className="shortcut-arrow" /></div>
          <strong>2 medicines need attention</strong>
          <span>Stock coverage is below lead time</span>
        </div>
        <div className="shortcut-card" onClick={() => onSelectTab('quote_inbox')} role="button" tabIndex={0}>
          <div className="shortcut-card-top"><Inbox size={15} /><span>Quote inbox</span><ArrowLeft size={13} className="shortcut-arrow" /></div>
          <strong>4 supplier offers</strong>
          <span>Ready for comparison</span>
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="connection-row">
          <span className={`connection-dot${isLiveBackend ? ' is-live' : ''}`} />
          {isLiveBackend ? 'Live API connected' : 'Simulated demo mode'}
        </div>
        <div className="sidebar-footer-link"><Bell size={13} /> Notifications</div>
        <div className="sidebar-footer-link"><Users size={13} /> Lead pharmacist account</div>
      </div>
    </aside>
  )
}

interface HeaderProps {
  title: string
  subtitle: string
  actions?: React.ReactNode
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, actions }) => (
  <header className="app-header">
    <div className="header-heading">
      <div className="header-breadcrumb"><Sparkles size={13} /> MediProcure AI <span>/</span> Operations</div>
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
    <div className="header-actions">
      <div className="header-search"><Inbox size={15} /><span>Search workspace</span><kbd>/</kbd></div>
      {actions}
    </div>
  </header>
)

export const StatusPill: React.FC<{ status: ShortageStatus | string; label?: string }> = ({ status, label }) => {
  const getStyle = () => {
    switch (status) {
      case 'critical':
        return { className: 'status-critical', icon: XCircle }
      case 'high':
        return { className: 'status-high', icon: AlertTriangle }
      case 'moderate':
        return { className: 'status-moderate', icon: AlertTriangle }
      case 'low':
      case 'safe':
      case 'approved':
      case 'validated':
        return { className: 'status-safe', icon: CheckCircle2 }
      default:
        return { className: 'status-neutral', icon: HelpCircle }
    }
  }
  const { className, icon: Icon } = getStyle()
  return <span className={`status-pill ${className}`}><Icon size={12} strokeWidth={2.2} />{label || status.replace('_', ' ')}</span>
}
