import re
import copy
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models.catalog import Dataset
from backend.app.models.quality import QualityIssue, RemediationAction

logger = logging.getLogger("RemediationEngine")


class RemediationEngine:
    """
    Deterministic data quality remediation functions for structured datasets.
    """

    @staticmethod
    def trim_whitespace(
        records: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Trims leading and trailing whitespace from string columns.
        """
        cleaned_records = []
        affected_rows = 0

        for row in records:
            row_copy = copy.deepcopy(row)
            row_modified = False

            target_cols = columns if columns is not None else list(row_copy.keys())

            for col in target_cols:
                val = row_copy.get(col)
                if isinstance(val, str):
                    trimmed = val.strip()
                    if trimmed != val:
                        row_copy[col] = trimmed
                        row_modified = True

            if row_modified:
                affected_rows += 1
            cleaned_records.append(row_copy)

        return cleaned_records, affected_rows

    @staticmethod
    def normalize_case(
        records: List[Dict[str, Any]],
        column_case_map: Dict[str, str]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Normalizes case for string columns. Supported case modes: 'upper', 'lower', 'title'.
        column_case_map example: {'email': 'lower', 'state': 'upper', 'name': 'title'}
        """
        cleaned_records = []
        affected_rows = 0

        for row in records:
            row_copy = copy.deepcopy(row)
            row_modified = False

            for col, mode in column_case_map.items():
                if col not in row_copy:
                    continue
                val = row_copy.get(col)
                if isinstance(val, str) and val:
                    mode_lower = mode.lower()
                    if mode_lower == "upper":
                        new_val = val.upper()
                    elif mode_lower == "lower":
                        new_val = val.lower()
                    elif mode_lower == "title":
                        new_val = val.title()
                    else:
                        new_val = val

                    if new_val != val:
                        row_copy[col] = new_val
                        row_modified = True

            if row_modified:
                affected_rows += 1
            cleaned_records.append(row_copy)

        return cleaned_records, affected_rows

    @staticmethod
    def format_phone_numbers(
        records: List[Dict[str, Any]],
        column_name: str,
        format_spec: str = "STANDARD"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Standardizes phone numbers into normalized format (e.g. +1-XXX-XXX-XXXX or (XXX) XXX-XXXX).
        """
        cleaned_records = []
        affected_rows = 0

        for row in records:
            row_copy = copy.deepcopy(row)
            val = row_copy.get(column_name)

            if isinstance(val, str) and val:
                digits = re.sub(r"\D", "", val)
                if len(digits) == 10:
                    formatted = f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
                elif len(digits) == 11 and digits.startswith("1"):
                    formatted = f"+1-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
                else:
                    formatted = val  # Keep original if non-standard length

                if formatted != val:
                    row_copy[column_name] = formatted
                    affected_rows += 1

            cleaned_records.append(row_copy)

        return cleaned_records, affected_rows

    @staticmethod
    def standardize_country_codes(
        records: List[Dict[str, Any]],
        column_name: str,
        target_format: str = "ALPHA-3"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Standardizes country names/aliases to ISO alpha-3 code (e.g., 'USA', 'CAN', 'GBR', 'DEU').
        """
        country_map = {
            "us": "USA", "usa": "USA", "united states": "USA", "united states of america": "USA",
            "uk": "GBR", "gbr": "GBR", "united kingdom": "GBR", "england": "GBR",
            "ca": "CAN", "can": "CAN", "canada": "CAN",
            "de": "DEU", "deu": "DEU", "germany": "DEU", "deutschland": "DEU",
            "fr": "FRA", "fra": "FRA", "france": "FRA",
            "in": "IND", "ind": "IND", "india": "IND",
            "jp": "JPN", "jpn": "JPN", "japan": "JPN",
            "au": "AUS", "aus": "AUS", "australia": "AUS",
        }

        cleaned_records = []
        affected_rows = 0

        for row in records:
            row_copy = copy.deepcopy(row)
            val = row_copy.get(column_name)

            if isinstance(val, str) and val:
                key = val.strip().lower()
                std_code = country_map.get(key, val)
                if std_code != val:
                    row_copy[column_name] = std_code
                    affected_rows += 1

            cleaned_records.append(row_copy)

        return cleaned_records, affected_rows

    @staticmethod
    def fill_defaults(
        records: List[Dict[str, Any]],
        defaults_map: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Fills null/empty/missing values with column defaults.
        defaults_map example: {'status': 'ACTIVE', 'country': 'USA', 'age': 0}
        """
        cleaned_records = []
        affected_rows = 0

        for row in records:
            row_copy = copy.deepcopy(row)
            row_modified = False

            for col, default_val in defaults_map.items():
                val = row_copy.get(col)
                is_missing = (
                    val is None or
                    (isinstance(val, str) and val.strip().upper() in ("", "NULL", "N/A", "NONE", "NAN"))
                )

                if is_missing:
                    row_copy[col] = default_val
                    row_modified = True

            if row_modified:
                affected_rows += 1
            cleaned_records.append(row_copy)

        return cleaned_records, affected_rows

    @staticmethod
    def deduplicate_records(
        records: List[Dict[str, Any]],
        key_columns: Optional[List[str]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Deduplicates records based on key_columns (or all fields if key_columns is None).
        Returns deduplicated list and count of dropped duplicate records.
        """
        seen = set()
        deduped = []
        dropped_count = 0

        for row in records:
            if key_columns:
                key_tuple = tuple(str(row.get(col)) for col in key_columns)
            else:
                key_tuple = tuple(sorted((k, str(v)) for k, v in row.items()))

            if key_tuple in seen:
                dropped_count += 1
            else:
                seen.add(key_tuple)
                deduped.append(row)

        return deduped, dropped_count


class RemediationService:
    """
    Orchestrates automated remediation actions, dataset updates, and database logging.
    """

    @staticmethod
    def execute_remediation_action(
        db_session: Session,
        dataset_name: str,
        action_type: str,
        records: List[Dict[str, Any]],
        params: Optional[Dict[str, Any]] = None,
        issue_id: Optional[str] = None,
        executed_by: str = "AUTOMATED_ENGINE"
    ) -> Tuple[List[Dict[str, Any]], RemediationAction]:
        """
        Executes specified remediation type on records, updates database logs, and resolves linked issue if applicable.
        """
        params = params or {}
        action_upper = action_type.upper()

        if action_upper == "TRIM_WHITESPACE":
            cols = params.get("columns")
            cleaned_records, affected_rows = RemediationEngine.trim_whitespace(records, columns=cols)
            col_name = ", ".join(cols) if cols else "ALL"

        elif action_upper == "CASE_NORMALIZE":
            column_case_map = params.get("column_case_map", {})
            cleaned_records, affected_rows = RemediationEngine.normalize_case(records, column_case_map)
            col_name = ", ".join(column_case_map.keys())

        elif action_upper == "PHONE_NORMALIZE":
            col_name = params.get("column_name", "phone")
            cleaned_records, affected_rows = RemediationEngine.format_phone_numbers(records, column_name=col_name)

        elif action_upper == "COUNTRY_NORMALIZE":
            col_name = params.get("column_name", "country")
            cleaned_records, affected_rows = RemediationEngine.standardize_country_codes(records, column_name=col_name)

        elif action_upper == "FILL_DEFAULT":
            defaults_map = params.get("defaults_map", {})
            cleaned_records, affected_rows = RemediationEngine.fill_defaults(records, defaults_map)
            col_name = ", ".join(defaults_map.keys())

        elif action_upper == "DEDUPLICATE":
            keys = params.get("key_columns")
            cleaned_records, affected_rows = RemediationEngine.deduplicate_records(records, key_columns=keys)
            col_name = ", ".join(keys) if keys else "ALL_FIELDS"

        else:
            raise ValueError(f"Unsupported remediation action_type '{action_type}'.")

        # Resolve or create Dataset in DB catalog
        dataset = db_session.query(Dataset).filter_by(dataset_name=dataset_name).first()
        if not dataset:
            dataset = Dataset(
                dataset_name=dataset_name,
                domain="General",
                source_system="RemediationEngine",
                location=f"data/lake/silver/{dataset_name}"
            )
            db_session.add(dataset)
            db_session.flush()

        # Check issue if provided
        issue_obj = None
        if issue_id:
            issue_obj = db_session.query(QualityIssue).filter_by(issue_id=issue_id).first()

        remediation_record = RemediationAction(
            issue_id=issue_obj.id if issue_obj else None,
            dataset_id=dataset.id,
            column_name=col_name,
            action_type=action_upper,
            affected_rows=affected_rows,
            executed_by=executed_by,
            details={
                "params": params,
                "initial_row_count": len(records),
                "final_row_count": len(cleaned_records),
            }
        )
        db_session.add(remediation_record)

        # If issue was linked and remediation was applied, resolve issue
        if issue_obj and issue_obj.status in ("OPEN", "IN_PROGRESS"):
            issue_obj.status = "RESOLVED"
            issue_obj.resolution_notes = f"Auto-remediated via action '{action_upper}'. Affected rows: {affected_rows}."
            issue_obj.resolved_at = db_session.query(QualityIssue).filter_by(issue_id=issue_id).first().detected_at

        db_session.commit()
        db_session.refresh(remediation_record)

        logger.info(f"Remediation '{action_upper}' executed on dataset '{dataset_name}'. Affected rows: {affected_rows}.")
        return cleaned_records, remediation_record
