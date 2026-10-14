# Enterprise Data Quality & Governance Platform — Data Flow Architecture

## Reference Data Flow Lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant Src as Enterprise Sources (CRM/ERP/HR)
    participant Ing as Ingestion Platform
    participant Brz as MinIO Bronze (Raw)
    participant Prof as Profiling Engine
    participant DQE as Data Quality Engine
    participant Slv as MinIO Silver (Clean)
    participant Rem as Remediation Engine
    participant Gld as MinIO Gold (Marts)
    participant Meta as Metadata & Governance DB
    participant Obs as Observability & Alerting
    participant API as FastAPI Backend
    participant UI as React Dashboard

    Src->>Ing: Ingest Raw Data (Batch / Kafka Stream)
    Ing->>Brz: Write Partitioned Parquet (Bronze)
    Brz->>Prof: Trigger Automated Profiling
    Prof->>Meta: Store Row Counts, Null Rates, Percentiles
    Brz->>DQE: Evaluate Technical & Business Quality Rules
    DQE->>Meta: Log Rule Execution & Quality Scores
    alt Quality Check Passed
        DQE->>Slv: Promote Raw Data to Silver Layer
    else Quality Check Failed / Violations Detected
        DQE->>Obs: Emit Quality Event to Kafka Topic
        DQE->>Meta: Create Quality Issue Record (OPEN)
        DQE->>Rem: Trigger Safe Deterministic Remediation
        Rem->>Slv: Write Fixed/Cleaned Dataset
        Rem->>Meta: Log Remediation Action & Audit Trail
    end
    Slv->>Gld: Aggregate & Enrich into Gold Business Marts
    Meta->>API: Expose Datasets, Scores, Lineage, Issues
    API->>UI: Render Interactive Dashboard & Graphs
```

## Layer Transitions & Data Contracts

1. **Source -> Bronze**:
   - Format: Raw CSV / JSON / DB dumps converted to raw Parquet format.
   - Validation: File arrival detection, metadata tracking.

2. **Bronze -> Profiling & DQ Check**:
   - Format: Parquet.
   - Validation: Schema enforcement against Data Contracts, Execution of 14+ Quality Rule Types, PII Classification.

3. **Bronze -> Silver**:
   - Format: Standardized Parquet.
   - Action: Quarantine failing rows or apply deterministic remediation (formatting, casing, phone normalization).

4. **Silver -> Gold**:
   - Format: Curated Star-Schema Marts (Parquet).
   - Action: Join cleaned dimensions & facts, aggregate business metrics, tag with ownership & glossaries.
