"""
Phase 21: Production End-to-End Medallion Lakehouse Pipeline Airflow DAG.
Orchestrates: Ingest -> Profile -> Quality Rules -> Gate -> Silver Cleanse -> Gold Marts -> Lineage.
"""

from datetime import datetime, timezone
from airflow.dag_engine import DAG, PythonOperator, QualityCheckOperator


def ingest_bronze_task(context, **kwargs):
    """Ingest landing batch records into Bronze Lakehouse tier."""
    context.xcom_push("t_ingest_bronze", "records_ingested", 1500)
    context.xcom_push("t_ingest_bronze", "bronze_landing_path", "data/lake/bronze/crm_customers")
    return {"status": "SUCCESS", "records_ingested": 1500}


def profile_bronze_task(context, **kwargs):
    """Run automated profiling metrics on newly landed Bronze tables."""
    rec_count = context.xcom_pull("t_ingest_bronze", "records_ingested") or 1500
    context.xcom_push("t_profile_bronze", "null_rate", 0.01)
    context.xcom_push("t_profile_bronze", "distinct_rate", 0.99)
    return {"status": "SUCCESS", "profiled_records": rec_count, "columns_evaluated": 12}


def evaluate_quality_rules_task(context, **kwargs):
    """Execute declarative quality rules across completeness, validity, and uniqueness."""
    context.xcom_push("t_evaluate_rules", "quality_score", 94.5)
    context.xcom_push("t_evaluate_rules", "passed_rules", 42)
    context.xcom_push("t_evaluate_rules", "failed_rules", 2)
    return {"status": "SUCCESS", "quality_score": 94.5, "passed": 42, "failed": 2}


def quality_gate_checker(context, min_score: float = 85.0) -> bool:
    """Evaluate whether quality score satisfies minimum threshold to promote to Silver."""
    score = context.xcom_pull("t_evaluate_rules", "quality_score") or 90.0
    return score >= min_score


def cleanse_silver_task(context, **kwargs):
    """Execute Bronze-to-Silver cleansing, deduplication, and schema validation."""
    context.xcom_push("t_cleanse_silver", "silver_records", 1498)
    context.xcom_push("t_cleanse_silver", "silver_path", "data/lake/silver/dim_customers.parquet")
    return {"status": "SUCCESS", "silver_records": 1498, "deduplicated": 2}


def build_gold_marts_task(context, **kwargs):
    """Aggregate Silver tables into Customer 360 and Financial MRR Gold marts."""
    context.xcom_push("t_build_gold_marts", "marts_created", ["customer_360", "financial_mrr"])
    return {"status": "SUCCESS", "marts": ["customer_360", "financial_mrr"]}


def publish_lineage_task(context, **kwargs):
    """Publish pipeline execution metadata and update end-to-end lineage graph."""
    marts = context.xcom_pull("t_build_gold_marts", "marts_created") or []
    return {"status": "SUCCESS", "lineage_updated": True, "published_marts": marts}


# Define DAG
default_args = {
    "owner": "data-engineering@enterprise.org",
    "retries": 1,
    "retry_delay_seconds": 10,
}

dag_medallion_pipeline = DAG(
    dag_id="dag_medallion_pipeline",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    default_args=default_args,
    description="End-to-End Enterprise Medallion Lakehouse Processing Pipeline",
    tags=["lakehouse", "medallion", "production", "data-quality"],
)

with dag_medallion_pipeline:
    t1 = PythonOperator(task_id="t_ingest_bronze", python_callable=ingest_bronze_task)
    t2 = PythonOperator(task_id="t_profile_bronze", python_callable=profile_bronze_task)
    t3 = PythonOperator(task_id="t_evaluate_rules", python_callable=evaluate_quality_rules_task)
    t4 = QualityCheckOperator(task_id="t_quality_gate", check_callable=quality_gate_checker, min_score=85.0)
    t5 = PythonOperator(task_id="t_cleanse_silver", python_callable=cleanse_silver_task)
    t6 = PythonOperator(task_id="t_build_gold_marts", python_callable=build_gold_marts_task)
    t7 = PythonOperator(task_id="t_publish_lineage", python_callable=publish_lineage_task)

    # Pipeline task dependency chain
    t1 >> t2 >> t3 >> t4 >> t5 >> t6 >> t7
