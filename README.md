# AegisData: Enterprise Data Quality & Data Governance Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-3178C6.svg)](https://www.typescriptlang.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.5+-FFF000.svg)](https://duckdb.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-113%20Passed-brightgreen.svg)](#-test-verification-suite)

A complete, enterprise-grade Data Quality & Data Governance Platform designed to ingest, profile, validate, cleanse, govern, observe, and remediate enterprise datasets at scale across Medallion Lakehouse tiers (**Bronze ➔ Silver ➔ Gold**).

---

## 🏛️ Platform Architecture Overview

```
                          ENTERPRISE DATA SOURCES
                                   │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
             CRM                 ERP                 HR
          (PostgreSQL)          (CSV)               (API)
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  │
                                  ▼
                         INGESTION PLATFORM
                      Python / Kafka / REST APIs
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
             BATCH INGESTION             STREAMING INGESTION
                    │                     (Apache Kafka)
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                         DATA LAKE STORAGE
                            MinIO / S3
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                 BRONZE        SILVER          GOLD
                 (Raw)        (Clean)       (Business)
                    │             │             │
                    └─────────────┼─────────────┘
                                  │
                                  ▼
                         PROFILING ENGINE
                    (Column stats, DuckDB OLAP)
                                  │
                                  ▼
                        DATA QUALITY ENGINE
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
         Rule Engine      Anomaly Detection     Contract Validation
         (14 rules)          (Z-Score/IQR)         (YAML & Drift)
              └───────────────────┼───────────────────┘
                                  │
                                  ▼
                        METADATA PLATFORM
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
         Data Catalog          Lineage            Glossary
         (Search, Tags)       (5-tier DAG)      (Controlled Terms)
              └───────────────────┼───────────────────┘
                                  │
                                  ▼
                         GOVERNANCE ENGINE
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
          Policies           Compliance             RBAC
        (PII Masking)    (GDPR, HIPAA, SOC 2)   (Role Permissions)
              └───────────────────┼───────────────────┘
                                  │
                                  ▼
                         OBSERVABILITY & ALERTING
                        (Prometheus & Grafana)
                                  │
                                  ▼
                         FASTAPI REST BACKEND
                                  │
                                  ▼
                         REACT DASHBOARD (TS)
```

---

## 🚀 Key Modules & Capabilities

- **Data Ingestion & Storage**: Batch & streaming ingestion into MinIO/S3 Medallion Lakehouse Parquet tables.
- **Automated Profiling Engine**: Vectorized DuckDB profiler computing columnar percentiles, quantiles (`p25`–`p99`), and null rates.
- **Data Quality Framework**: 14 declarative technical & business rules across 6 key dimensions (Completeness, Validity, Uniqueness, Consistency, Accuracy, Freshness).
- **Issue & Remediation Management**: Kanban lifecycle tracking with one-click deterministic auto-remediation.
- **Metadata Catalog & Business Glossary**: Centralized asset catalog with PII classification and controlled vocabulary.
- **Data Lineage & Impact Analysis**: Interactive 5-tier Medallion DAG (**Source ➔ Bronze ➔ Silver ➔ Gold ➔ BI**) with downstream impact highlighting.
- **Data Contracts & Schema Drift**: Declarative YAML contracts enforcing SLA thresholds and schema drift history.
- **Data Governance & Compliance**: Regulatory controls matrix (GDPR, HIPAA, SOC 2, ISO 27001) and interactive cryptographic PII masking sandbox.
- **ML Observability**: Unsupervised Gaussian Z-Score outlier detection and AI quality rule recommendation discovery.
- **Apache Kafka Streaming**: Partitioned broker, consumer groups, Bronze micro-batch landing, and wire-level quality alerting.
- **Airflow & dbt Modeling**: Scheduled DAG orchestration (`dag_medallion_pipeline`, `dag_quality_sla_monitor`) and dbt star-schema models.
- **Observability Stack**: Prometheus metrics scraping and pre-configured Grafana telemetry dashboards.

---

## 📁 Repository Structure

```
enterprise-data-governance/
├── backend/            # FastAPI REST backend application & Alembic migrations
├── frontend/           # React 18 + TypeScript + Vite interactive dashboard UI
├── data-generator/     # Multi-domain synthetic enterprise dataset generator
├── data-quality/       # Profiling engine, 14 rules, scoring, and remediation
├── governance/         # PII auto-classification, masking sandbox, compliance matrix
├── lineage/            # Node/edge dependency DAG & impact analysis
├── contracts/          # YAML Data Contract parser & schema drift detector
├── ml/                 # Outlier anomaly detection & AI rule recommendations
├── ingestion/          # Batch, Streaming, and API ingestion engines
├── kafka/              # Kafka producer, consumer, and real-time alert filter
├── spark/              # PySpark batch jobs & DuckDB columnar profiler
├── airflow/            # Airflow DAG engine & production pipeline DAGs
├── dbt/                # dbt data transformation models (staging, marts) & tests
├── monitoring/         # Prometheus scrape configs, alert rules & Grafana dashboards
├── infrastructure/     # Dockerfiles (backend, frontend) and Nginx configurations
├── docs/               # System architecture & technical documentation
├── tests/              # Comprehensive 22-phase test suite (113 passing tests)
├── scripts/            # Startup, healthcheck, and demo data seeders
├── Makefile            # Project command shortcuts
└── docker-compose.yml  # 8-service local production stack orchestrator
```

---

## ⚙️ Quick Start

### Option A: Complete Docker Compose Stack (Recommended)
Launch the entire 8-service stack with one command:
```bash
./scripts/start_platform.sh
```

Or manually:
```bash
docker compose up -d
python3 scripts/seed_demo_data.py
```

### Option B: Local Standalone Development
1. **Initialize Backend**:
   ```bash
   python3 -m pip install -r requirements.txt
   python3 scripts/seed_demo_data.py
   uvicorn backend.app.main:app --port 8000 --reload
   ```

2. **Initialize Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 🌐 Active Endpoints & Access Points

| Component | URL | Credentials / Notes |
|:---|:---|:---|
| **React UI Dashboard** | [http://localhost:3000](http://localhost:3000) or [http://localhost:5173](http://localhost:5173) | Data Steward Role |
| **FastAPI REST API** | [http://localhost:8000](http://localhost:8000) | JSON API v1 |
| **Swagger API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API Explorer |
| **MinIO Lakehouse Console**| [http://localhost:9001](http://localhost:9001) | `minioadmin` / `minioadmin123` |
| **Prometheus Metrics** | [http://localhost:9090](http://localhost:9090) | Scrapes `/api/v1/health` |
| **Grafana Dashboards** | [http://localhost:3001](http://localhost:3001) | `admin` / `admin` |

---

## 🧪 Test Verification Suite

The platform includes 22 individual test suites covering every architectural component:

```bash
# Run all 113 automated tests
python3 -m pytest tests/ -v
```

```
tests/test_phase1_structure.py .......... [PASSED]
tests/test_phase2_database.py ........... [PASSED]
tests/test_phase3_data_generator.py ..... [PASSED]
tests/test_phase4_ingestion.py .......... [PASSED]
tests/test_phase5_data_lake.py .......... [PASSED]
tests/test_phase6_profiling.py .......... [PASSED]
tests/test_phase7_quality_engine.py ..... [PASSED]
tests/test_phase8_quality_scoring.py .... [PASSED]
tests/test_phase9_issue_management.py ... [PASSED]
tests/test_phase10_metadata_catalog.py .. [PASSED]
tests/test_phase11_business_glossary.py . [PASSED]
tests/test_phase12_data_lineage.py ...... [PASSED]
tests/test_phase13_contracts_and_drift.py [PASSED]
tests/test_phase14_remediation.py ....... [PASSED]
tests/test_phase15_governance.py ........ [PASSED]
tests/test_phase16_ml.py ................ [PASSED]
tests/test_phase17_fastapi_backend.py ... [PASSED]
tests/test_phase18_frontend.py .......... [PASSED]
tests/test_phase19_kafka.py ............. [PASSED]
tests/test_phase20_spark.py ............. [PASSED]
tests/test_phase21_airflow_dbt.py ....... [PASSED]
tests/test_phase22_deployment.py ........ [PASSED]
======================== 113 passed in 8.7s ========================
```

---

## 🩺 System Diagnostics

Run the automated endpoint diagnostic prober anytime to verify service health:
```bash
./scripts/healthcheck.sh
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
