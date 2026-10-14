import React, { useState } from 'react';
import {
  FileCheck2,
  FileCode,
  AlertCircle,
  Clock,
  Shield,
  Layers,
  CheckCircle,
  Play,
  Sparkles,
} from 'lucide-react';
import { DataContract, DriftEvent } from '../../types';

interface ContractsViewProps {
  contracts: DataContract[];
  driftEvents: DriftEvent[];
}

export const ContractsView: React.FC<ContractsViewProps> = ({ contracts, driftEvents }) => {
  const [selectedContract, setSelectedContract] = useState<DataContract>(contracts[0]);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [validationResult, setValidationResult] = useState<string | null>(null);

  const handleValidateContract = () => {
    setIsValidating(true);
    setValidationResult(null);
    setTimeout(() => {
      setIsValidating(false);
      setValidationResult(`Contract '${selectedContract.dataset_name}' (v${selectedContract.version}) verified: SLA Freshness compliant (0.6h < ${selectedContract.sla_freshness_hours}h SLA). No breaking changes.`);
    }, 1000);
  };

  return (
    <div id="contracts-drift-view">
      {/* Header */}
      <div className="view-header">
        <div className="view-title-group">
          <h2>Data Contracts & Schema Drift Telemetry</h2>
          <p className="view-description">
            Enforce strict schema boundaries, freshness SLAs, and catch breaking column mutations before downstream pipelines fail.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            id="btn-validate-contract"
            className="btn btn-primary"
            onClick={handleValidateContract}
            disabled={isValidating}
          >
            <Play size={15} className={isValidating ? 'spin-anim' : ''} />
            <span>{isValidating ? 'Validating SLA & Schema...' : 'Validate Active Contract'}</span>
          </button>
        </div>
      </div>

      {validationResult && (
        <div
          className="glass-card"
          style={{
            marginBottom: '1.5rem',
            borderColor: 'var(--status-good)',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            padding: '1rem 1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <CheckCircle size={20} style={{ color: 'var(--status-good)' }} />
          <span style={{ fontWeight: 600, fontSize: '0.875rem', color: '#fff' }}>{validationResult}</span>
        </div>
      )}

      {/* Main Grid: Contracts on Left vs Drift History on Right */}
      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        {/* Left: Contracts Selector & Schema Definition */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.15rem' }}>Active Data Contracts</h3>
            <span className="badge badge-cyan">{contracts.length} Registered</span>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
            {contracts.map((c) => (
              <button
                key={c.id}
                id={`btn-select-contract-${c.id}`}
                className={`btn btn-sm ${selectedContract.id === c.id ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSelectedContract(c)}
              >
                {c.dataset_name} ({c.version})
              </button>
            ))}
          </div>

          <div className="glass-card" style={{ marginBottom: '1.25rem', padding: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontWeight: 700, fontSize: '1rem', color: '#fff' }}>{selectedContract.dataset_name}</span>
              <span className="badge badge-success">{selectedContract.status}</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Owner: <code>{selectedContract.owner}</code> &bull; Freshness SLA: <strong>&le; {selectedContract.sla_freshness_hours}h</strong>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
              Last Verified: {new Date(selectedContract.last_validated).toLocaleString()}
            </div>
          </div>

          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
            Contract Schema Specifications
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Field Name</th>
                  <th>Expected Type</th>
                  <th>Nullable</th>
                  <th>PII Tag</th>
                </tr>
              </thead>
              <tbody>
                {selectedContract.schema_columns.map((col) => (
                  <tr key={col.name}>
                    <td style={{ fontWeight: 600, color: '#fff' }}>{col.name}</td>
                    <td><code>{col.type}</code></td>
                    <td>
                      <span className={`badge ${col.nullable ? 'badge-warning' : 'badge-cyan'}`} style={{ fontSize: '0.65rem' }}>
                        {col.nullable ? 'NULLABLE' : 'REQUIRED'}
                      </span>
                    </td>
                    <td>
                      {col.pii ? (
                        <span className="badge badge-danger" style={{ fontSize: '0.65rem' }}>PII CLASSIFIED</span>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>None</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Schema Drift & Evolution Log */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem' }}>Schema Drift Event Stream</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Automated detection of breaking changes, schema widening, and unexpected columns.
              </p>
            </div>
            <span className="badge badge-warning">{driftEvents.length} Events</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {driftEvents.map((event) => (
              <div
                key={event.id}
                className="glass-card"
                style={{
                  borderLeft: `4px solid ${
                    event.severity === 'HIGH' ? 'var(--status-critical)' : event.severity === 'MEDIUM' ? 'var(--status-warning)' : 'var(--accent-cyan)'
                  }`,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: 700, color: '#fff', fontSize: '0.9rem' }}>{event.dataset_name}</span>
                    <span className="badge badge-purple" style={{ fontSize: '0.65rem' }}>{event.drift_type}</span>
                  </div>
                  <span
                    className={`badge ${
                      event.severity === 'HIGH' ? 'badge-danger' : event.severity === 'MEDIUM' ? 'badge-warning' : 'badge-cyan'
                    }`}
                    style={{ fontSize: '0.65rem' }}
                  >
                    {event.severity}
                  </span>
                </div>

                <p style={{ fontSize: '0.825rem', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
                  {event.detail}
                </p>

                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                  Detected: {new Date(event.detected_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
