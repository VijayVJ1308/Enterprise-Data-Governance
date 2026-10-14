// Phase 18: TypeScript domain interfaces

export type DomainType = 'CRM' | 'ERP' | 'HR' | 'FINANCE' | 'ECOMMERCE' | 'MARKETING';
export type SensitivityLevel = 'PUBLIC' | 'INTERNAL' | 'CONFIDENTIAL' | 'RESTRICTED';
export type IssueSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type IssueStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'DISMISSED';

export interface ColumnProfile {
  column_name: string;
  data_type: string;
  null_count: number;
  null_percentage: number;
  distinct_count: number;
  unique_percentage: number;
  min_value?: any;
  max_value?: any;
  mean?: number;
  std_dev?: number;
  pii_detected?: boolean;
  pii_type?: string;
}

export interface Dataset {
  id: string;
  dataset_name: string;
  domain: DomainType;
  owner_team: string;
  sensitivity: SensitivityLevel;
  description: string;
  row_count: number;
  column_count: number;
  quality_score: number;
  columns?: ColumnProfile[];
  created_at: string;
  updated_at: string;
}

export interface DimensionScores {
  completeness: number;
  validity: number;
  uniqueness: number;
  consistency: number;
  accuracy: number;
  freshness: number;
}

export interface QualitySummary {
  overall_score: number;
  dimensions: DimensionScores;
  passed_rules: number;
  failed_rules: number;
  total_rules: number;
  active_issues: number;
  critical_issues: number;
  freshness_hours: number;
}

export interface QualityRule {
  id: string;
  rule_code: string;
  name: string;
  dimension: keyof DimensionScores;
  column_name: string;
  description: string;
  threshold: number;
  status: 'PASSED' | 'FAILED' | 'PENDING';
  severity: IssueSeverity;
  last_evaluated: string;
}

export interface QualityIssue {
  id: string;
  dataset_name: string;
  rule_code: string;
  column_name: string;
  severity: IssueSeverity;
  status: IssueStatus;
  description: string;
  failed_count: number;
  assignee?: string;
  created_at: string;
}

export interface RemediationAction {
  id: string;
  issue_id: string;
  action_type: 'TRIM_WHITESPACE' | 'IMPUTE_NULLS' | 'DEDUPLICATE' | 'NORMALIZE_DATES' | 'STANDARDIZE_PHONE';
  dataset_name: string;
  column_name: string;
  status: 'PENDING' | 'EXECUTED' | 'REVERTED';
  affected_rows: number;
  executed_at?: string;
}

export interface GlossaryTerm {
  id: string;
  term: string;
  domain: DomainType;
  definition: string;
  synonyms: string[];
  governance_steward: string;
  linked_columns: string[];
  status: 'APPROVED' | 'DRAFT' | 'DEPRECATED';
}

export interface LineageNode {
  id: string;
  label: string;
  type: 'SOURCE' | 'BRONZE' | 'SILVER' | 'GOLD' | 'BI';
  domain: string;
  tier: number; // 0 for source, 1 bronze, 2 silver, 3 gold, 4 bi
  records: number;
  health: number; // 0 - 100
}

export interface LineageEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

export interface LineageGraph {
  nodes: LineageNode[];
  edges: LineageEdge[];
}

export interface DataContract {
  id: string;
  dataset_name: string;
  version: string;
  owner: string;
  sla_freshness_hours: number;
  status: 'ACTIVE' | 'DRAFT' | 'VIOLATED';
  schema_columns: {
    name: string;
    type: string;
    nullable: boolean;
    pii: boolean;
  }[];
  last_validated: string;
}

export interface DriftEvent {
  id: string;
  dataset_name: string;
  drift_type: 'COLUMN_ADDED' | 'COLUMN_DROPPED' | 'TYPE_MISMATCH' | 'NULLABILITY_CHANGED';
  detail: string;
  detected_at: string;
  severity: IssueSeverity;
}

export interface ComplianceControl {
  framework: 'GDPR' | 'HIPAA' | 'SOC2' | 'ISO27001';
  control_id: string;
  name: string;
  description: string;
  status: 'COMPLIANT' | 'NEEDS_REVIEW' | 'NON_COMPLIANT';
  affected_assets_count: number;
}

export interface MLAnomaly {
  id: string;
  dataset_name: string;
  column_name: string;
  metric_name: string;
  detected_value: number;
  expected_range: [number, number];
  z_score: number;
  timestamp: string;
  is_anomaly: boolean;
}

export interface MLRuleRecommendation {
  id: string;
  dataset_name: string;
  column_name: string;
  suggested_rule: string;
  dimension: string;
  confidence: number;
  reason: string;
}
