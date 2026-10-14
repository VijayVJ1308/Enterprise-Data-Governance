import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  Lock,
  Key,
  EyeOff,
  FileText,
  CheckCircle,
  AlertTriangle,
  Layers,
  Sparkles,
} from 'lucide-react';
import { ComplianceControl } from '../../types';
import { apiService } from '../../services/api';

interface GovernanceViewProps {
  complianceControls: ComplianceControl[];
}

export const GovernanceView: React.FC<GovernanceViewProps> = ({ complianceControls }) => {
  const [selectedFramework, setSelectedFramework] = useState<string>('ALL');
  const [sandboxInput, setSandboxInput] = useState<string>('alex.mercer@enterprise-corp.com');
  const [sandboxType, setSandboxType] = useState<'EMAIL' | 'PHONE' | 'SSN' | 'IBAN'>('EMAIL');
  const [maskedOutput, setMaskedOutput] = useState<string>(
    apiService.maskText('alex.mercer@enterprise-corp.com', 'EMAIL')
  );

  const frameworks = ['ALL', 'GDPR', 'HIPAA', 'SOC2', 'ISO27001'] as const;

  const filteredControls = complianceControls.filter(
    (c) => selectedFramework === 'ALL' || c.framework === selectedFramework
  );

  const handleMask = (input: string, type: 'EMAIL' | 'PHONE' | 'SSN' | 'IBAN') => {
    setSandboxInput(input);
    setSandboxType(type);
    setMaskedOutput(apiService.maskText(input, type));
  };

  return (
    <div id="governance-compliance-view">
      {/* Header */}
      <div className="view-header">
        <div className="view-title-group">
          <h2>Data Governance, Compliance & Cryptographic Masking</h2>
          <p className="view-description">
            Regulatory alignment across GDPR, HIPAA, SOC 2, and ISO 27001 with field-level obfuscation and immutable audit logs.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <span className="badge badge-success" style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}>
            <ShieldCheck size={14} /> 94.4% Compliance Index
          </span>
        </div>
      </div>

      {/* Real-time PII Masking Sandbox */}
      <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <Lock size={18} style={{ color: 'var(--accent-cyan)' }} />
          <h3 style={{ fontSize: '1.15rem' }}>Interactive PII Masking & Tokenization Sandbox</h3>
        </div>
        <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          Test deterministic field-level masking rules utilized across PySpark and Trino query federation.
        </p>

        <div className="grid-2" style={{ gap: '1.5rem' }}>
          {/* Input side */}
          <div>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <button
                id="btn-sample-email"
                className={`btn btn-sm ${sandboxType === 'EMAIL' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleMask('alex.mercer@enterprise-corp.com', 'EMAIL')}
              >
                Sample Email
              </button>
              <button
                id="btn-sample-phone"
                className={`btn btn-sm ${sandboxType === 'PHONE' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleMask('+1-415-555-0199', 'PHONE')}
              >
                Sample Phone
              </button>
              <button
                id="btn-sample-ssn"
                className={`btn btn-sm ${sandboxType === 'SSN' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleMask('987-65-4321', 'SSN')}
              >
                Sample SSN
              </button>
              <button
                id="btn-sample-iban"
                className={`btn btn-sm ${sandboxType === 'IBAN' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleMask('GB29NWBK60161331926819', 'IBAN')}
              >
                Sample IBAN
              </button>
            </div>

            <div style={{ marginBottom: '0.5rem', fontSize: '0.78rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>
              Raw Confidential Input
            </div>
            <input
              id="sandbox-pii-input"
              type="text"
              className="search-input"
              style={{ paddingLeft: '1rem' }}
              value={sandboxInput}
              onChange={(e) => {
                setSandboxInput(e.target.value);
                setMaskedOutput(apiService.maskText(e.target.value, sandboxType));
              }}
            />
          </div>

          {/* Masked Output side */}
          <div>
            <div style={{ marginBottom: '0.5rem', fontSize: '0.78rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>
              Obfuscated Production Representation
            </div>
            <div
              id="sandbox-pii-output"
              className="glass-card"
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '1rem',
                color: 'var(--accent-emerald)',
                border: '1px solid var(--accent-emerald)',
                background: 'rgba(16, 185, 129, 0.08)',
                padding: '0.75rem 1rem',
                minHeight: '44px',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              {maskedOutput || '---'}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.4rem' }}>
              Algorithm: SHA-256 HMAC Salted Prefix Redaction &bull; Zero Reversibility Guarantee
            </div>
          </div>
        </div>
      </div>

      {/* Regulatory Compliance Matrix */}
      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem' }}>Regulatory Compliance Controls Matrix</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Continuous automated posture validation against enterprise data standards.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.35rem' }}>
            {frameworks.map((fw) => (
              <button
                key={fw}
                id={`filter-fw-${fw}`}
                className={`btn btn-sm ${selectedFramework === fw ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSelectedFramework(fw)}
              >
                {fw}
              </button>
            ))}
          </div>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Framework</th>
                <th>Control ID</th>
                <th>Control Requirement</th>
                <th>Status</th>
                <th>Covered Assets</th>
              </tr>
            </thead>
            <tbody>
              {filteredControls.map((ctrl) => (
                <tr key={`${ctrl.framework}-${ctrl.control_id}`}>
                  <td>
                    <span className="badge badge-purple" style={{ fontWeight: 700 }}>
                      {ctrl.framework}
                    </span>
                  </td>
                  <td>
                    <code style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{ctrl.control_id}</code>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, color: '#fff' }}>{ctrl.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{ctrl.description}</div>
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        ctrl.status === 'COMPLIANT'
                          ? 'badge-success'
                          : ctrl.status === 'NEEDS_REVIEW'
                          ? 'badge-warning'
                          : 'badge-danger'
                      }`}
                    >
                      {ctrl.status}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    {ctrl.affected_assets_count} tables
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
