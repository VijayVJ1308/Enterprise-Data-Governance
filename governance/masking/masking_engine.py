import hashlib
import copy
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("DataMaskingEngine")

UNMASKED_ROLES = {"ADMIN", "DATA_GOVERNANCE_ADMIN", "DATA_STEWARD", "SYSTEM"}


class DataMaskingEngine:
    """
    Dynamic Data Masking Engine supporting FULL, PARTIAL, and HASH masking strategies.
    """

    @staticmethod
    def mask_value(
        val: Any,
        pii_type: Optional[str] = None,
        strategy: str = "PARTIAL",
        salt: str = "governance_salt"
    ) -> Any:
        if val is None or str(val).strip() == "":
            return val

        str_val = str(val)
        strat_upper = strategy.upper()

        if strat_upper == "FULL":
            return "***MASKED***"

        if strat_upper == "HASH":
            salted = f"{salt}:{str_val}"
            return hashlib.sha256(salted.encode("utf-8")).hexdigest()[:16]

        if strat_upper == "PARTIAL":
            pii_upper = (pii_type or "").upper()

            if pii_upper == "EMAIL" and "@" in str_val:
                parts = str_val.split("@", 1)
                user = parts[0]
                domain = parts[1]
                masked_user = user[0] + "***" if len(user) > 1 else "*"
                return f"{masked_user}@{domain}"

            if pii_upper == "PHONE" and len(str_val) >= 4:
                return f"***-***-{str_val[-4:]}"

            if pii_upper == "SSN" and len(str_val) >= 4:
                return f"***-**-{str_val[-4:]}"

            if pii_upper == "CREDIT_CARD" and len(str_val) >= 4:
                return f"****-****-****-{str_val[-4:]}"

            # Default generic partial mask
            if len(str_val) <= 4:
                return "****"
            return str_val[0] + "*" * (len(str_val) - 2) + str_val[-1]

        return str_val

    @staticmethod
    def mask_records(
        records: List[Dict[str, Any]],
        column_classifications: Dict[str, Dict[str, Any]],
        strategy_override: Optional[Dict[str, str]] = None,
        user_role: str = "DATA_ANALYST"
    ) -> List[Dict[str, Any]]:
        """
        Applies dynamic field masking based on column sensitivity and user role.
        """
        if user_role.upper() in UNMASKED_ROLES:
            logger.info(f"User role '{user_role}' has full unmasked data access.")
            return records

        strategy_override = strategy_override or {}
        masked_records = []

        for row in records:
            row_copy = copy.deepcopy(row)
            for col, class_info in column_classifications.items():
                if col not in row_copy:
                    continue

                classification = class_info.get("classification", "INTERNAL")
                pii_type = class_info.get("pii_type")

                if classification in ("PII", "CONFIDENTIAL", "RESTRICTED"):
                    strat = strategy_override.get(col, "PARTIAL")
                    row_copy[col] = DataMaskingEngine.mask_value(
                        row_copy[col],
                        pii_type=pii_type,
                        strategy=strat
                    )

            masked_records.append(row_copy)

        return masked_records
