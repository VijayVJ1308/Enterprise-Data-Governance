import React, { useState } from 'react';
import {
  GitBranch,
  Layers,
  ArrowRight,
  Database,
  BarChart,
  Shield,
  Activity,
  CheckCircle,
  Info,
} from 'lucide-react';
import { LineageGraph, LineageNode } from '../../types';

interface LineageViewProps {
  graph: LineageGraph;
}

export const LineageView: React.FC<LineageViewProps> = ({ graph }) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string>('silver_clean_customers');

  const selectedNode = graph.nodes.find((n) => n.id === selectedNodeId) || graph.nodes[0];

  // Upstream and downstream calculations
  const incomingEdges = graph.edges.filter((e) => e.target === selectedNodeId);
  const outgoingEdges = graph.edges.filter((e) => e.source === selectedNodeId);

  // Group nodes by tier (0: Source, 1: Bronze, 2: Silver, 3: Gold, 4: BI)
  const tiers = [
    { tier: 0, title: 'Sources', color: 'var(--accent-blue)', bg: 'rgba(59, 130, 246, 0.1)' },
    { tier: 1, title: 'Bronze Raw', color: 'var(--accent-amber)', bg: 'rgba(245, 158, 11, 0.1)' },
    { tier: 2, title: 'Silver Cleansed', color: 'var(--accent-cyan)', bg: 'rgba(6, 182, 212, 0.1)' },
    { tier: 3, title: 'Gold Marts', color: 'var(--accent-purple)', bg: 'rgba(139, 92, 246, 0.1)' },
    { tier: 4, title: 'BI & Downstream', color: 'var(--accent-emerald)', bg: 'rgba(16, 185, 129, 0.1)' },
  ];

  const getNodeColor = (type: LineageNode['type']) => {
    switch (type) {
      case 'SOURCE': return '#3b82f6';
      case 'BRONZE': return '#f59e0b';
      case 'SILVER': return '#06b6d4';
      case 'GOLD': return '#8b5cf6';
      case 'BI': return '#10b981';
      default: return '#94a3b8';
    }
  };

  return (
    <div id="lineage-graph-view">
      {/* Header */}
      <div className="view-header">
        <div className="view-title-group">
          <h2>End-to-End Medallion Data Lineage & Impact Analysis</h2>
          <p className="view-description">
            Interactive dependency graph tracking data flow from external source ingestion through Bronze, Silver, Gold, and downstream BI reports.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <span className="badge badge-purple" style={{ fontSize: '0.75rem' }}>
            <Activity size={12} /> Live Lineage DAG Active
          </span>
        </div>
      </div>

      {/* Main Graph Visualization Panel */}
      <div className="glass-panel" style={{ padding: '1.75rem', marginBottom: '1.5rem', overflowX: 'auto' }}>
        <div style={{ minWidth: '950px' }}>
          {/* Tier Columns Header */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1.5rem', marginBottom: '1.5rem' }}>
            {tiers.map((t) => (
              <div
                key={t.tier}
                style={{
                  padding: '0.5rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: t.bg,
                  border: `1px solid ${t.color}40`,
                  textAlign: 'center',
                }}
              >
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: t.color, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {t.title}
                </span>
              </div>
            ))}
          </div>

          {/* Nodes Grid by Tier */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1.5rem' }}>
            {tiers.map((t) => {
              const nodesInTier = graph.nodes.filter((n) => n.tier === t.tier);
              return (
                <div key={t.tier} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {nodesInTier.map((node) => {
                    const isSelected = selectedNodeId === node.id;
                    const isUpstream = incomingEdges.some((e) => e.source === node.id);
                    const isDownstream = outgoingEdges.some((e) => e.target === node.id);

                    let borderHighlight = 'var(--border-subtle)';
                    if (isSelected) borderHighlight = 'var(--accent-cyan)';
                    else if (isUpstream) borderHighlight = 'var(--accent-blue)';
                    else if (isDownstream) borderHighlight = 'var(--accent-emerald)';

                    return (
                      <div
                        key={node.id}
                        id={`lineage-node-${node.id}`}
                        className="glass-card"
                        onClick={() => setSelectedNodeId(node.id)}
                        style={{
                          cursor: 'pointer',
                          borderColor: borderHighlight,
                          boxShadow: isSelected ? 'var(--glow-cyan)' : undefined,
                          background: isSelected ? 'rgba(30, 41, 59, 0.95)' : undefined,
                          borderLeft: `4px solid ${getNodeColor(node.type)}`,
                          padding: '0.9rem',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                          <span style={{ fontSize: '0.7rem', color: getNodeColor(node.type), fontWeight: 700 }}>
                            {node.type}
                          </span>
                          <span style={{ fontSize: '0.72rem', color: 'var(--status-good)', fontWeight: 600 }}>
                            {node.health}%
                          </span>
                        </div>

                        <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#fff', marginBottom: '0.25rem', wordBreak: 'break-word' }}>
                          {node.label}
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '0.5rem' }}>
                          <span>{node.domain}</span>
                          <span>{node.records.toLocaleString()} rows</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Selected Node Details & Impact Analysis Drawer */}
      <div className="grid-2">
        {/* Node Specifications */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem' }}>Selected Node: {selectedNode.label}</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Artifact ID: <code>{selectedNode.id}</code> &bull; Domain: {selectedNode.domain}
              </p>
            </div>
            <span
              className="badge"
              style={{
                backgroundColor: `${getNodeColor(selectedNode.type)}20`,
                color: getNodeColor(selectedNode.type),
                borderColor: `${getNodeColor(selectedNode.type)}50`,
              }}
            >
              {selectedNode.type} TIER
            </span>
          </div>

          <div className="grid-2" style={{ gap: '1rem', marginBottom: '1rem' }}>
            <div className="glass-card">
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Volume</div>
              <div style={{ fontSize: '1.35rem', fontWeight: 700, color: '#fff' }}>
                {selectedNode.records.toLocaleString()}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Lakehouse records</div>
            </div>

            <div className="glass-card">
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Quality Health</div>
              <div style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--status-good)' }}>
                {selectedNode.health}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Automated score</div>
            </div>
          </div>
        </div>

        {/* Upstream & Downstream Dependencies */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.15rem', marginBottom: '1rem' }}>Impact & Dependency Analysis</h3>

          <div style={{ marginBottom: '1.25rem' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '0.5rem' }}>
              Immediate Upstream Ancestors ({incomingEdges.length})
            </div>
            {incomingEdges.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {incomingEdges.map((e) => (
                  <div key={e.id} className="glass-card" style={{ padding: '0.65rem 0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                    <span style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>{e.source}</span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Via: {e.label}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Source origin node (no upstream).</div>
            )}
          </div>

          <div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '0.5rem' }}>
              Downstream Consumer Impact ({outgoingEdges.length})
            </div>
            {outgoingEdges.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {outgoingEdges.map((e) => (
                  <div key={e.id} className="glass-card" style={{ padding: '0.65rem 0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                    <span style={{ fontWeight: 600, color: 'var(--accent-emerald)' }}>{e.target}</span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Via: {e.label}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Leaf node (no downstream dependencies).</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
