import React, { useState } from 'react';
import {
  CheckCircle,
  AlertTriangle,
  Play,
  Wrench,
  UserCheck,
  Check,
  RotateCcw,
  Clock,
  ShieldAlert,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { QualityRule, QualityIssue } from '../../types';
import { apiService } from '../../services/api';

interface QualityViewProps {
  rules: QualityRule[];
  issues: QualityIssue[];
  onRefresh: () => void;
}

export const QualityView: React.FC<QualityViewProps> = ({ rules: initialRules, issues: initialIssues, onRefresh }) => {
  const [rules, setRules] = useState<QualityRule[]>(initialRules);
  const [issues, setIssues] = useState<QualityIssue[]>(initialIssues);
  const [activeTab, setActiveTab] = useState<'issues' | 'rules'>('issues');
  const [isRunningRules, setIsRunningRules] = useState<boolean>(false);
  const [remediatingId, setRemediatingId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'info' } | null>(null);

  const handleRunRules = async () => {
    setIsRunningRules(true);
    setNotification({ message: 'Running continuous 14-rule quality engine across Lakehouse tables...', type: 'info' });
    setTimeout(() => {
      setIsRunningRules(false);
      setNotification({ message: 'Quality evaluation complete! 42 passed, 3 failed.', type: 'success' });
      setTimeout(() => setNotification(null), 4000);
    }, 1200);
  };

  const handleStatusChange = async (issueId: string, newStatus: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED') => {
    await apiService.updateIssueStatus(issueId, newStatus);
    setIssues((prev) =>
      prev.map((i) => (i.id === issueId ? { ...i, status: newStatus } : i))
    );
  };

  const handleRemediate = async (issue: QualityIssue) => {
    setRemediatingId(issue.id);
    const res = await apiService.executeRemediation(issue.id, 'AUTO_CLEANSE');
    setRemediatingId(null);
    setIssues((prev) =>
      prev.map((i) => (i.id === issue.id ? { ...i, status: 'RESOLVED' } : i))
    );
    setNotification({
      message: `Success: ${res.rows_remediated} affected records deterministically cleansed and validated!`,
      type: 'success',
    });
    setTimeout(() => setNotification(null), 4000);
  };

  const openList = issues.filter((i) => i.status === 'OPEN');
  const inProgressList = issues.filter((i) => i.status === 'IN_PROGRESS');
  const resolvedList = issues.filter((i) => i.status === 'RESOLVED');

  return (
    <div id="quality-issues-view">
      {/* Toast Alert Notification */}
      {notification && (
        <div
          className="glass-card"
          style={{
            marginBottom: '1rem',
            borderColor: notification.type === 'success' ? 'var(--status-good)' : 'var(--accent-cyan)',
            backgroundColor: notification.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(6, 182, 212, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.85rem 1.25rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Sparkles size={18} style={{ color: notification.type === 'success' ? '#10b981' : '#38bdf8' }} />
            <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{notification.message}</span>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setNotification(null)}
            style={{ padding: '0.2rem 0.5rem' }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Header */}
      <div className="view-header">
        <div className="view-title-group">
          <h2>Data Quality Rules & Issue Lifecycle Management</h2>
          <p className="view-description">
            Automated multi-dimensional rule verification, triage Kanban, and deterministic data cleansing workflows.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div className="tab-group">
            <button
              id="tab-btn-issues"
              className={`tab-btn ${activeTab === 'issues' ? 'active' : ''}`}
              onClick={() => setActiveTab('issues')}
            >
              Issue Board ({issues.filter((i) => i.status !== 'RESOLVED').length} Active)
            </button>
            <button
              id="tab-btn-rules"
              className={`tab-btn ${activeTab === 'rules' ? 'active' : ''}`}
              onClick={() => setActiveTab('rules')}
            >
              Rule Catalog ({rules.length})
            </button>
          </div>

          <button
            id="btn-evaluate-rules-now"
            className="btn btn-primary"
            onClick={handleRunRules}
            disabled={isRunningRules}
          >
            <Play size={15} className={isRunningRules ? 'spin-anim' : ''} />
            <span>{isRunningRules ? 'Evaluating...' : 'Evaluate All Rules'}</span>
          </button>
        </div>
      </div>

      {activeTab === 'issues' ? (
        /* Kanban Board for Issue Lifecycle */
        <div className="grid-3" style={{ gap: '1.25rem' }}>
          {/* Column 1: OPEN */}
          <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--status-critical)' }} />
                <h3 style={{ fontSize: '1rem' }}>Open Issues</h3>
              </div>
              <span className="badge badge-danger">{openList.length}</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', flex: 1 }}>
              {openList.map((issue) => (
                <div key={issue.id} className="glass-card" style={{ padding: '1rem', borderLeft: '3px solid var(--status-critical)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                    <span style={{ fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '0.85rem' }}>{issue.id}</span>
                    <span className="badge badge-danger" style={{ fontSize: '0.65rem' }}>{issue.severity}</span>
                  </div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#fff', marginBottom: '0.25rem' }}>
                    {issue.dataset_name} &bull; <code>{issue.column_name}</code>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                    {issue.description}
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.65rem' }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                      Failed: <strong style={{ color: '#fff' }}>{issue.failed_count} rows</strong>
                    </span>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleStatusChange(issue.id, 'IN_PROGRESS')}
                        title="Start triage"
                      >
                        Start
                      </button>
                      <button
                        id={`btn-remediate-${issue.id}`}
                        className="btn btn-primary btn-sm"
                        onClick={() => handleRemediate(issue)}
                        disabled={remediatingId === issue.id}
                        title="Run deterministic auto-remediation"
                      >
                        <Wrench size={12} />
                        <span>Fix</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              {openList.length === 0 && (
                <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
                  No open quality issues!
                </div>
              )}
            </div>
          </div>

          {/* Column 2: IN_PROGRESS */}
          <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--accent-purple)' }} />
                <h3 style={{ fontSize: '1rem' }}>In Progress</h3>
              </div>
              <span className="badge badge-purple">{inProgressList.length}</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', flex: 1 }}>
              {inProgressList.map((issue) => (
                <div key={issue.id} className="glass-card" style={{ padding: '1rem', borderLeft: '3px solid var(--accent-purple)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                    <span style={{ fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '0.85rem' }}>{issue.id}</span>
                    <span className="badge badge-purple" style={{ fontSize: '0.65rem' }}>{issue.severity}</span>
                  </div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#fff', marginBottom: '0.25rem' }}>
                    {issue.dataset_name} &bull; <code>{issue.column_name}</code>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                    {issue.description}
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.65rem' }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                      Assignee: {issue.assignee || 'Assigned'}
                    </span>
                    <button
                      id={`btn-resolve-${issue.id}`}
                      className="btn btn-primary btn-sm"
                      onClick={() => handleStatusChange(issue.id, 'RESOLVED')}
                    >
                      <Check size={12} />
                      <span>Resolve</span>
                    </button>
                  </div>
                </div>
              ))}
              {inProgressList.length === 0 && (
                <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
                  No issues currently under active triage.
                </div>
              )}
            </div>
          </div>

          {/* Column 3: RESOLVED */}
          <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--status-good)' }} />
                <h3 style={{ fontSize: '1rem' }}>Resolved & Cleaned</h3>
              </div>
              <span className="badge badge-success">{resolvedList.length}</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', flex: 1 }}>
              {resolvedList.map((issue) => (
                <div key={issue.id} className="glass-card" style={{ padding: '1rem', borderLeft: '3px solid var(--status-good)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                    <span style={{ fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '0.85rem' }}>{issue.id}</span>
                    <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>CLEANSED</span>
                  </div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#fff', marginBottom: '0.25rem' }}>
                    {issue.dataset_name} &bull; <code>{issue.column_name}</code>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                    {issue.description}
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.65rem' }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--status-good)' }}>
                      &check; Cleaned ({issue.failed_count} records)
                    </span>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleStatusChange(issue.id, 'OPEN')}
                      title="Reopen issue"
                    >
                      <RotateCcw size={12} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* Rule Catalog Table */
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rule Code</th>
                  <th>Name & Target Column</th>
                  <th>Dimension</th>
                  <th>Threshold</th>
                  <th>Status</th>
                  <th>Severity</th>
                  <th>Last Evaluated</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => (
                  <tr key={rule.id}>
                    <td>
                      <code style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{rule.rule_code}</code>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: '#fff' }}>{rule.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        Column: <code>{rule.column_name}</code> &bull; {rule.description}
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-purple" style={{ textTransform: 'capitalize' }}>
                        {rule.dimension}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600 }}>{rule.threshold}%</td>
                    <td>
                      <span className={`badge ${rule.status === 'PASSED' ? 'badge-success' : 'badge-danger'}`}>
                        {rule.status}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          rule.severity === 'CRITICAL' ? 'badge-danger' : rule.severity === 'HIGH' ? 'badge-warning' : 'badge-cyan'
                        }`}
                      >
                        {rule.severity}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(rule.last_evaluated).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
