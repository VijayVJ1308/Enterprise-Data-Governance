import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Sidebar, NavView } from './components/layout/Sidebar';
import { ExecutiveView } from './components/dashboard/ExecutiveView';
import { CatalogView } from './components/catalog/CatalogView';
import { QualityView } from './components/quality/QualityView';
import { LineageView } from './components/lineage/LineageView';
import { ContractsView } from './components/contracts/ContractsView';
import { GovernanceView } from './components/governance/GovernanceView';
import { AnomalyView } from './components/ml/AnomalyView';
import { apiService } from './services/api';
import {
  Dataset,
  QualitySummary,
  QualityRule,
  QualityIssue,
  LineageGraph,
  DataContract,
  DriftEvent,
  ComplianceControl,
  MLAnomaly,
  MLRuleRecommendation,
} from './types';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<NavView>('executive');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // Platform Data State
  const [summary, setSummary] = useState<QualitySummary | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [rules, setRules] = useState<QualityRule[]>([]);
  const [issues, setIssues] = useState<QualityIssue[]>([]);
  const [lineage, setLineage] = useState<LineageGraph | null>(null);
  const [contracts, setContracts] = useState<DataContract[]>([]);
  const [driftEvents, setDriftEvents] = useState<DriftEvent[]>([]);
  const [compliance, setCompliance] = useState<ComplianceControl[]>([]);
  const [anomalies, setAnomalies] = useState<MLAnomaly[]>([]);
  const [recommendations, setRecommendations] = useState<MLRuleRecommendation[]>([]);

  const loadAllData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [
        sumData,
        dsData,
        rulesData,
        issuesData,
        lineageData,
        contractsData,
        driftData,
        compData,
        anomData,
        recData,
      ] = await Promise.all([
        apiService.getQualitySummary(),
        apiService.getDatasets(),
        apiService.getQualityRules(),
        apiService.getIssues(),
        apiService.getLineageGraph(),
        apiService.getContracts(),
        apiService.getDriftEvents(),
        apiService.getComplianceControls(),
        apiService.getAnomalies(),
        apiService.getRuleRecommendations(),
      ]);

      setSummary(sumData);
      setDatasets(dsData);
      setRules(rulesData);
      setIssues(issuesData);
      setLineage(lineageData);
      setContracts(contractsData);
      setDriftEvents(driftData);
      setCompliance(compData);
      setAnomalies(anomData);
      setRecommendations(recData);
    } catch (err) {
      console.error('Failed loading platform telemetry:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  const activeIssueCount = issues.filter((i) => i.status !== 'RESOLVED').length;

  return (
    <div className="app-container">
      <Navbar
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        onRefresh={loadAllData}
        isRefreshing={isRefreshing}
      />

      <div className="main-layout">
        <Sidebar
          currentView={currentView}
          onSelectView={setCurrentView}
          activeIssueCount={activeIssueCount}
        />

        <main className="content-area" id="main-content-panel">
          {summary && currentView === 'executive' && (
            <ExecutiveView
              summary={summary}
              datasets={datasets}
              issues={issues}
              onNavigate={(v) => setCurrentView(v as NavView)}
            />
          )}

          {currentView === 'catalog' && (
            <CatalogView
              datasets={datasets}
              searchTerm={searchTerm}
            />
          )}

          {currentView === 'quality' && (
            <QualityView
              rules={rules}
              issues={issues}
              onRefresh={loadAllData}
            />
          )}

          {lineage && currentView === 'lineage' && (
            <LineageView graph={lineage} />
          )}

          {currentView === 'contracts' && (
            <ContractsView
              contracts={contracts}
              driftEvents={driftEvents}
            />
          )}

          {currentView === 'governance' && (
            <GovernanceView complianceControls={compliance} />
          )}

          {currentView === 'ml' && (
            <AnomalyView
              anomalies={anomalies}
              recommendations={recommendations}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
