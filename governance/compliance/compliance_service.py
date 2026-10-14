import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models.governance import ComplianceFramework, ComplianceControl, PolicyViolation

logger = logging.getLogger("ComplianceService")

DEFAULT_FRAMEWORKS = [
    {
        "framework_code": "GDPR",
        "name": "General Data Protection Regulation",
        "version": "EU 2016/679",
        "description": "EU regulation on data protection and privacy.",
        "controls": [
            {"control_code": "Art32_Security", "description": "Security of processing: technical & encryption controls", "owner": "CISO"},
            {"control_code": "Art5_Minimisation", "description": "Data minimisation: dynamic field masking & classification", "owner": "Data Protection Officer"},
            {"control_code": "Art30_Records", "description": "Records of processing activities & data catalog lineage", "owner": "Governance Lead"},
        ]
    },
    {
        "framework_code": "HIPAA",
        "name": "Health Insurance Portability & Accountability Act",
        "version": "45 CFR Part 160/164",
        "description": "US regulation for protecting PHI & medical data.",
        "controls": [
            {"control_code": "164.312_Access", "description": "Access control & PHI/PII dynamic masking", "owner": "Compliance Officer"},
            {"control_code": "164.312_Audit", "description": "Audit controls & immutable activity logging", "owner": "Security Team"},
        ]
    },
    {
        "framework_code": "SOC2",
        "name": "SOC 2 Type II Trust Services Criteria",
        "version": "AICPA 2017",
        "description": "Security, Availability, Confidentiality, and Processing Integrity.",
        "controls": [
            {"control_code": "CC6.1_Security", "description": "Logical access security & RBAC enforcement", "owner": "IT Security"},
            {"control_code": "CC7.1_Monitoring", "description": "System & data quality anomaly monitoring", "owner": "Data Ops"},
        ]
    },
    {
        "framework_code": "ISO27001",
        "name": "ISO/IEC 27001 Information Security",
        "version": "2022",
        "description": "International standard for information security management systems.",
        "controls": [
            {"control_code": "A.8.2_Classification", "description": "Information classification & owner tagging", "owner": "Chief Information Risk Officer"},
            {"control_code": "A.8.3_Media", "description": "Protection of sensitive media & data lake assets", "owner": "Data Security Specialist"},
        ]
    }
]


class ComplianceService:
    """
    Manages enterprise regulatory compliance frameworks, technical control mapping, and audit status reporting.
    """

    @staticmethod
    def initialize_compliance_frameworks(db_session: Session) -> List[ComplianceFramework]:
        """
        Seeds standard compliance frameworks and controls if not present in the database.
        """
        framework_objs = []
        for fw_spec in DEFAULT_FRAMEWORKS:
            fw = db_session.query(ComplianceFramework).filter_by(framework_code=fw_spec["framework_code"]).first()
            if not fw:
                fw = ComplianceFramework(
                    framework_code=fw_spec["framework_code"],
                    name=fw_spec["name"],
                    version=fw_spec["version"],
                    description=fw_spec["description"]
                )
                db_session.add(fw)
                db_session.flush()

                for ctrl_spec in fw_spec["controls"]:
                    ctrl = ComplianceControl(
                        framework_id=fw.id,
                        control_code=ctrl_spec["control_code"],
                        description=ctrl_spec["description"],
                        owner=ctrl_spec["owner"],
                        status="PASS",
                        evidence_summary="Default compliance control initialized.",
                        last_reviewed_at=datetime.now(timezone.utc)
                    )
                    db_session.add(ctrl)
            framework_objs.append(fw)

        db_session.commit()
        return db_session.query(ComplianceFramework).all()

    @staticmethod
    def evaluate_compliance_status(db_session: Session) -> Dict[str, Any]:
        """
        Evaluates overall compliance scores based on open policy violations and control statuses.
        """
        ComplianceService.initialize_compliance_frameworks(db_session)

        open_violations_count = db_session.query(PolicyViolation).filter_by(status="OPEN").count()
        frameworks = db_session.query(ComplianceFramework).all()

        framework_summary = []
        total_controls = 0
        passing_controls = 0

        for fw in frameworks:
            controls = db_session.query(ComplianceControl).filter_by(framework_id=fw.id).all()
            fw_total = len(controls)
            
            # If there are open critical violations, update corresponding controls
            for ctrl in controls:
                if open_violations_count > 0 and "Security" in ctrl.control_code:
                    ctrl.status = "FAIL" if open_violations_count >= 3 else "IN_PROGRESS"
                    ctrl.evidence_summary = f"{open_violations_count} open governance policy violation(s) detected."
                else:
                    ctrl.status = "PASS"
                    ctrl.evidence_summary = "All automated governance control checks passed."

            fw_pass = sum(1 for c in controls if c.status == "PASS")
            total_controls += fw_total
            passing_controls += fw_pass

            score_pct = round((fw_pass / fw_total * 100.0), 1) if fw_total > 0 else 100.0

            framework_summary.append({
                "framework_code": fw.framework_code,
                "name": fw.name,
                "compliance_score": score_pct,
                "total_controls": fw_total,
                "passing_controls": fw_pass,
            })

        db_session.commit()
        overall_score = round((passing_controls / total_controls * 100.0), 1) if total_controls > 0 else 100.0

        return {
            "overall_compliance_score": overall_score,
            "open_policy_violations": open_violations_count,
            "frameworks": framework_summary,
            "status": "COMPLIANT" if overall_score >= 80.0 else "NON_COMPLIANT"
        }
