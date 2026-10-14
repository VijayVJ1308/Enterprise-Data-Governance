import React, { useState, useEffect } from 'react';
import { Shield, Search, RefreshCw, Bell, User, CheckCircle2, AlertCircle } from 'lucide-react';
import { apiService } from '../../services/api';

interface NavbarProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  searchTerm,
  onSearchChange,
  onRefresh,
  isRefreshing = false,
}) => {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'offline'>('checking');

  useEffect(() => {
    let mounted = true;
    apiService.getHealth()
      .then((res) => {
        if (mounted) {
          if (res.status === 'healthy') setBackendStatus('connected');
          else setBackendStatus('offline');
        }
      })
      .catch(() => {
        if (mounted) setBackendStatus('offline');
      });
    return () => { mounted = false; };
  }, []);

  return (
    <header className="navbar" id="app-navbar">
      <div className="navbar-brand">
        <div className="brand-icon-wrapper">
          <Shield size={22} />
        </div>
        <div>
          <div className="brand-title">AegisData</div>
          <div className="brand-subtitle">Governance Lakehouse</div>
        </div>
      </div>

      <div className="navbar-center">
        <div className="search-input-wrapper">
          <Search size={16} />
          <input
            id="global-search-input"
            type="text"
            className="search-input"
            placeholder="Search datasets, schema columns, rules, contracts, glossary..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>
      </div>

      <div className="navbar-actions">
        <div
          id="backend-status-pill"
          className="status-indicator"
          style={{
            borderColor: backendStatus === 'connected' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(56, 189, 248, 0.3)',
            backgroundColor: backendStatus === 'connected' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(56, 189, 248, 0.1)',
            color: backendStatus === 'connected' ? '#10b981' : '#38bdf8',
          }}
          title={backendStatus === 'connected' ? 'Connected to FastAPI REST Core' : 'Operating in High-Resilience Standalone Demo Mode'}
        >
          {backendStatus === 'connected' ? (
            <>
              <span className="status-dot" style={{ backgroundColor: '#10b981' }} />
              <span>API Live (v1.0.0)</span>
            </>
          ) : (
            <>
              <span className="status-dot" style={{ backgroundColor: '#38bdf8' }} />
              <span>Offline / Demo Ready</span>
            </>
          )}
        </div>

        <button
          id="btn-refresh-telemetry"
          className="btn btn-secondary btn-sm"
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Reload fresh governance metrics"
        >
          <RefreshCw size={14} className={isRefreshing ? 'spin-anim' : ''} />
          <span>Refresh</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderLeft: '1px solid var(--border-subtle)', paddingLeft: '1rem' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: '0.8rem',
              fontWeight: 700,
            }}
          >
            AD
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f8fafc' }}>Lead Steward</span>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>Enterprise Admin</span>
          </div>
        </div>
      </div>
    </header>
  );
};
