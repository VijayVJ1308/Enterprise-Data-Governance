import React from 'react';
import {
  Activity,
  ShieldCheck,
  AlertTriangle,
  Database,
  ArrowUpRight,
  TrendingUp,
  Clock,
  Sparkles,
  Layers,
  CheckCircle2,
} from 'lucide-react';
import { QualitySummary, Dataset, QualityIssue } from '../../types';

interface ExecutiveViewProps {
  summary: QualitySummary;
  datasets: Dataset[];
  issues: QualityIssue[];
  onNavigate: (view: 'catalog' | 'quality' | 'contracts' | 'governance') => void;
}

export const ExecutiveView: React.FC<ExecutiveViewProps> = ({
  summary,
  datasets,
  issues,
  onNavigate,
}) => {
  const openIssues = issues.filter((i) => i.status !== 'RESOLVED');
  const criticalCount = issues.filter((i) => i.severity === 'CRITICAL' && i.status !== 'RESOLVED').length;

  const dimensionList: { key: keyof typeof summary.dimensions; name: string; color: string }[] = [
    { key: 'completeness', name: 'Completeness', color: 'var(--accent-cyan)' },
    { key: 'validity', name: 'Validity', color: 'var(--accent-blue)' },
    { key: 'uniqueness', name: 'Uniqueness', color: 'var(--accent-purple)' },
    { key: 'consistency', name: 'Consistency', color: 'var(--accent-emerald)' },
    { key: 'accuracy', name: 'Accuracy', color: 'var(--accent-amber)' },
    { key: 'freshness', name: 'Freshness SLA', color: 'var(--accent-rose)' },
  ];

  return (
    <div id="executive-dashboard-view">
      {/* Header */}
      <div className="view-header">
        <div className="view-title-group">
          <h2>Enterprise Data Quality & Governance Scorecard</h2>
          <p className="view-description">
            Continuous automated telemetry across Medallion lakehouse tiers, regulatory constraints, and SLA contracts.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            id="btn-goto-quality-rules"
            className="btn btn-primary"
            onClick={() => onNavigate('quality')}
          >
            <Activity size={16} />
            <span>Evaluate Rules ({summary.total_rules})</span>
          </button>
          <button
            id="btn-goto-compliance"
            className="btn btn-secondary"
            onClick={() => onNavigate('governance')}
          >
            <ShieldCheck size={16} />
            <span>Compliance Matrix</span>
          </button>
        </div>
      </div>

      {/* Top 4 KPI Metric Cards */}
      <div className="metrics-grid">
        {/* Metric 1: Platform Health Score */}
        <div className="glass-panel metric-card" id="metric-health-score">
          <div className="metric-card-header">
            <span className="metric-title">Platform Health Index</span>
            <div style={{ color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '2px', fontSize: '0.75rem', fontWeight: 600 }}>
              <TrendingUp size={14} /> +2.1%
            </div>
          </div>
          <div className="metric-value" style={{ color: '#10b981' }}>
            {summary.overall_score}%
          </div>
          <div className="metric-subtext">
            <span>Enterprise target: &ge; 90.0%</span>
          </div>
        </div>

        {/* Metric 2: Cataloged Assets */}
        <div className="glass-panel metric-card" id="metric-cataloged-assets" onClick={() => onNavigate('catalog')} style={{ cursor: 'pointer' }}>
          <div className="metric-card-header">
            <span className="metric-title">Cataloged Datasets</span>
            <Database size={16} style={{ color: 'var(--accent-cyan)' }} />
          </div>
          <div className="metric-value">{datasets.length}</div>
          <div className="metric-subtext">
            <span>{datasets.reduce((acc, d) => acc + (d.row_count || 0), 0).toLocaleString()} Total Lake Rows</span>
          </div>
        </div>

        {/* Metric 3: Active Quality Issues */}
        <div className="glass-panel metric-card" id="metric-active-issues" onClick={() => onNavigate('quality')} style={{ cursor: 'pointer' }}>
          <div className="metric-card-header">
            <span className="metric-title">Active Quality Issues</span>
            <AlertTriangle size={16} style={{ color: criticalCount > 0 ? 'var(--status-critical)' : 'var(--status-warning)' }} />
          </div>
          <div className="metric-value" style={{ color: criticalCount > 0 ? '#ef4444' : '#f59e0b' }}>
            {openIssues.length}
          </div>
          <div className="metric-subtext">
            <span style={{ color: criticalCount > 0 ? '#f87171' : 'var(--text-dim)' }}>
              {criticalCount} Critical &bull; {openIssues.length - criticalCount} Medium/High
            </span>
          </div>
        </div>

        {/* Metric 4: Freshness SLA */}
        <div className="glass-panel metric-card" id="metric-freshness-sla" onClick={() => onNavigate('contracts')} style={{ cursor: 'pointer' }}>
          <div className="metric-card-header">
            <span className="metric-title">Pipeline Freshness SLA</span>
            <Clock size={16} style={{ color: 'var(--accent-purple)' }} />
          </div>
          <div className="metric-value">
            {summary.freshness_hours}h
          </div>
          <div className="metric-subtext">
            <span style={{ color: 'var(--accent-emerald)' }}>&check; Under 1h contract threshold</span>
          </div>
        </div>
      </div>

      {/* Middle Grid: 6 Dimensions breakdown + Domain Quality Ranking */}
      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        {/* Left: 6 Dimensions Breakdown */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.15rem' }}>6-Dimension Quality Breakdown</h3>
            <span className="badge badge-cyan">Automated Engine</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
            {dimensionList.map((dim) => {
              const score = summary.dimensions[dim.key];
              return (
                <div key={dim.key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.85rem' }}>
                    <span style={{ fontWeight: 500, color: 'var(--text-main)' }}>{dim.name}</span>
                    <span style={{ fontWeight: 700, color: score >= 90 ? 'var(--status-good)' : 'var(--status-warning)' }}>
                      {score}%
                    </span>
                  </div>
                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill"
                      style={{
                        width: `${score}%`,
                        backgroundColor: dim.color,
                        boxShadow: `0 0 10px ${dim.color}66`,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Domain Health & Compliance Posture */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.15rem' }}>Domain Data Assets & Health</h3>
            <span className="badge badge-purple">Medallion Certified</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {datasets.map((ds) => (
              <div
                key={ds.id}
                className="glass-card"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.9rem 1.15rem',
                  borderLeft: `4px solid ${
                    ds.quality_score >= 95 ? 'var(--accent-emerald)' : ds.quality_score >= 90 ? 'var(--accent-blue)' : 'var(--accent-amber)'
                  }`,
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: 600, color: '#fff', fontSize: '0.95rem' }}>{ds.dataset_name}</span>
                    <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>{ds.domain}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.2rem' }}>
                    Owner: {ds.owner_team} &bull; {(ds.row_count || 0).toLocaleString()} rows &bull; {ds.sensitivity}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: ds.quality_score >= 90 ? 'var(--status-good)' : 'var(--status-warning)' }}>
                    {ds.quality_score}%
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Score</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row: Recent Urgent Issues & Quick Remediation */}
      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem' }}>Active Remediation Queue</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Open rule failures requiring automated remediation or steward sign-off.
            </p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('quality')}>
            View All Issues <ArrowUpRight size={14} />
          </button>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Issue ID</th>
                <th>Dataset</th>
                <th>Column</th>
                <th>Rule Code</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Failed Count</th>
                <th>Assignee</th>
              </tr>
            </thead>
            <tbody>
              {issues.slice(0, 4).map((issue) => (
                <tr key={issue.id}>
                  <td style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>{issue.id}</td>
                  <td style={{ fontWeight: 500 }}>{issue.dataset_name}</td>
                  <td><code>{issue.column_name}</code></td>
                  <td style={{ fontSize: '0.75rem' }}>{issue.rule_code}</td>
                  <td>
                    <span
                      className={`badge ${
                        issue.severity === 'CRITICAL' ? 'badge-danger' : issue.severity === 'HIGH' ? 'badge-warning' : 'badge-cyan'
                      }`}
                    >
                      {issue.severity}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        issue.status === 'RESOLVED' ? 'badge-success' : issue.status === 'IN_PROGRESS' ? 'badge-purple' : 'badge-warning'
                      }`}
                    >
                      {issue.status}
                    </span>
                  </td>
                  <td style={{ fontWeight: 700 }}>{issue.failed_count}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{issue.assignee || 'Unassigned'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
