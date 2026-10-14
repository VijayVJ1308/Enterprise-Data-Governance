"""
Phase 21: Airflow DAG Orchestration & dbt Data Modeling Tests.

Tests:
1. Airflow DAG Instantiation, Topology & Bitshift Dependencies
2. Airflow End-to-End Medallion Pipeline DAG Run & XCom Pass-through
3. Airflow Quality Gate Operator Branching / Failure Assertion
4. Airflow Hourly Freshness SLA Monitor DAG Run
5. dbt Project & Profiles YAML Validation
6. dbt Model Compilation, Staging & Mart Materialization
7. dbt Declarative Schema Tests (unique, not_null, accepted_values)
8. dbt Schema Test Failure Detection on Injected Violations
"""

import os
import unittest
import pandas as pd

from airflow.dag_engine import DAG, PythonOperator, QualityCheckOperator, DagRunContext
from airflow.dags.dag_medallion_pipeline import dag_medallion_pipeline
from airflow.dags.dag_quality_sla_monitor import dag_quality_sla_monitor
from dbt.runner import DbtRunner


class TestPhase21AirflowDbt(unittest.TestCase):

    def test_airflow_dag_instantiation_and_topology(self):
        dag = dag_medallion_pipeline
        self.assertEqual(dag.dag_id, "dag_medallion_pipeline")
        self.assertEqual(dag.schedule_interval, "@daily")
        self.assertEqual(len(dag.tasks), 7)
        self.assertIn("lakehouse", dag.tags)

        # Verify topological execution order
        topo_order = [t.task_id for t in dag.get_topological_sort()]
        self.assertEqual(
            topo_order,
            [
                "t_ingest_bronze",
                "t_profile_bronze",
                "t_evaluate_rules",
                "t_quality_gate",
                "t_cleanse_silver",
                "t_build_gold_marts",
                "t_publish_lineage",
            ],
        )

    def test_airflow_medallion_dag_execution(self):
        ctx = DagRunContext()
        res = dag_medallion_pipeline.run(ctx)

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(len(res["tasks"]), 7)
        for task_id, task_res in res["tasks"].items():
            self.assertEqual(task_res["status"], "SUCCESS", f"Task {task_id} failed")

        # Verify XCom communication across pipeline tiers
        bronze_count = ctx.xcom_pull("t_ingest_bronze", "records_ingested")
        self.assertEqual(bronze_count, 1500)

        score = ctx.xcom_pull("t_evaluate_rules", "quality_score")
        self.assertEqual(score, 94.5)

        marts = ctx.xcom_pull("t_build_gold_marts", "marts_created")
        self.assertIn("customer_360", marts)

    def test_airflow_quality_gate_failure_behavior(self):
        # Create a test DAG with a failing quality gate (score 65% < 85%)
        with DAG(dag_id="test_failing_gate_dag") as test_dag:
            def low_quality_score_task(context, **kwargs):
                context.xcom_push("t_eval", "quality_score", 65.0)
                return {"score": 65.0}

            def gate_fn(context, min_score=85.0):
                score = context.xcom_pull("t_eval", "quality_score") or 0.0
                return score >= min_score

            def silver_task(context, **kwargs):
                return {"promoted": True}

            t1 = PythonOperator(task_id="t_eval", python_callable=low_quality_score_task)
            t2 = QualityCheckOperator(task_id="t_gate", check_callable=gate_fn, min_score=85.0)
            t3 = PythonOperator(task_id="t_silver", python_callable=silver_task)

            t1 >> t2 >> t3

        run_res = test_dag.run()
        self.assertEqual(run_res["status"], "FAILED")
        self.assertEqual(run_res["failed_task"], "t_gate")
        self.assertNotIn("t_silver", run_res["tasks"])  # Downstream task prevented!

    def test_airflow_sla_monitor_dag_execution(self):
        ctx = DagRunContext()
        res = dag_quality_sla_monitor.run(ctx)

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(len(res["tasks"]), 4)
        freshness_res = res["tasks"]["t_check_freshness"]["result"]
        self.assertFalse(freshness_res["sla_breached"])
        self.assertLess(freshness_res["latency_minutes"], 60.0)

    def test_dbt_project_structure_and_yaml_validation(self):
        dbt_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dbt")
        self.assertTrue(os.path.exists(os.path.join(dbt_root, "dbt_project.yml")))
        self.assertTrue(os.path.exists(os.path.join(dbt_root, "profiles.yml")))
        self.assertTrue(os.path.exists(os.path.join(dbt_root, "models", "schema.yml")))

        runner = DbtRunner(project_dir=dbt_root)
        self.assertEqual(runner.project_config.get("name"), "aegis_data_governance")

    def test_dbt_models_execution_and_materialization(self):
        dbt_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dbt")
        runner = DbtRunner(project_dir=dbt_root)

        # Mock Bronze raw source tables
        crm_raw = pd.DataFrame([
            {"customer_id": "C-1", "first_name": "  Diana ", "email": "DIANA@CORP.COM ", "domain": "CRM", "created_at": "2026-01-10 10:00:00"},
            {"customer_id": "C-2", "first_name": "Bruce", "email": "bruce@corp.com", "domain": "CRM", "created_at": "2026-02-15 11:30:00"},
        ])
        erp_raw = pd.DataFrame([
            {"txn_id": "TX-100", "amount_usd": 12500.0, "currency": "USD", "timestamp": "2026-10-01 09:00:00"},
            {"txn_id": "TX-101", "amount_usd": -500.0, "currency": "USD", "timestamp": "2026-10-02 14:00:00"},
            {"txn_id": "TX-102", "amount_usd": 8500.0, "currency": "EUR", "timestamp": "2026-10-05 16:30:00"},
        ])
        ecom_raw = pd.DataFrame([
            {"order_id": "ORD-1", "customer_id": "C-1", "total_amount": 450.0, "status": "COMPLETED", "timestamp": "2026-10-10 12:00:00"},
        ])

        source_tables = {
            "crm_customers": crm_raw,
            "erp_transactions": erp_raw,
            "ecommerce_orders": ecom_raw,
        }

        run_summary = runner.run_all_models(source_tables)
        self.assertEqual(run_summary["status"], "SUCCESS")
        self.assertEqual(run_summary["total_models"], 6)

        # Verify dim_customers materialized
        dim_cust = runner.con.execute("SELECT * FROM dim_customers").df()
        self.assertEqual(len(dim_cust), 2)
        self.assertEqual(dim_cust.iloc[0]["first_name"], "Diana")  # Cleaned
        self.assertEqual(dim_cust.iloc[0]["email"], "diana@corp.com")  # Standardized

        # Verify fct_monthly_mrr materialized
        mrr = runner.con.execute("SELECT * FROM fct_monthly_mrr").df()
        self.assertGreater(len(mrr), 0)
        usd_row = mrr[mrr["currency"] == "USD"].iloc[0]
        self.assertEqual(usd_row["gross_revenue_usd"], 12500.0)
        self.assertEqual(usd_row["refunds_usd"], 500.0)
        self.assertEqual(usd_row["net_revenue_usd"], 12000.0)

    def test_dbt_schema_tests_pass(self):
        dbt_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dbt")
        runner = DbtRunner(project_dir=dbt_root)

        # Materialize valid models
        runner.con.execute("""
            CREATE TABLE dim_customers AS 
            SELECT 'C-1' as customer_id, 'alice@corp.com' as email
            UNION ALL
            SELECT 'C-2', 'bob@corp.com';

            CREATE TABLE fct_transactions AS
            SELECT 'T-1' as txn_id, 'USD' as currency, 100.0 as amount_usd
            UNION ALL
            SELECT 'T-2', 'EUR', 200.0;

            CREATE TABLE fct_monthly_mrr AS
            SELECT '2026-10' as settlement_month, 'USD' as currency;
        """)

        test_summary = runner.run_schema_tests()
        self.assertEqual(test_summary["status"], "PASS")
        self.assertEqual(test_summary["failed"], 0)
        self.assertGreater(test_summary["passed"], 5)

    def test_dbt_schema_tests_catch_violations(self):
        dbt_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dbt")
        runner = DbtRunner(project_dir=dbt_root)

        # Injected violations:
        # 1. Duplicate customer_id 'C-1' (unique failure)
        # 2. Null email on customer 'C-3' (not_null failure)
        # 3. Unaccepted currency 'BITCOIN' (accepted_values failure)
        runner.con.execute("""
            CREATE TABLE dim_customers AS 
            SELECT 'C-1' as customer_id, 'alice@corp.com' as email
            UNION ALL
            SELECT 'C-1', 'alice_dup@corp.com'
            UNION ALL
            SELECT 'C-3', CAST(NULL AS VARCHAR);

            CREATE TABLE fct_transactions AS
            SELECT 'T-1' as txn_id, 'BITCOIN' as currency, 50000.0 as amount_usd;

            CREATE TABLE fct_monthly_mrr AS
            SELECT '2026-10' as settlement_month, 'USD' as currency;
        """)

        test_summary = runner.run_schema_tests()
        self.assertEqual(test_summary["status"], "FAIL")
        self.assertEqual(test_summary["failed"], 3)  # 3 injected violations caught!


if __name__ == "__main__":
    unittest.main()
