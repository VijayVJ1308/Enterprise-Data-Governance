#!/usr/bin/env bash
# ==============================================================================
# Enterprise Data Governance Platform - Healthcheck Prober
# ==============================================================================

echo "=============================================================================="
echo "🩺 AegisData Governance - Service Health Diagnostics"
echo "=============================================================================="

check_endpoint() {
    local service_name="$1"
    local url="$2"
    local expected_code="${3:-200}"

    if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "$url" | grep -q "$expected_code"; then
        printf "  %-24s [%s]  🟢 OK (%s)\n" "$service_name" "$url" "$expected_code"
        return 0
    else
        printf "  %-24s [%s]  ⚪ OFFLINE (Standby)\n" "$service_name" "$url"
        return 1
    fi
}

check_endpoint "FastAPI Backend" "http://localhost:8000/api/v1/health" "200" || true
check_endpoint "Frontend Dashboard" "http://localhost:3000/" "200" || check_endpoint "Frontend Dev" "http://localhost:5173/" "200" || true
check_endpoint "MinIO Lakehouse S3" "http://localhost:9000/minio/health/live" "200" || true
check_endpoint "Prometheus Scraper" "http://localhost:9090/-/healthy" "200" || true
check_endpoint "Grafana Dashboards" "http://localhost:3001/api/health" "200" || true

echo "=============================================================================="
