import {
  Dataset,
  QualitySummary,
  QualityRule,
  QualityIssue,
  RemediationAction,
  GlossaryTerm,
  LineageGraph,
  DataContract,
  DriftEvent,
  ComplianceControl,
  MLAnomaly,
  MLRuleRecommendation,
} from '../types';

const API_BASE = '/api/v1';

// In-memory mock store for offline demonstration and resilience
let mockDatasets: Dataset[] = [
  {
    id: 'ds-1',
    dataset_name: 'crm_customers',
    domain: 'CRM',
    owner_team: 'Sales Operations',
    sensitivity: 'CONFIDENTIAL',
    description: 'Core customer records with contact info, lifetime value, and onboarding timestamps.',
    row_count: 142500,
    column_count: 14,
    quality_score: 94.2,
    created_at: '2026-03-12T10:00:00Z',
    updated_at: '2026-10-14T08:30:00Z',
    columns: [
      { column_name: 'customer_id', data_type: 'VARCHAR(64)', null_count: 0, null_percentage: 0.0, distinct_count: 142500, unique_percentage: 100.0, pii_detected: false },
      { column_name: 'email', data_type: 'VARCHAR(255)', null_count: 14, null_percentage: 0.01, distinct_count: 142480, unique_percentage: 99.98, pii_detected: true, pii_type: 'EMAIL' },
      { column_name: 'phone_number', data_type: 'VARCHAR(32)', null_count: 120, null_percentage: 0.08, distinct_count: 141900, unique_percentage: 99.5, pii_detected: true, pii_type: 'PHONE' },
      { column_name: 'first_name', data_type: 'VARCHAR(100)', null_count: 0, null_percentage: 0.0, distinct_count: 8400, unique_percentage: 5.8, pii_detected: true, pii_type: 'PERSON' },
      { column_name: 'annual_spend', data_type: 'DECIMAL(12,2)', null_count: 35, null_percentage: 0.02, distinct_count: 45200, unique_percentage: 31.7, min_value: 0, max_value: 125000, mean: 4850.5, pii_detected: false },
      { column_name: 'signup_date', data_type: 'TIMESTAMP', null_count: 0, null_percentage: 0.0, distinct_count: 1420, unique_percentage: 1.0, pii_detected: false },
    ],
  },
  {
    id: 'ds-2',
    dataset_name: 'erp_transactions',
    domain: 'ERP',
    owner_team: 'Financial Engineering',
    sensitivity: 'RESTRICTED',
    description: 'General ledger transactions, invoice journal lines, and billing settlements.',
    row_count: 2450000,
    column_count: 22,
    quality_score: 97.8,
    created_at: '2026-01-05T09:15:00Z',
    updated_at: '2026-10-14T12:00:00Z',
    columns: [
      { column_name: 'txn_id', data_type: 'UUID', null_count: 0, null_percentage: 0.0, distinct_count: 2450000, unique_percentage: 100.0, pii_detected: false },
      { column_name: 'amount_usd', data_type: 'DECIMAL(14,2)', null_count: 0, null_percentage: 0.0, distinct_count: 890000, unique_percentage: 36.3, min_value: -15000, max_value: 950000, mean: 12450, pii_detected: false },
      { column_name: 'account_number', data_type: 'VARCHAR(34)', null_count: 0, null_percentage: 0.0, distinct_count: 41200, unique_percentage: 1.6, pii_detected: true, pii_type: 'IBAN' },
      { column_name: 'currency', data_type: 'CHAR(3)', null_count: 0, null_percentage: 0.0, distinct_count: 24, unique_percentage: 0.001, pii_detected: false },
    ],
  },
  {
    id: 'ds-3',
    dataset_name: 'hr_employee_master',
    domain: 'HR',
    owner_team: 'People Analytics',
    sensitivity: 'CONFIDENTIAL',
    description: 'Employee demographics, compensation tiers, department assignments, and tenure status.',
    row_count: 8500,
    column_count: 18,
    quality_score: 88.5,
    created_at: '2026-02-18T14:20:00Z',
    updated_at: '2026-10-13T18:45:00Z',
    columns: [
      { column_name: 'emp_id', data_type: 'VARCHAR(20)', null_count: 0, null_percentage: 0.0, distinct_count: 8500, unique_percentage: 100.0, pii_detected: false },
      { column_name: 'ssn', data_type: 'VARCHAR(11)', null_count: 4, null_percentage: 0.04, distinct_count: 8496, unique_percentage: 99.95, pii_detected: true, pii_type: 'SSN' },
      { column_name: 'department', data_type: 'VARCHAR(50)', null_count: 12, null_percentage: 0.14, distinct_count: 32, unique_percentage: 0.37, pii_detected: false },
      { column_name: 'salary_grade', data_type: 'VARCHAR(10)', null_count: 0, null_percentage: 0.0, distinct_count: 15, unique_percentage: 0.17, pii_detected: false },
    ],
  },
  {
    id: 'ds-4',
    dataset_name: 'ecommerce_orders',
    domain: 'ECOMMERCE',
    owner_team: 'Growth Analytics',
    sensitivity: 'INTERNAL',
    description: 'Digital storefront checkout checkouts, cart items, promo coupons, and fulfillment status.',
    row_count: 890000,
    column_count: 19,
    quality_score: 92.1,
    created_at: '2026-04-01T11:00:00Z',
    updated_at: '2026-10-14T14:10:00Z',
  },
];

let mockIssues: QualityIssue[] = [
  {
    id: 'ISSUE-101',
    dataset_name: 'crm_customers',
    rule_code: 'COMP_EMAIL_NULL',
    column_name: 'email',
    severity: 'HIGH',
    status: 'OPEN',
    description: 'Found 14 records with null or blank email in mandatory contact register',
    failed_count: 14,
    assignee: 'Alice Zhang',
    created_at: '2026-10-14T06:12:00Z',
  },
  {
    id: 'ISSUE-102',
    dataset_name: 'erp_transactions',
    rule_code: 'VAL_NEGATIVE_AMOUNT',
    column_name: 'amount_usd',
    severity: 'CRITICAL',
    status: 'IN_PROGRESS',
    description: 'Detected 3 anomalous transaction settlements with unapproved negative balance values',
    failed_count: 3,
    assignee: 'Marcus Vance',
    created_at: '2026-10-14T07:45:00Z',
  },
  {
    id: 'ISSUE-103',
    dataset_name: 'hr_employee_master',
    rule_code: 'UNIQ_SSN_DUPLICATE',
    column_name: 'ssn',
    severity: 'HIGH',
    status: 'RESOLVED',
    description: 'Resolved duplicate SSN hashes resulting from contractor rehire migration',
    failed_count: 2,
    assignee: 'Elena Rostova',
    created_at: '2026-10-13T16:20:00Z',
  },
  {
    id: 'ISSUE-104',
    dataset_name: 'ecommerce_orders',
    rule_code: 'FRESH_SLA_BREACH',
    column_name: 'order_timestamp',
    severity: 'MEDIUM',
    status: 'OPEN',
    description: 'Bronze streaming micro-batch latency exceeded 15 minute freshness SLA',
    failed_count: 1,
    assignee: 'Unassigned',
    created_at: '2026-10-14T09:00:00Z',
  },
];

let mockRules: QualityRule[] = [
  { id: 'R1', rule_code: 'COMP_EMAIL_NULL', name: 'Email Completeness', dimension: 'completeness', column_name: 'email', description: 'Ensure customer email has 0% nulls', threshold: 99.9, status: 'FAILED', severity: 'HIGH', last_evaluated: '2026-10-14T08:30:00Z' },
  { id: 'R2', rule_code: 'VAL_EMAIL_REGEX', name: 'Email Format RFC 5322', dimension: 'validity', column_name: 'email', description: 'Validate standard email pattern', threshold: 99.5, status: 'PASSED', severity: 'HIGH', last_evaluated: '2026-10-14T08:30:00Z' },
  { id: 'R3', rule_code: 'UNIQ_CUST_ID', name: 'Primary Key Uniqueness', dimension: 'uniqueness', column_name: 'customer_id', description: 'Customer ID primary key uniqueness guarantee', threshold: 100.0, status: 'PASSED', severity: 'CRITICAL', last_evaluated: '2026-10-14T08:30:00Z' },
  { id: 'R4', rule_code: 'VAL_NEGATIVE_AMOUNT', name: 'Non-Negative Billing Amount', dimension: 'validity', column_name: 'amount_usd', description: 'Transactions must be >= 0 except credit notes', threshold: 99.99, status: 'FAILED', severity: 'CRITICAL', last_evaluated: '2026-10-14T12:00:00Z' },
  { id: 'R5', rule_code: 'FRESH_STREAM_SLA', name: 'Streaming Freshness SLA', dimension: 'freshness', column_name: 'ingested_at', description: 'Data ingestion lag strictly within 30 minutes', threshold: 95.0, status: 'PASSED', severity: 'MEDIUM', last_evaluated: '2026-10-14T14:00:00Z' },
  { id: 'R6', rule_code: 'CONS_COUNTRY_CODE', name: 'ISO Country Consistency', dimension: 'consistency', column_name: 'country_code', description: 'Country code strictly matches ISO 3166-1 alpha-2', threshold: 100.0, status: 'PASSED', severity: 'LOW', last_evaluated: '2026-10-14T14:00:00Z' },
];

let mockLineage: LineageGraph = {
  nodes: [
    { id: 'src_postgres_crm', label: 'Postgres CRM RDS', type: 'SOURCE', domain: 'CRM', tier: 0, records: 142500, health: 96 },
    { id: 'src_sap_erp', label: 'SAP S/4HANA ERP', type: 'SOURCE', domain: 'ERP', tier: 0, records: 2450000, health: 98 },
    { id: 'src_workday', label: 'Workday HR API', type: 'SOURCE', domain: 'HR', tier: 0, records: 8500, health: 92 },
    { id: 'bronze_raw_crm', label: 'bronze.crm_customers', type: 'BRONZE', domain: 'CRM', tier: 1, records: 142500, health: 94 },
    { id: 'bronze_raw_erp', label: 'bronze.erp_ledger', type: 'BRONZE', domain: 'ERP', tier: 1, records: 2450000, health: 97 },
    { id: 'silver_clean_customers', label: 'silver.dim_customer', type: 'SILVER', domain: 'CRM', tier: 2, records: 142486, health: 99 },
    { id: 'silver_clean_finance', label: 'silver.fct_gl_journal', type: 'SILVER', domain: 'ERP', tier: 2, records: 2449997, health: 99 },
    { id: 'gold_mrr_revenue', label: 'gold.mrr_executive_mart', type: 'GOLD', domain: 'FINANCE', tier: 3, records: 360000, health: 98 },
    { id: 'bi_tableau_exec', label: 'Tableau Executive MRR', type: 'BI', domain: 'FINANCE', tier: 4, records: 360000, health: 100 },
    { id: 'bi_powerbi_sales', label: 'PowerBI Sales Performance', type: 'BI', domain: 'CRM', tier: 4, records: 142486, health: 98 },
  ],
  edges: [
    { id: 'e1', source: 'src_postgres_crm', target: 'bronze_raw_crm', label: 'Kafka Ingest' },
    { id: 'e2', source: 'src_sap_erp', target: 'bronze_raw_erp', label: 'Airflow Batch' },
    { id: 'e3', source: 'bronze_raw_crm', target: 'silver_clean_customers', label: 'PySpark Clean & Dedupe' },
    { id: 'e4', source: 'bronze_raw_erp', target: 'silver_clean_finance', label: 'PySpark Medallion' },
    { id: 'e5', source: 'silver_clean_customers', target: 'gold_mrr_revenue', label: 'dbt Star Schema' },
    { id: 'e6', source: 'silver_clean_finance', target: 'gold_mrr_revenue', label: 'dbt Aggregation' },
    { id: 'e7', source: 'gold_mrr_revenue', target: 'bi_tableau_exec', label: 'Direct Query' },
    { id: 'e8', source: 'silver_clean_customers', target: 'bi_powerbi_sales', label: 'PowerBI Connector' },
  ],
};

let mockContracts: DataContract[] = [
  {
    id: 'cnt-01',
    dataset_name: 'crm_customers',
    version: '1.4.0',
    owner: 'data-engineering@enterprise.org',
    sla_freshness_hours: 1,
    status: 'ACTIVE',
    schema_columns: [
      { name: 'customer_id', type: 'VARCHAR(64)', nullable: false, pii: false },
      { name: 'email', type: 'VARCHAR(255)', nullable: false, pii: true },
      { name: 'phone_number', type: 'VARCHAR(32)', nullable: true, pii: true },
      { name: 'annual_spend', type: 'DECIMAL(12,2)', nullable: true, pii: false },
    ],
    last_validated: '2026-10-14T14:30:00Z',
  },
  {
    id: 'cnt-02',
    dataset_name: 'erp_transactions',
    version: '2.1.0',
    owner: 'finance-core@enterprise.org',
    sla_freshness_hours: 6,
    status: 'ACTIVE',
    schema_columns: [
      { name: 'txn_id', type: 'UUID', nullable: false, pii: false },
      { name: 'amount_usd', type: 'DECIMAL(14,2)', nullable: false, pii: false },
      { name: 'account_number', type: 'VARCHAR(34)', nullable: false, pii: true },
    ],
    last_validated: '2026-10-14T12:00:00Z',
  },
];

let mockDriftEvents: DriftEvent[] = [
  {
    id: 'drf-1',
    dataset_name: 'crm_customers',
    drift_type: 'COLUMN_ADDED',
    detail: 'Field "loyalty_tier" detected with default type VARCHAR(20) without prior contract bump.',
    detected_at: '2026-10-13T21:40:00Z',
    severity: 'MEDIUM',
  },
  {
    id: 'drf-2',
    dataset_name: 'ecommerce_orders',
    drift_type: 'TYPE_MISMATCH',
    detail: 'Field "discount_pct" changed from FLOAT to DECIMAL(5,2).',
    detected_at: '2026-10-12T14:15:00Z',
    severity: 'LOW',
  },
];

let mockCompliance: ComplianceControl[] = [
  { framework: 'GDPR', control_id: 'Art. 17', name: 'Right to Erasure (RTBF)', description: 'Automated cryptographic erasure workflow across Lakehouse tables', status: 'COMPLIANT', affected_assets_count: 4 },
  { framework: 'GDPR', control_id: 'Art. 32', name: 'Pseudonymization & Encryption', description: 'Deterministic AES-256 / SHA-256 field-level masking for PII columns', status: 'COMPLIANT', affected_assets_count: 7 },
  { framework: 'HIPAA', control_id: '164.312(a)', name: 'Access Control & Audit Logging', description: 'Granular RBAC and append-only governance trail records', status: 'COMPLIANT', affected_assets_count: 12 },
  { framework: 'SOC2', control_id: 'CC6.1', name: 'Logical Perimeter Data Boundaries', description: 'Medallion Lake isolation between raw Bronze and certified Gold marts', status: 'COMPLIANT', affected_assets_count: 9 },
  { framework: 'ISO27001', control_id: 'A.8.2', name: 'Information Classification Matrix', description: 'Automated regex & ML detection of Confidential/Restricted datasets', status: 'NEEDS_REVIEW', affected_assets_count: 2 },
];

let mockAnomalies: MLAnomaly[] = [
  { id: 'anm-1', dataset_name: 'crm_customers', column_name: 'annual_spend', metric_name: 'mean_daily_spend', detected_value: 38400.0, expected_range: [4200.0, 5600.0], z_score: 4.82, timestamp: '2026-10-14T08:00:00Z', is_anomaly: true },
  { id: 'anm-2', dataset_name: 'erp_transactions', column_name: 'amount_usd', metric_name: 'null_percentage', detected_value: 0.0, expected_range: [0.0, 0.05], z_score: 0.1, timestamp: '2026-10-14T11:00:00Z', is_anomaly: false },
];

let mockRecommendations: MLRuleRecommendation[] = [
  { id: 'rec-1', dataset_name: 'crm_customers', column_name: 'phone_number', suggested_rule: 'E164_PHONE_FORMAT', dimension: 'validity', confidence: 0.96, reason: 'Identified 99.5% adherence to E.164 phone specification with minor prefix variance.' },
  { id: 'rec-2', dataset_name: 'erp_transactions', column_name: 'currency', suggested_rule: 'ISO_4217_CURRENCY', dimension: 'consistency', confidence: 0.99, reason: 'High categorical cardinality matching global currency codes standard.' },
];

// Helper for safe fetch with mock fallback
async function fetchWithFallback<T>(url: string, fallback: T): Promise<T> {
  try {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), 1800);
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(id);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    // Graceful fallback to rich mock data
    return fallback;
  }
}

export const apiService = {
  // Health
  async getHealth(): Promise<{ status: string; version: string; database: string }> {
    return fetchWithFallback(`${API_BASE}/health`, { status: 'healthy', version: '1.0.0', database: 'connected (simulated)' });
  },

  // Executive Quality Summary
  async getQualitySummary(): Promise<QualitySummary> {
    return {
      overall_score: 93.4,
      dimensions: {
        completeness: 94.8,
        validity: 92.5,
        uniqueness: 98.1,
        consistency: 95.3,
        accuracy: 91.0,
        freshness: 89.2,
      },
      passed_rules: 42,
      failed_rules: 3,
      total_rules: 45,
      active_issues: mockIssues.filter(i => i.status !== 'RESOLVED').length,
      critical_issues: mockIssues.filter(i => i.severity === 'CRITICAL' && i.status !== 'RESOLVED').length,
      freshness_hours: 0.6,
    };
  },

  // Catalog
  async getDatasets(): Promise<Dataset[]> {
    return fetchWithFallback(`${API_BASE}/catalog/datasets`, mockDatasets);
  },

  async getDatasetById(id: string): Promise<Dataset | undefined> {
    const all = await this.getDatasets();
    return all.find(d => d.id === id || d.dataset_name === id);
  },

  // Quality Rules & Issues
  async getQualityRules(): Promise<QualityRule[]> {
    return fetchWithFallback(`${API_BASE}/quality/rules`, mockRules);
  },

  async getIssues(): Promise<QualityIssue[]> {
    return fetchWithFallback(`${API_BASE}/issues`, mockIssues);
  },

  async updateIssueStatus(issueId: string, status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED'): Promise<QualityIssue | undefined> {
    const issue = mockIssues.find(i => i.id === issueId);
    if (issue) {
      issue.status = status;
    }
    return issue;
  },

  async executeRemediation(issueId: string, actionType: string): Promise<{ success: boolean; message: string; rows_remediated: number }> {
    const issue = mockIssues.find(i => i.id === issueId);
    if (issue) {
      issue.status = 'RESOLVED';
    }
    return {
      success: true,
      message: `Deterministic remediation '${actionType}' completed successfully.`,
      rows_remediated: issue ? issue.failed_count : 14,
    };
  },

  // Lineage
  async getLineageGraph(): Promise<LineageGraph> {
    return fetchWithFallback(`${API_BASE}/lineage/graph`, mockLineage);
  },

  // Contracts
  async getContracts(): Promise<DataContract[]> {
    return fetchWithFallback(`${API_BASE}/contracts`, mockContracts);
  },

  async getDriftEvents(): Promise<DriftEvent[]> {
    return fetchWithFallback(`${API_BASE}/contracts/drift`, mockDriftEvents);
  },

  // Governance & Compliance
  async getComplianceControls(): Promise<ComplianceControl[]> {
    return fetchWithFallback(`${API_BASE}/governance/compliance`, mockCompliance);
  },

  maskText(raw: string, type: 'EMAIL' | 'PHONE' | 'SSN' | 'IBAN' | 'GENERAL'): string {
    if (!raw) return '';
    if (type === 'EMAIL') {
      const parts = raw.split('@');
      if (parts.length === 2) {
        return `${parts[0].slice(0, 2)}***@${parts[1]}`;
      }
    }
    if (type === 'PHONE') {
      return raw.replace(/(\d{3})\d{4}(\d{3})/, '$1-XXXX-$2');
    }
    if (type === 'SSN') {
      return 'XXX-XX-' + raw.slice(-4);
    }
    if (type === 'IBAN') {
      return raw.slice(0, 4) + ' **** **** ' + raw.slice(-4);
    }
    return '********';
  },

  // ML Anomalies & Recommendations
  async getAnomalies(): Promise<MLAnomaly[]> {
    return fetchWithFallback(`${API_BASE}/ml/anomalies`, mockAnomalies);
  },

  async getRuleRecommendations(): Promise<MLRuleRecommendation[]> {
    return fetchWithFallback(`${API_BASE}/ml/recommendations`, mockRecommendations);
  },
};
