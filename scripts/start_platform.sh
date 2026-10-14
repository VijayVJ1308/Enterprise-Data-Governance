#!/usr/bin/env bash
# ==============================================================================
# Enterprise Data Governance & Quality Platform - One-Click Launcher
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=============================================================================="
echo "🛡️  AegisData: Enterprise Data Quality & Governance Platform"
echo "=============================================================================="

# 1. Environment configuration
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# 2. Check Docker availability
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "🐳 Docker daemon detected. Bootstrapping full-stack containers..."
    docker compose up -d
    echo "Waiting for services to become healthy..."
    sleep 5
else
    echo "⚠️  Docker not running in local environment. Starting local standalone mode..."
fi

# 3. Seed demo metadata and lakehouse files
echo "🌱 Seeding demo governance metadata and Medallion lakehouse tables..."
python3 scripts/seed_demo_data.py

echo ""
echo "=============================================================================="
echo "🚀 Platform Services Ready:"
echo "=============================================================================="
echo "  - React Dashboard (UI):    http://localhost:3000 (Docker) / http://localhost:5173 (Dev)"
echo "  - FastAPI REST API:        http://localhost:8000"
echo "  - Interactive Swagger Docs: http://localhost:8000/docs"
echo "  - MinIO S3 Object Storage: http://localhost:9001 (Console: minioadmin / minioadmin123)"
echo "  - Prometheus Metrics:      http://localhost:9090"
echo "  - Grafana Dashboards:      http://localhost:3001 (admin / admin)"
echo "=============================================================================="
