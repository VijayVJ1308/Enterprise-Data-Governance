# Enterprise Data Quality & Governance Platform — Requirements Specification

## 1. Business Requirements (BR)

| Req ID | Title | Description | Primary Stakeholder |
|---|---|---|---|
| **BR-001** | Centralized Visibility | Provide unified visibility across distributed enterprise data sources (CRM, ERP, HR). | Data Governance Council / CDO |
| **BR-002** | Automated DQ Detection | Automatically detect data quality anomalies, format errors, nulls, and duplicate records. | Data Quality Engineer |
| **BR-003** | Data Ownership & Stewardship | Explicitly assign Data Owners and Data Stewards to every enterprise dataset and domain. | Data Governance Architect |
| **BR-004** | Searchable Data Catalog | Enable business users to discover datasets, schemas, classifications, and lineage. | Data Analyst / Scientist |
| **BR-005** | Downstream Impact Analysis | Allow users to inspect upstream and downstream dependencies prior to breaking changes. | Data Engineer |
| **BR-006** | Schema Drift Monitoring | Automatically track and flag column additions, deletions, renames, and type mutations. | Data Platform Engineer |
| **BR-007** | Pipeline & Freshness Observability | Monitor dataset update cadence against defined SLAs and log pipeline health. | Data Ops / SRE |
| **BR-008** | Sensitive Data Protection | Auto-classify PII/PHI fields and apply deterministic masking (full, partial, hashing). | Data Security Engineer |
| **BR-009** | Configurable Governance Policies | Enforce configurable compliance policies (e.g. mandatory ownership, quality thresholds). | Chief Compliance Officer |
| **BR-010** | Quality Issue Lifecycle | Manage quality issues through a formal lifecycle (`OPEN` -> `IN_PROGRESS` -> `RESOLVED` / `IGNORED`). | Data Steward |
| **BR-011** | Immutable Audit Trail | Record all system actions, policy edits, and sensitive data accesses in an append-only audit log. | Security Auditor |
| **BR-012** | Executive Health Dashboard | Present high-level aggregated data health, compliance status, and quality scores to leadership. | C-Suite / VPs |

---

## 2. Functional Requirements (FR)

- **FR-001 Data Ingestion**: Ingest data from CSV, JSON, Parquet, PostgreSQL, REST APIs, and Kafka streams.
- **FR-002 Medallion Storage**: Store raw ingested data in `bronze/`, cleaned/validated data in `silver/`, and aggregated/governed business marts in `gold/` using Parquet format.
- **FR-003 Data Profiling**: Automatically calculate row count, column count, null counts/rates, uniqueness, min/max/mean/median/stddev, percentiles, cardinality, data types, and pattern distributions.
- **FR-004 Rule Engine**: Support declarative rules: `NOT_NULL`, `UNIQUE`, `VALID_FORMAT`, `REGEX`, `RANGE`, `REFERENTIAL_INTEGRITY`, `ACCEPTED_VALUES`, `DATE_VALIDATION`, `CUSTOM_SQL`, `CUSTOM_PYTHON`, `FRESHNESS`, `DUPLICATE`, and `SCHEMA`.
- **FR-005 Quality Scoring**: Calculate multi-tiered scores (Column, Dataset, Domain, Business Unit, Enterprise) across 6 dimensions: Completeness, Validity, Uniqueness, Consistency, Timeliness, Accuracy.
- **FR-006 Issue Management**: Track issues with fields (`issue_id`, `dataset`, `column`, `rule_id`, `severity`, `status`, `owner`, `assigned_to`, `detected_at`, `resolved_at`).
- **FR-007 Safe Automated Remediation**: Perform deterministic fixes (whitespace trimming, case normalization, phone formatting, country code standardization, exact deduplication, default filling) with audit trails.
- **FR-008 Lineage & Impact**: Track dataset and column level lineage across source -> lake -> mart -> BI.
- **FR-009 Data Contracts**: Validate YAML contracts defining schema constraints, SLA freshness, and quality thresholds. Flag breaches automatically.
- **FR-010 Compliance Mapping**: Map technical controls to GDPR, HIPAA, SOC 2, and ISO 27001 compliance requirements.
- **FR-011 REST API & React UI**: Expose full operational capabilities via FastAPI REST endpoints and render an interactive React dashboard.

---

## 3. Non-Functional Requirements (NFR)

- **NFR-001 Scalability**: Support batch profiling and validation on millions of rows using PySpark & DuckDB/PostgreSQL.
- **NFR-002 Security**: Enforce RBAC (8 roles), JWT auth, parameterized queries, PII masking, and audit logging.
- **NFR-003 Reliability & Idempotency**: All ingestion and transformation pipelines must be idempotent and safe to retry.
- **NFR-004 Observability**: Export Prometheus metrics for latency, pipeline failures, freshness SLAs, and quality scores.
- **NFR-005 Reproducibility**: 1-step deployment via `docker-compose up` with zero paid cloud dependencies required locally.
