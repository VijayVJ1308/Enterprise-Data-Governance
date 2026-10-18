# 🚀 AegisData Platform: Complete Run Commands Guide

This guide details all execution commands to run, test, observe, and manage the **AegisData Enterprise Data Quality & Governance Platform**.

---

## 📋 Quick Reference: Common Commands

| Goal | Command | Description |
| :--- | :--- | :--- |
| **View All Shortcuts** | `make help` | Displays list of all make commands |
| **Seed Demo Data** | `make seed` or `python3 scripts/seed_demo_data.py` | Seeds governance metadata & Lakehouse parquet |
| **Run Backend API** | `make run-backend` | Starts FastAPI on `http://localhost:8000` |
| **Run Frontend UI** | `make run-frontend` | Starts React Vite UI on `http://localhost:5173` |
| **Run Health Diagnostics**| `make healthcheck` | Probes all local and containerized endpoints |
| **Run Complete Test Suite**| `make test` | Runs 113 automated tests across 22 phases |
| **Start Docker Stack** | `make docker-start` or `./scripts/start_platform.sh` | Launches all 8 Docker containers |
| **Stop Docker Stack** | `make docker-down` | Stops containers and cleans volumes |
| **Build Frontend** | `make build-frontend` | Compiles production TypeScript + Vite bundle |

---

## 💻 Mode 1: Local Standalone Execution (Recommended for Fast Development)

No Docker daemon required. Runs directly on your machine.

### 1. Prerequisites & Dependencies
```bash
# Python dependencies
python3 -m pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Seed Initial Demo Metadata
Populates SQLite/DuckDB with enterprise catalogs, PII policies, lineage DAG, and Medallion lakehouse tables:
```bash
python3 scripts/seed_demo_data.py
# Or: make seed
```

### 3. Start the FastAPI Backend (Terminal 1)
```bash
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
# Or: make run-backend
```
- **REST API Base**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### 4. Start the React Frontend Dashboard (Terminal 2)
```bash
cd frontend
npm run dev
# Or from repo root: make run-frontend
```
- **Interactive UI Dashboard**: [http://localhost:5173](http://localhost:5173)

---

## 🐳 Mode 2: Docker Compose Full-Stack (Production Simulation)

Launches all 8 microservices including MinIO S3, Kafka streaming, Prometheus metrics, and Grafana dashboards.

> **Note**: Please ensure Docker Desktop is running before executing these commands.

### One-Click Bootstrap
```bash
./scripts/start_platform.sh
# Or: make docker-start
```

### Manual Docker Compose Commands
```bash
# 1. Start all 8 containers in detached mode
docker compose up -d
# Or: make docker-up

# 2. Seed lakehouse tables into MinIO
python3 scripts/seed_demo_data.py

# 3. View live logs from all services
docker compose logs -f

# 4. Stop all services and remove volumes
docker compose down -v
# Or: make docker-down
```

---

## 🌐 Active Service Endpoints & Credentials

| Service | Port | Local URL | Default Credentials / Role |
| :--- | :--- | :--- | :--- |
| **React UI Dashboard (Docker)** | `3000` | [http://localhost:3000](http://localhost:3000) | Data Steward Role |
| **React UI Dashboard (Dev)** | `5173` | [http://localhost:5173](http://localhost:5173) | Vite HMR Dev Server |
| **FastAPI REST API** | `8000` | [http://localhost:8000](http://localhost:8000) | Public JSON API v1 |
| **Swagger Interactive Docs** | `8000` | [http://localhost:8000/docs](http://localhost:8000/docs) | OpenAPI 3.0 Explorer |
| **MinIO Lakehouse S3 API** | `9000` | [http://localhost:9000](http://localhost:9000) | `minioadmin` / `minioadmin123` |
| **MinIO Lakehouse Web Console** | `9001` | [http://localhost:9001](http://localhost:9001) | `minioadmin` / `minioadmin123` |
| **Prometheus Metrics Engine** | `9090` | [http://localhost:9090](http://localhost:9090) | Scrapes `/api/v1/health` |
| **Grafana Observability UI** | `3001` | [http://localhost:3001](http://localhost:3001) | `admin` / `admin` |
| **PostgreSQL Database** | `5432` | `localhost:5432` | `aegis` / `aegis_secret` / `aegis_db` |

---

## 🩺 Diagnostics & Health Verification

Probe all system endpoints to verify connectivity:
```bash
./scripts/healthcheck.sh
# Or: make healthcheck
```

Example Output:
```
==============================================================================
🩺 AegisData Governance - Service Health Diagnostics
==============================================================================
  FastAPI Backend          [http://localhost:8000/api/v1/health]  🟢 OK (200)
  Frontend Dev             [http://localhost:5173/]               🟢 OK (200)
  MinIO Lakehouse S3       [http://localhost:9000/minio/health/live] 🟢 OK (200)
  Prometheus Scraper       [http://localhost:9090/-/healthy]      🟢 OK (200)
  Grafana Dashboards       [http://localhost:3001/api/health]     🟢 OK (200)
==============================================================================
```

---

## 🧪 Automated Test Verification

Run all 113 comprehensive unit, integration, and platform tests across all 22 phases:
```bash
python3 -m pytest tests/ -v
# Or: make test
```

To run a specific phase test:
```bash
# Example: Quality Rule Engine
python3 -m pytest tests/test_phase7_quality_engine.py -v

# Example: Data Lineage & DAG
python3 -m pytest tests/test_phase12_data_lineage.py -v

# Example: FastAPI Backend Routes
python3 -m pytest tests/test_phase17_fastapi_backend.py -v
```

---

## ⚙️ Module-Specific Execution Commands

### 1. Synthetic Enterprise Data Generator
Generate realistic enterprise datasets (customers, transactions, support tickets):
```bash
python3 -c "
from data_generator.generator import EnterpriseDataGenerator
gen = EnterpriseDataGenerator()
customers = gen.generate_customers(n=100)
print(f'Generated {len(customers)} synthetic customer records')
"
```

### 2. DuckDB Vectorized Column Profiler
Profile Parquet datasets with percentile calculations:
```bash
python3 -c "
from data_quality.profiler import ColumnProfiler
profiler = ColumnProfiler()
report = profiler.profile_file('data/lake/silver/demo_customers.parquet')
print('Profiling completed:', report.keys())
"
```

### 3. ML Outlier Detection (Z-Score & IQR)
Run unsupervised anomaly detection on metrics:
```bash
python3 -c "
from ml.anomaly_detector import AnomalyDetector
detector = AnomalyDetector()
res = detector.detect_zscore([10, 11, 12, 10, 9, 100, 11, 10])
print('Anomalies detected:', res['anomalies'])
"
```

### 4. Data Contracts & Schema Drift Detection
Verify dataset compliance against YAML contracts:
```bash
python3 -c "
from contracts.contract_engine import DataContractEngine
engine = DataContractEngine()
contract = engine.load_contract('contracts/schemas/customers_contract.yaml')
print(f'Contract verified: {contract.name} (version {contract.version})')
"
```
