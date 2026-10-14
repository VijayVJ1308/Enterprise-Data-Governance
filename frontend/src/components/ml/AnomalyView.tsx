import React, { useState } from 'react';
import {
  Sparkles,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Lightbulb,
  PlusCircle,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import { MLAnomaly, MLRuleRecommendation } from '../../types';

interface AnomalyViewProps {
  anomalies: MLAnomaly[];
  recommendations: MLRuleRecommendation[];
}

export const AnomalyView: React.FC<AnomalyViewProps> = ({
  anomalies,
  recommendations: initialRecommendations,
}) => {
  const [recommendations, setRecommendations] = useState<MLRuleRecommendation[]>(initialRecommendations);
  const [adoptedIds, setAdoptedIds] = useState<string[]>([]);
  const [toast, setToast] = useState<string | null>(null);

  const handleAdopt = (rec: MLRuleRecommendation) => {
    setAdoptedIds((prev) => [...prev, rec.id]);
    setToast(`Adopted recommendation: Rule '${rec.suggested_rule}' successfully added to Quality Engine!`);
    setTimeout(() => setToast(null), 4000);
  };

  return (
    <div id="ml-observability-view">
      {/* Toast Alert */}
      {toast && (
        <div
          className="glass-card"
          style={{
            marginBottom: '1rem',
            borderColor: 'var(--accent-purple)',
            backgroundColor: 'rgba(139, 92, 246, 0.15)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.65rem',
            padding: '0.85rem 1.25rem',
          }}
        >
          <Sparkles size={18} style={{ color: 'var(--accent-purple)' }} />
          <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{toast}</span>
        </div>
      )}

      {/* Header */}
      <div className="view-header">
        <div className="view-title-group">
          <h2>ML Observability & Anomaly Discovery</h2>
          <p className="view-description">
            Unsupervised statistical outlier detection (Z-Score & IQR) and automated machine learning rule recommendations.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <span className="badge badge-purple" style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}>
            <Sparkles size={14} /> Gaussian Profiler Active
          </span>
        </div>
      </div>

      {/* Grid: Statistical Anomalies on Left vs Rule Recommendations on Right */}
      <div className="grid-2">
        {/* Left: Outlier Telemetry */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem' }}>Statistical Distribution Anomalies</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Deviations exceeding 3.0 standard deviations from 30-day baseline.
              </p>
            </div>
            <span className="badge badge-danger">
              {anomalies.filter((a) => a.is_anomaly).length} Critical Outliers
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {anomalies.map((anm) => (
              <div
                key={anm.id}
                className="glass-card"
                style={{
                  borderLeft: `4px solid ${anm.is_anomaly ? 'var(--status-critical)' : 'var(--status-good)'}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: 700, color: '#fff', fontSize: '0.95rem' }}>{anm.dataset_name}</span>
                    <code>{anm.column_name}</code>
                  </div>
                  <span
                    className={`badge ${anm.is_anomaly ? 'badge-danger' : 'badge-success'}`}
                    style={{ fontSize: '0.65rem' }}
                  >
                    {anm.is_anomaly ? 'ANOMALY DETECTED' : 'NORMAL RANGE'}
                  </span>
                </div>

                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                  Metric: <strong style={{ color: 'var(--text-main)' }}>{anm.metric_name}</strong>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-dim)', background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: 'var(--radius-sm)' }}>
                  <div>
                    Observed:{' '}
                    <span style={{ color: anm.is_anomaly ? 'var(--status-critical)' : 'var(--status-good)', fontWeight: 700 }}>
                      {anm.detected_value.toLocaleString()}
                    </span>
                  </div>
                  <div>
                    Expected Range:{' '}
                    <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>
                      [{anm.expected_range[0]}, {anm.expected_range[1]}]
                    </span>
                  </div>
                  <div>
                    Z-Score:{' '}
                    <span style={{ color: anm.z_score > 3 ? 'var(--status-critical)' : 'var(--text-main)', fontWeight: 700 }}>
                      {anm.z_score} &sigma;
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Automated Rule Recommendations */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem' }}>AI-Suggested Quality Rules</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Pattern mining and schema heuristics automatically generating production assertions.
              </p>
            </div>
            <span className="badge badge-purple">{recommendations.length} Suggestions</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {recommendations.map((rec) => {
              const isAdopted = adoptedIds.includes(rec.id);
              return (
                <div
                  key={rec.id}
                  className="glass-card"
                  style={{
                    borderLeft: `4px solid ${isAdopted ? 'var(--status-good)' : 'var(--accent-purple)'}`,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontWeight: 700, color: 'var(--accent-purple)', fontSize: '0.9rem' }}>
                        {rec.suggested_rule}
                      </span>
                      <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>
                        {rec.dimension}
                      </span>
                    </div>
                    <span className="badge badge-purple" style={{ fontSize: '0.65rem' }}>
                      {(rec.confidence * 100).toFixed(0)}% Confidence
                    </span>
                  </div>

                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                    Target: <strong>{rec.dataset_name}</strong> &bull; <code>{rec.column_name}</code>
                  </div>

                  <p style={{ fontSize: '0.8rem', color: 'var(--text-main)', marginBottom: '0.75rem' }}>
                    {rec.reason}
                  </p>

                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                      id={`btn-adopt-rec-${rec.id}`}
                      className={`btn btn-sm ${isAdopted ? 'btn-secondary' : 'btn-primary'}`}
                      disabled={isAdopted}
                      onClick={() => handleAdopt(rec)}
                    >
                      {isAdopted ? (
                        <>
                          <CheckCircle size={14} style={{ color: 'var(--status-good)' }} />
                          <span>Active in Rule Engine</span>
                        </>
                      ) : (
                        <>
                          <PlusCircle size={14} />
                          <span>Adopt Rule</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
