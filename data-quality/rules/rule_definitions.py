from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List


@dataclass
class QualityRuleSpec:
    rule_id: str
    rule_name: str
    dataset_name: str
    column_name: Optional[str]
    rule_type: str  # NOT_NULL, UNIQUE, VALID_FORMAT, REGEX, RANGE, REFERENTIAL_INTEGRITY, ACCEPTED_VALUES, DATE_VALIDATION, CUSTOM_SQL, CUSTOM_PYTHON, FRESHNESS, DUPLICATE, SCHEMA, BUSINESS_RULE
    rule_expression: Optional[str] = None
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    category: str = "TECHNICAL"  # TECHNICAL vs BUSINESS
    owner: str = "Data Quality Team"
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityEvaluationResult:
    rule_id: str
    rule_name: str
    dataset_name: str
    passed: bool
    total_records: int
    failed_records: int
    pass_rate: float
    execution_time_ms: float
    evaluated_at: str
    failed_examples: List[Dict[str, Any]] = field(default_factory=list)
