import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("PIIClassifier")

# Regex patterns for column names
COLUMN_PATTERNS = {
    "SSN": [r"ssn", r"social_security", r"tax_id"],
    "EMAIL": [r"email", r"e_mail", r"mail_addr"],
    "PHONE": [r"phone", r"mobile", r"cell", r"telephone", r"fax"],
    "CREDIT_CARD": [r"credit_card", r"card_num", r"cc_num", r"pan", r"cvv"],
    "NAME": [r"first_name", r"last_name", r"full_name", r"surname", r"person_name"],
    "ADDRESS": [r"street", r"address", r"postal_code", r"zipcode"],
    "DOB": [r"dob", r"birth_date", r"date_of_birth"],
    "IP_ADDRESS": [r"ip_addr", r"ip_address", r"ipv4", r"ipv6"],
    "SALARY": [r"salary", r"compensation", r"income", r"bank_account", r"iban"],
}

# Regex patterns for string value sample matching
VALUE_PATTERNS = {
    "SSN": r"^\d{3}-\d{2}-\d{4}$",
    "EMAIL": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "PHONE": r"^\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}$",
    "CREDIT_CARD": r"^\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}$",
    "IP_ADDRESS": r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
}


class PIIClassifier:
    """
    Automated PII & Sensitive Data Classifier based on column heuristics & value regex inspection.
    """

    @staticmethod
    def classify_column(
        column_name: str,
        sample_values: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        col_lower = column_name.lower().strip()

        # 1. Check Column Name Heuristics
        for pii_type, patterns in COLUMN_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, col_lower):
                    classification = "PII" if pii_type in ("SSN", "EMAIL", "PHONE", "CREDIT_CARD", "NAME", "DOB") else "CONFIDENTIAL"
                    return {
                        "classification": classification,
                        "pii_type": pii_type,
                        "confidence": 0.90,
                        "method": "COLUMN_HEURISTIC"
                    }

        # 2. Check Sample Value Heuristics if provided
        if sample_values:
            non_null_samples = [str(v) for v in sample_values if v is not None and str(v).strip() != ""]
            if non_null_samples:
                for pii_type, val_pattern in VALUE_PATTERNS.items():
                    matches = sum(1 for s in non_null_samples if re.match(val_pattern, s))
                    match_rate = matches / len(non_null_samples)
                    if match_rate >= 0.5:
                        classification = "PII" if pii_type in ("SSN", "EMAIL", "PHONE", "CREDIT_CARD") else "CONFIDENTIAL"
                        return {
                            "classification": classification,
                            "pii_type": pii_type,
                            "confidence": round(match_rate, 2),
                            "method": "VALUE_REGEX"
                        }

        return {
            "classification": "INTERNAL",
            "pii_type": None,
            "confidence": 1.0,
            "method": "DEFAULT"
        }

    @staticmethod
    def classify_dataset(
        records: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Classifies all columns in a dataset.
        """
        if not records:
            return {}

        column_names = list(records[0].keys())
        classification_results = {}

        for col in column_names:
            samples = [row.get(col) for row in records[:50]]  # Sample up to 50 rows
            classification_results[col] = PIIClassifier.classify_column(col, samples)

        return classification_results
