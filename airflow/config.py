"""
Phase 21: Airflow Orchestration Configuration.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class AirflowOrchestratorConfig:
    """Enterprise Airflow Orchestrator Configuration."""

    dags_folder: str = field(
        default_factory=lambda: os.getenv("AIRFLOW_DAGS_FOLDER", "airflow/dags")
    )
    default_owner: str = "data-engineering@enterprise.org"
    sla_timeout_seconds: int = 3600  # 1 hour default SLA
    retry_delay_seconds: int = 300
    default_retries: int = 2
    alert_channel: str = "#data-pipeline-alerts"
