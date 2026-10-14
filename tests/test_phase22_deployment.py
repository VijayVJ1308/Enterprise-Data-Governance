"""
Phase 22: Docker Compose Full-Stack Deployment, Prometheus/Grafana Observability & Demo Seeders Tests.

Tests:
1. docker-compose.yml 8-Service Stack Validation
2. Backend & Frontend Multi-Stage Dockerfiles
3. Nginx Reverse Proxy Configuration
4. Prometheus Scrape Targets & Alertmanager Rules
5. Grafana Datasource Provisioning & Dashboard JSON Schema
6. Demo Data Seeder Execution & Database Population
7. Launch & Healthcheck Shell Scripts Permissions
"""

import os
import json
import yaml
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))


class TestPhase22Deployment(unittest.TestCase):

    def test_docker_compose_configuration(self):
        compose_path = os.path.join(ROOT_DIR, "docker-compose.yml")
        self.assertTrue(os.path.exists(compose_path), "docker-compose.yml must exist")

        with open(compose_path, "r", encoding="utf-8") as f:
            compose_cfg = yaml.safe_load(f)

        services = compose_cfg.get("services", {})
        expected_services = [
            "postgres",
            "minio",
            "zookeeper",
            "kafka",
            "backend",
            "frontend",
            "prometheus",
            "grafana",
        ]
        for svc in expected_services:
            self.assertIn(svc, services, f"Service '{svc}' must be defined in docker-compose.yml")

        # Verify networks and volumes
        self.assertIn("governance-net", compose_cfg.get("networks", {}))
        volumes = compose_cfg.get("volumes", {})
        self.assertIn("postgres_data", volumes)
        self.assertIn("minio_data", volumes)
        self.assertIn("prometheus_data", volumes)
        self.assertIn("grafana_data", volumes)

    def test_dockerfile_backend_syntax(self):
        dockerfile_path = os.path.join(ROOT_DIR, "infrastructure", "docker", "Dockerfile.backend")
        self.assertTrue(os.path.exists(dockerfile_path))
        with open(dockerfile_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("FROM python:", content)
        self.assertIn("EXPOSE 8000", content)
        self.assertIn("HEALTHCHECK", content)
        self.assertIn("uvicorn", content)

    def test_dockerfile_frontend_and_nginx_config(self):
        df_path = os.path.join(ROOT_DIR, "infrastructure", "docker", "Dockerfile.frontend")
        nginx_path = os.path.join(ROOT_DIR, "infrastructure", "docker", "nginx.conf")

        self.assertTrue(os.path.exists(df_path))
        self.assertTrue(os.path.exists(nginx_path))

        with open(df_path, "r", encoding="utf-8") as f:
            df_content = f.read()
        self.assertIn("FROM node:", df_content)
        self.assertIn("FROM nginx:alpine", df_content)

        with open(nginx_path, "r", encoding="utf-8") as f:
            nginx_content = f.read()
        self.assertIn("proxy_pass http://backend:8000/api/;", nginx_content)
        self.assertIn("try_files $uri $uri/ /index.html;", nginx_content)
        self.assertIn("gzip on;", nginx_content)

    def test_prometheus_scrape_and_alert_rules_config(self):
        prom_path = os.path.join(ROOT_DIR, "monitoring", "prometheus.yml")
        alert_path = os.path.join(ROOT_DIR, "monitoring", "alert_rules.yml")

        self.assertTrue(os.path.exists(prom_path))
        self.assertTrue(os.path.exists(alert_path))

        with open(prom_path, "r", encoding="utf-8") as f:
            prom_cfg = yaml.safe_load(f)
        jobs = [sc["job_name"] for sc in prom_cfg.get("scrape_configs", [])]
        self.assertIn("aegis-backend", jobs)
        self.assertIn("prometheus", jobs)
        self.assertIn("kafka-broker", jobs)

        with open(alert_path, "r", encoding="utf-8") as f:
            alert_cfg = yaml.safe_load(f)
        rules = alert_cfg["groups"][0]["rules"]
        alert_names = [r["alert"] for r in rules]
        self.assertIn("DataQualityScoreDegradation", alert_names)
        self.assertIn("PipelineFreshnessBreach", alert_names)

    def test_grafana_provisioning_and_dashboard_schema(self):
        ds_path = os.path.join(ROOT_DIR, "monitoring", "grafana", "provisioning", "datasources", "datasources.yml")
        dash_prov_path = os.path.join(ROOT_DIR, "monitoring", "grafana", "provisioning", "dashboards", "dashboards.yml")
        dash_json_path = os.path.join(ROOT_DIR, "monitoring", "grafana", "dashboards", "enterprise_data_quality_dashboard.json")

        self.assertTrue(os.path.exists(ds_path))
        self.assertTrue(os.path.exists(dash_prov_path))
        self.assertTrue(os.path.exists(dash_json_path))

        with open(dash_json_path, "r", encoding="utf-8") as f:
            dash = json.load(f)
        self.assertEqual(dash.get("uid"), "aegis-dq-telemetry")
        panel_titles = [p["title"] for p in dash.get("panels", [])]
        self.assertIn("Enterprise Quality Health Index", panel_titles)
        self.assertIn("6-Dimension Quality Score Breakdown", panel_titles)
        self.assertIn("Active Remediation Issues", panel_titles)

    def test_demo_seeder_execution(self):
        from scripts.seed_demo_data import seed_demo_data
        res = seed_demo_data()
        self.assertGreater(res.get("datasets", 0), 0)
        self.assertGreater(res.get("columns", 0), 0)
        self.assertGreater(res.get("quality_rules", 0), 0)
        self.assertTrue(os.path.exists(res.get("lakehouse_parquet_created", "")))

    def test_shell_scripts_presence_and_execution_permissions(self):
        start_sh = os.path.join(ROOT_DIR, "scripts", "start_platform.sh")
        health_sh = os.path.join(ROOT_DIR, "scripts", "healthcheck.sh")

        self.assertTrue(os.path.exists(start_sh))
        self.assertTrue(os.path.exists(health_sh))

        # Check executable permissions
        self.assertTrue(os.access(start_sh, os.X_OK), "scripts/start_platform.sh must be executable")
        self.assertTrue(os.access(health_sh, os.X_OK), "scripts/healthcheck.sh must be executable")


if __name__ == "__main__":
    unittest.main()
