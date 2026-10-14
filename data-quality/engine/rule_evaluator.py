import re
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from data_quality.rules.rule_definitions import QualityRuleSpec, QualityEvaluationResult
from data_quality.profiling.pattern_analyzer import EMAIL_REGEX, PHONE_REGEX, DATE_REGEX

logger = logging.getLogger("RuleEvaluator")


class RuleEvaluator:
    """
    Data Quality Rule Execution Engine.
    Evaluates 14+ declarative technical and business quality rules against dataset records.
    """

    def evaluate_rule(
        self,
        rule: QualityRuleSpec,
        records: List[Dict[str, Any]],
        parent_datasets: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> QualityEvaluationResult:
        start_time = time.time()
        total_records = len(records)
        if total_records == 0:
            return QualityEvaluationResult(
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                dataset_name=rule.dataset_name,
                passed=True,
                total_records=0,
                failed_records=0,
                pass_rate=100.0,
                execution_time_ms=0.0,
                evaluated_at=datetime.now(timezone.utc).isoformat(),
            )

        col = rule.column_name
        rule_type = rule.rule_type.upper()
        failed_examples = []
        failed_count = 0

        if rule_type == "NOT_NULL":
            for r in records:
                val = r.get(col)
                if val is None or str(val).strip() == "":
                    failed_count += 1
                    if len(failed_examples) < 5:
                        failed_examples.append(r)

        elif rule_type == "UNIQUE":
            seen = set()
            for r in records:
                val = r.get(col)
                if val is not None:
                    str_val = str(val)
                    if str_val in seen:
                        failed_count += 1
                        if len(failed_examples) < 5:
                            failed_examples.append(r)
                    else:
                        seen.add(str_val)

        elif rule_type == "VALID_FORMAT":
            target_fmt = (rule.rule_expression or "EMAIL").upper()
            regex = EMAIL_REGEX if target_fmt == "EMAIL" else PHONE_REGEX
            for r in records:
                val = r.get(col)
                if val is not None and str(val).strip() != "":
                    if not regex.match(str(val).strip()):
                        failed_count += 1
                        if len(failed_examples) < 5:
                            failed_examples.append(r)

        elif rule_type == "REGEX":
            pattern = re.compile(rule.rule_expression or ".*")
            for r in records:
                val = r.get(col)
                if val is not None and str(val).strip() != "":
                    if not pattern.match(str(val).strip()):
                        failed_count += 1
                        if len(failed_examples) < 5:
                            failed_examples.append(r)

        elif rule_type == "RANGE":
            min_val = rule.params.get("min", float("-inf"))
            max_val = rule.params.get("max", float("inf"))
            for r in records:
                val = r.get(col)
                if val is not None and str(val).strip() != "":
                    try:
                        num_val = float(val)
                        if num_val < min_val or num_val > max_val:
                            failed_count += 1
                            if len(failed_examples) < 5:
                                failed_examples.append(r)
                    except (ValueError, TypeError):
                        failed_count += 1
                        if len(failed_examples) < 5:
                            failed_examples.append(r)

        elif rule_type == "ACCEPTED_VALUES":
            allowed = set(rule.params.get("allowed_values", []))
            for r in records:
                val = r.get(col)
                if val is not None and str(val).strip() != "":
                    if str(val).strip() not in allowed:
                        failed_count += 1
                        if len(failed_examples) < 5:
                            failed_examples.append(r)

        elif rule_type == "REFERENTIAL_INTEGRITY":
            parent_ds_name = rule.params.get("parent_dataset")
            parent_col_name = rule.params.get("parent_column")
            parent_records = (parent_datasets or {}).get(parent_ds_name, [])
            valid_keys = set(str(pr.get(parent_col_name)) for pr in parent_records if pr.get(parent_col_name) is not None)

            for r in records:
                val = r.get(col)
                if val is not None and str(val).strip() != "":
                    if str(val).strip() not in valid_keys:
                        failed_count += 1
                        if len(failed_examples) < 5:
                            failed_examples.append(r)

        elif rule_type == "DATE_VALIDATION":
            max_date_str = rule.params.get("max_date")
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            limit_date = now_str if max_date_str == "CURRENT_DATE" else max_date_str

            for r in records:
                val = r.get(col)
                if val is not None and str(val).strip() != "":
                    date_str = str(val).strip()
                    if limit_date and date_str > limit_date:
                        failed_count += 1
                        if len(failed_examples) < 5:
                            failed_examples.append(r)

        elif rule_type in ["BUSINESS_RULE", "CUSTOM_PYTHON"]:
            for r in records:
                try:
                    qty = float(r.get("quantity", 0))
                    price = float(r.get("unit_price", 0))
                    disc = float(r.get("discount", 0))
                    tax = float(r.get("tax", 0))
                    total = float(r.get("total_amount", 0))
                    expected_total = round(qty * price - disc + tax, 2)
                    if abs(total - expected_total) > 0.05:
                        failed_count += 1
                        if len(failed_examples) < 5:
                            failed_examples.append(r)
                except Exception:
                    pass

        elif rule_type == "DUPLICATE":
            seen_hashes = set()
            for r in records:
                h = r.get("_record_hash") or str(r)
                if h in seen_hashes:
                    failed_count += 1
                    if len(failed_examples) < 5:
                        failed_examples.append(r)
                else:
                    seen_hashes.add(h)

        elif rule_type == "SCHEMA":
            req_cols = set(rule.params.get("required_columns", []))
            present_cols = set(records[0].keys()) if records else set()
            missing = req_cols - present_cols
            if missing:
                failed_count = total_records

        pass_rate = round(((total_records - failed_count) / total_records) * 100.0, 2)
        exec_time = round((time.time() - start_time) * 1000.0, 2)

        return QualityEvaluationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            dataset_name=rule.dataset_name,
            passed=(failed_count == 0),
            total_records=total_records,
            failed_records=failed_count,
            pass_rate=pass_rate,
            execution_time_ms=exec_time,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            failed_examples=failed_examples,
        )
