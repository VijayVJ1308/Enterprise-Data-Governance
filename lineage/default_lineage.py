import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from lineage.lineage_service import LineageService

logger = logging.getLogger("DefaultLineageSeeder")


def seed_default_lineage(db_session: Session) -> Dict[str, int]:
    """
    Seeds standard enterprise end-to-end lineage:
    Source Systems -> Ingestion Pipelines -> Bronze Lake -> Quality Pipelines -> Silver Lake -> Mart Pipelines -> Gold Marts -> Dashboards & Reports
    """
    logger.info("Seeding standard enterprise data lineage graph...")

    # 1. Source Systems
    LineageService.add_node(db_session, "src:crm_postgres.customers", "CRM PostgreSQL Customers", "DATASET", domain="Sales")
    LineageService.add_node(db_session, "src:erp_csv.orders", "ERP Orders CSV", "DATASET", domain="Sales")
    LineageService.add_node(db_session, "src:erp_csv.products", "ERP Products CSV", "DATASET", domain="Inventory")
    LineageService.add_node(db_session, "src:hr_api.employees", "HR REST API Employees", "DATASET", domain="HR")

    # 2. Ingestion Pipelines
    LineageService.add_node(db_session, "pipe:ingest_customers_batch", "Customer Batch Ingestor", "PIPELINE", domain="Sales")
    LineageService.add_node(db_session, "pipe:ingest_orders_streaming", "Orders Kafka Ingestor", "PIPELINE", domain="Sales")
    LineageService.add_node(db_session, "pipe:ingest_products_batch", "Products Batch Ingestor", "PIPELINE", domain="Inventory")
    LineageService.add_node(db_session, "pipe:ingest_employees_api", "HR API Ingestor", "PIPELINE", domain="HR")

    # 3. Bronze Medallion Datasets
    LineageService.add_node(db_session, "lake:bronze.customers", "Bronze Raw Customers", "DATASET", domain="Sales")
    LineageService.add_node(db_session, "lake:bronze.orders", "Bronze Raw Orders", "DATASET", domain="Sales")
    LineageService.add_node(db_session, "lake:bronze.products", "Bronze Raw Products", "DATASET", domain="Inventory")
    LineageService.add_node(db_session, "lake:bronze.employees", "Bronze Raw Employees", "DATASET", domain="HR")

    # 4. Data Quality & Cleansing Pipelines
    LineageService.add_node(db_session, "pipe:cleanse_customers_job", "Customer DQ & Standardization Job", "PIPELINE", domain="Sales")
    LineageService.add_node(db_session, "pipe:cleanse_orders_job", "Order DQ & Validation Job", "PIPELINE", domain="Sales")
    LineageService.add_node(db_session, "pipe:cleanse_products_job", "Product DQ & Normalization Job", "PIPELINE", domain="Inventory")

    # 5. Silver Medallion Datasets
    LineageService.add_node(db_session, "lake:silver.customers", "Silver Cleaned Customers", "DATASET", domain="Sales")
    LineageService.add_node(db_session, "lake:silver.orders", "Silver Validated Orders", "DATASET", domain="Sales")
    LineageService.add_node(db_session, "lake:silver.products", "Silver Standardized Products", "DATASET", domain="Inventory")

    # 6. Aggregation & Mart Pipelines
    LineageService.add_node(db_session, "pipe:build_customer_360_mart", "Customer 360 Mart ETL", "PIPELINE", domain="Analytics")
    LineageService.add_node(db_session, "pipe:build_sales_revenue_mart", "Sales & Revenue Aggregator", "PIPELINE", domain="Finance")

    # 7. Gold Medallion Data Marts
    LineageService.add_node(db_session, "lake:gold.customer_360_mart", "Gold Customer 360 Mart", "DATASET", domain="Analytics")
    LineageService.add_node(db_session, "lake:gold.sales_revenue_mart", "Gold Monthly Sales Revenue Mart", "DATASET", domain="Finance")

    # 8. BI Dashboards & Reports
    LineageService.add_node(db_session, "dash:executive_sales_overview", "Executive Sales & Revenue Dashboard", "DASHBOARD", domain="Executive")
    LineageService.add_node(db_session, "dash:customer_churn_analytics", "Customer Churn Analytics Dashboard", "DASHBOARD", domain="Marketing")
    LineageService.add_node(db_session, "rep:monthly_finance_audit", "Monthly Financial Audit Report", "REPORT", domain="Finance")

    # Column-level Lineage Nodes
    LineageService.add_node(db_session, "col:src:customers.email", "src:customers.email", "COLUMN", domain="Sales")
    LineageService.add_node(db_session, "col:silver:customers.clean_email", "silver:customers.clean_email", "COLUMN", domain="Sales")
    LineageService.add_node(db_session, "col:gold:customer_360.primary_email", "gold:customer_360.primary_email", "COLUMN", domain="Analytics")

    # Edges Construction

    # Ingestion Flow
    LineageService.add_edge(db_session, "src:crm_postgres.customers", "pipe:ingest_customers_batch", "DIRECT_TRANSFORM", "batch_ingest_v1")
    LineageService.add_edge(db_session, "pipe:ingest_customers_batch", "lake:bronze.customers", "DIRECT_TRANSFORM", "batch_ingest_v1")

    LineageService.add_edge(db_session, "src:erp_csv.orders", "pipe:ingest_orders_streaming", "DIRECT_TRANSFORM", "kafka_ingest_v1")
    LineageService.add_edge(db_session, "pipe:ingest_orders_streaming", "lake:bronze.orders", "DIRECT_TRANSFORM", "kafka_ingest_v1")

    LineageService.add_edge(db_session, "src:erp_csv.products", "pipe:ingest_products_batch", "DIRECT_TRANSFORM", "batch_ingest_v1")
    LineageService.add_edge(db_session, "pipe:ingest_products_batch", "lake:bronze.products", "DIRECT_TRANSFORM", "batch_ingest_v1")

    # Quality & Silver Flow
    LineageService.add_edge(db_session, "lake:bronze.customers", "pipe:cleanse_customers_job", "FILTER", "spark_dq_v2")
    LineageService.add_edge(db_session, "pipe:cleanse_customers_job", "lake:silver.customers", "DIRECT_TRANSFORM", "spark_dq_v2")

    LineageService.add_edge(db_session, "lake:bronze.orders", "pipe:cleanse_orders_job", "FILTER", "spark_dq_v2")
    LineageService.add_edge(db_session, "pipe:cleanse_orders_job", "lake:silver.orders", "DIRECT_TRANSFORM", "spark_dq_v2")

    LineageService.add_edge(db_session, "lake:bronze.products", "pipe:cleanse_products_job", "FILTER", "spark_dq_v2")
    LineageService.add_edge(db_session, "pipe:cleanse_products_job", "lake:silver.products", "DIRECT_TRANSFORM", "spark_dq_v2")

    # Mart & Gold Flow (Multi-source JOIN)
    LineageService.add_edge(db_session, "lake:silver.customers", "pipe:build_customer_360_mart", "JOIN", "dbt_c360_job")
    LineageService.add_edge(db_session, "lake:silver.orders", "pipe:build_customer_360_mart", "JOIN", "dbt_c360_job")
    LineageService.add_edge(db_session, "pipe:build_customer_360_mart", "lake:gold.customer_360_mart", "AGGREGATION", "dbt_c360_job")

    LineageService.add_edge(db_session, "lake:silver.orders", "pipe:build_sales_revenue_mart", "AGGREGATION", "dbt_revenue_job")
    LineageService.add_edge(db_session, "lake:silver.products", "pipe:build_sales_revenue_mart", "JOIN", "dbt_revenue_job")
    LineageService.add_edge(db_session, "pipe:build_sales_revenue_mart", "lake:gold.sales_revenue_mart", "AGGREGATION", "dbt_revenue_job")

    # BI Flow
    LineageService.add_edge(db_session, "lake:gold.sales_revenue_mart", "dash:executive_sales_overview", "DIRECT_TRANSFORM", "tableau_refresh")
    LineageService.add_edge(db_session, "lake:gold.customer_360_mart", "dash:customer_churn_analytics", "DIRECT_TRANSFORM", "powerbi_refresh")
    LineageService.add_edge(db_session, "lake:gold.sales_revenue_mart", "rep:monthly_finance_audit", "DIRECT_TRANSFORM", "report_generator")

    # Column-level Edges
    LineageService.add_edge(db_session, "col:src:customers.email", "col:silver:customers.clean_email", "FILTER", "trim_and_lowercase")
    LineageService.add_edge(db_session, "col:silver:customers.clean_email", "col:gold:customer_360.primary_email", "DIRECT_TRANSFORM", "select_primary")

    graph = LineageService.get_lineage_graph(db_session)
    logger.info(f"Default lineage seeded successfully with {len(graph['nodes'])} nodes and {len(graph['edges'])} edges.")
    return {"nodes": len(graph["nodes"]), "edges": len(graph["edges"])}
