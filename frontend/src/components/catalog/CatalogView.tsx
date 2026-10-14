import React, { useState } from 'react';
import {
  Database,
  Search,
  Filter,
  Shield,
  Layers,
  ChevronRight,
  Eye,
  CheckCircle,
  AlertCircle,
  Lock,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { Dataset, ColumnProfile, DomainType, SensitivityLevel } from '../../types';

interface CatalogViewProps {
  datasets: Dataset[];
  searchTerm: string;
}

export const CatalogView: React.FC<CatalogViewProps> = ({ datasets, searchTerm }) => {
  const [selectedDomain, setSelectedDomain] = useState<string>('ALL');
  const [selectedSensitivity, setSelectedSensitivity] = useState<string>('ALL');
  const [activeDataset, setActiveDataset] = useState<Dataset | null>(datasets[0] || null);
  const [isProfiling, setIsProfiling] = useState<boolean>(false);

  // Filter datasets
  const filteredDatasets = datasets.filter((d) => {
    const matchesSearch =
      d.dataset_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.domain.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDomain = selectedDomain === 'ALL' || d.domain === selectedDomain;
    const matchesSensitivity = selectedSensitivity === 'ALL' || d.sensitivity === selectedSensitivity;
    return matchesSearch && matchesDomain && matchesSensitivity;
  });

  const handleTriggerProfiling = () => {
    setIsProfiling(true);
    setTimeout(() => {
      setIsProfiling(false);
    }, 1200);
  };

  return (
    <div id="catalog-view">
      {/* Header */}
      <div className="view-header">
        <div className="view-title-group">
          <h2>Enterprise Metadata Catalog & Profiler</h2>
          <p className="view-description">
            Unified data assets registry, column statistics, sensitivity classifications, and automated schema contracts.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            id="btn-reprofile-dataset"
            className="btn btn-primary"
            onClick={handleTriggerProfiling}
            disabled={isProfiling}
          >
            <RefreshCw size={16} className={isProfiling ? 'spin-anim' : ''} />
            <span>{isProfiling ? 'Profiling Lakehouse...' : 'Run Automated Profiler'}</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', display: 'flex', gap: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          <Filter size={16} /> Filter By:
        </div>

        {/* Domain Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>Domain:</span>
          {(['ALL', 'CRM', 'ERP', 'HR', 'ECOMMERCE'] as const).map((dm) => (
            <button
              key={dm}
              id={`filter-domain-${dm}`}
              className={`btn btn-sm ${selectedDomain === dm ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setSelectedDomain(dm)}
            >
              {dm}
            </button>
          ))}
        </div>

        {/* Sensitivity Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>Sensitivity:</span>
          {(['ALL', 'RESTRICTED', 'CONFIDENTIAL', 'INTERNAL'] as const).map((lvl) => (
            <button
              key={lvl}
              id={`filter-sens-${lvl}`}
              className={`btn btn-sm ${selectedSensitivity === lvl ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setSelectedSensitivity(lvl)}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Main 2-Column Split: Dataset Catalog List vs Column Profile Drawer */}
      <div className="grid-2">
        {/* Left Column: Dataset Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase' }}>
            Registered Assets ({filteredDatasets.length})
          </div>

          {filteredDatasets.map((ds) => {
            const isSelected = activeDataset?.id === ds.id;
            return (
              <div
                key={ds.id}
                id={`dataset-card-${ds.id}`}
                className="glass-card"
                onClick={() => setActiveDataset(ds)}
                style={{
                  cursor: 'pointer',
                  borderColor: isSelected ? 'var(--accent-cyan)' : undefined,
                  boxShadow: isSelected ? 'var(--glow-cyan)' : undefined,
                  background: isSelected ? 'rgba(30, 41, 59, 0.9)' : undefined,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Database size={18} style={{ color: 'var(--accent-cyan)' }} />
                    <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>{ds.dataset_name}</span>
                  </div>
                  <span
                    className={`badge ${
                      ds.sensitivity === 'RESTRICTED'
                        ? 'badge-danger'
                        : ds.sensitivity === 'CONFIDENTIAL'
                        ? 'badge-warning'
                        : 'badge-cyan'
                    }`}
                  >
                    {ds.sensitivity}
                  </span>
                </div>

                <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '0.85rem' }}>
                  {ds.description}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-dim)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.65rem' }}>
                  <span>Domain: <strong style={{ color: 'var(--text-main)' }}>{ds.domain}</strong></span>
                  <span>Owner: <strong style={{ color: 'var(--text-main)' }}>{ds.owner_team}</strong></span>
                  <span>Rows: <strong style={{ color: 'var(--text-main)' }}>{(ds.row_count || 0).toLocaleString()}</strong></span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent-cyan)', fontWeight: 600 }}>
                    <span>Inspect</span>
                    <ChevronRight size={14} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Column: Column Profile & PII Deep Dive */}
        <div>
          {activeDataset ? (
            <div className="glass-panel" style={{ padding: '1.5rem', position: 'sticky', top: '80px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <h3 style={{ fontSize: '1.25rem' }}>{activeDataset.dataset_name}</h3>
                    <span className="badge badge-cyan">{activeDataset.domain}</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                    Schema Profile &bull; {activeDataset.columns ? activeDataset.columns.length : activeDataset.column_count} Columns &bull;{' '}
                    {(activeDataset.row_count || 0).toLocaleString()} rows
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--status-good)' }}>
                    {activeDataset.quality_score}%
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Asset Health</div>
                </div>
              </div>

              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Column Profiles & PII Classification
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '550px', overflowY: 'auto', paddingRight: '0.35rem' }}>
                {activeDataset.columns && activeDataset.columns.length > 0 ? (
                  activeDataset.columns.map((col) => (
                    <div
                      key={col.column_name}
                      className="glass-card"
                      style={{
                        padding: '0.85rem',
                        borderLeft: col.pii_detected ? '3px solid var(--accent-rose)' : '3px solid var(--border-medium)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: 600, fontSize: '0.9rem', color: '#fff' }}>{col.column_name}</span>
                          <code style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>{col.data_type}</code>
                        </div>
                        {col.pii_detected && (
                          <span className="badge badge-danger" style={{ fontSize: '0.65rem' }}>
                            <Lock size={10} /> PII: {col.pii_type}
                          </span>
                        )}
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.5rem' }}>
                        <div>
                          Nulls:{' '}
                          <span style={{ color: col.null_percentage > 0 ? 'var(--status-warning)' : 'var(--text-main)', fontWeight: 600 }}>
                            {col.null_count} ({col.null_percentage}%)
                          </span>
                        </div>
                        <div>
                          Distinct:{' '}
                          <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>
                            {col.distinct_count.toLocaleString()}
                          </span>
                        </div>
                        <div>
                          Uniqueness:{' '}
                          <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>
                            {col.unique_percentage}%
                          </span>
                        </div>
                      </div>

                      {col.mean !== undefined && (
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.35rem', borderTop: '1px dashed var(--border-subtle)', paddingTop: '0.35rem' }}>
                          Stats: Min: {col.min_value} &bull; Max: {col.max_value} &bull; Mean: {col.mean}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-dim)' }}>
                    No column profile snapshot available yet. Click "Run Automated Profiler" above.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-dim)' }}>
              Select a dataset from the left to view detailed column statistics and PII classifications.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
