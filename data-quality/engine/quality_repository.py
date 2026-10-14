import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.catalog import Dataset
from backend.app.models.quality import QualityRule, QualityResult, QualityIssue
from data_quality.rules.rule_definitions import QualityRuleSpec, QualityEvaluationResult

logger = logging.getLogger("QualityRepository")


class QualityRepository:

    @staticmethod
    def save_rule_and_result(
        db_session: Session,
        rule_spec: QualityRuleSpec,
        result: QualityEvaluationResult,
    ) -> QualityResult:
        dataset = db_session.query(Dataset).filter_by(dataset_name=rule_spec.dataset_name).first()
        if not dataset:
            dataset = Dataset(
                dataset_name=rule_spec.dataset_name,
                description=f"Auto-registered dataset for {rule_spec.dataset_name}",
                domain="General",
                source_system="IngestionPlatform",
                location=f"data/lake/bronze/{rule_spec.dataset_name}",
            )
            db_session.add(dataset)
            db_session.flush()

        # Save or update QualityRule
        rule_record = db_session.query(QualityRule).filter_by(rule_id=rule_spec.rule_id).first()
        if not rule_record:
            rule_record = QualityRule(
                rule_id=rule_spec.rule_id,
                rule_name=rule_spec.rule_name,
                dataset_id=dataset.id,
                column_name=rule_spec.column_name,
                rule_type=rule_spec.rule_type,
                rule_expression=rule_spec.rule_expression,
                severity=rule_spec.severity,
                category=rule_spec.category,
                owner=rule_spec.owner,
                enabled=rule_spec.enabled,
            )
            db_session.add(rule_record)
            db_session.flush()

        # Save QualityResult
        eval_result_record = QualityResult(
            rule_id=rule_record.id,
            dataset_id=dataset.id,
            passed=result.passed,
            total_records=result.total_records,
            failed_records=result.failed_records,
            pass_rate=result.pass_rate,
            execution_time_ms=result.execution_time_ms,
            details={"failed_examples_count": len(result.failed_examples)},
        )
        db_session.add(eval_result_record)

        # Auto-create QualityIssue if rule evaluation failed
        if not result.passed:
            issue_id = f"ISS-{rule_spec.rule_id}"
            existing_issue = db_session.query(QualityIssue).filter_by(issue_id=issue_id, status="OPEN").first()
            if not existing_issue:
                new_issue = QualityIssue(
                    issue_id=issue_id,
                    dataset_id=dataset.id,
                    column_name=rule_spec.column_name,
                    rule_id=rule_record.id,
                    severity=rule_spec.severity,
                    description=f"Quality rule '{rule_spec.rule_name}' failed on column '{rule_spec.column_name}'. Failed records: {result.failed_records}/{result.total_records} ({100.0 - result.pass_rate:.1f}% error rate).",
                    status="OPEN",
                    owner=rule_spec.owner,
                )
                db_session.add(new_issue)

        db_session.commit()
        db_session.refresh(eval_result_record)
        logger.info(f"Persisted result for rule '{rule_spec.rule_id}' on dataset '{rule_spec.dataset_name}' (Passed: {result.passed}, Pass Rate: {result.pass_rate}%).")
        return eval_result_record
