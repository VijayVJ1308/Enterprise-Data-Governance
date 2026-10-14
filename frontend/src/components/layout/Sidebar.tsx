import React from 'react';
import {
  LayoutDashboard,
  Database,
  CheckCircle,
  GitBranch,
  FileCheck2,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';

export type NavView = 'executive' | 'catalog' | 'quality' | 'lineage' | 'contracts' | 'governance' | 'ml';

interface SidebarProps {
  currentView: NavView;
  onSelectView: (view: NavView) => void;
  activeIssueCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onSelectView,
  activeIssueCount = 3,
}) => {
  const navItems = [
    {
      id: 'executive' as NavView,
      label: 'Executive Health',
      icon: LayoutDashboard,
      badge: null,
    },
    {
      id: 'catalog' as NavView,
      label: 'Data Catalog',
      icon: Database,
      badge: '4 Sets',
    },
    {
      id: 'quality' as NavView,
      label: 'Quality & Issues',
      icon: CheckCircle,
      badge: activeIssueCount > 0 ? `${activeIssueCount} Open` : null,
      badgeClass: 'badge-danger',
    },
    {
      id: 'lineage' as NavView,
      label: 'Lineage Graph',
      icon: GitBranch,
      badge: 'DAG',
    },
    {
      id: 'contracts' as NavView,
      label: 'Contracts & Drift',
      icon: FileCheck2,
      badge: 'v1.4',
    },
    {
      id: 'governance' as NavView,
      label: 'Governance & PII',
      icon: ShieldAlert,
      badge: 'GDPR',
    },
    {
      id: 'ml' as NavView,
      label: 'ML Observability',
      icon: Sparkles,
      badge: 'AI Recs',
      badgeClass: 'badge-purple',
    },
  ];

  return (
    <aside className="sidebar" id="app-sidebar">
      <div style={{ padding: '0.25rem 0.5rem 0.75rem', fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-dim)', letterSpacing: '0.08em', fontWeight: 700 }}>
        Platform Modules
      </div>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              id={`nav-${item.id}`}
              className={`nav-link ${isActive ? 'active' : ''}`}
              onClick={() => onSelectView(item.id)}
              style={{
                width: '100%',
                justifyContent: 'flex-start',
                background: isActive ? undefined : 'transparent',
                textAlign: 'left',
              }}
            >
              <Icon size={18} />
              <span className="nav-label" style={{ flex: 1 }}>{item.label}</span>
              {item.badge && (
                <span className={`badge ${item.badgeClass || 'badge-cyan'}`} style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div style={{ marginTop: 'auto', paddingTop: '1.5rem', borderTop: '1px solid var(--border-subtle)' }}>
        <div className="glass-card" style={{ padding: '0.85rem' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.35rem' }}>
            Medallion Engine
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 600 }}>
            <span>Lake Pipeline</span>
            <span style={{ color: 'var(--accent-emerald)' }}>HEALTHY</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Bronze ➔ Silver ➔ Gold
          </div>
        </div>
      </div>
    </aside>
  );
};
