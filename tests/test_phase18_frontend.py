import os
import json
import pytest

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
SRC_DIR = os.path.join(FRONTEND_DIR, "src")


def test_package_json_configuration():
    pkg_path = os.path.join(FRONTEND_DIR, "package.json")
    assert os.path.exists(pkg_path), "frontend/package.json must exist"
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    assert pkg.get("name") == "enterprise-data-governance-frontend"
    assert "react" in pkg.get("dependencies", {})
    assert "react-dom" in pkg.get("dependencies", {})
    assert "lucide-react" in pkg.get("dependencies", {})
    assert "vite" in pkg.get("devDependencies", {})
    assert "typescript" in pkg.get("devDependencies", {})


def test_vite_and_typescript_configs():
    vite_cfg = os.path.join(FRONTEND_DIR, "vite.config.ts")
    ts_cfg = os.path.join(FRONTEND_DIR, "tsconfig.json")
    index_html = os.path.join(FRONTEND_DIR, "index.html")

    assert os.path.exists(vite_cfg), "vite.config.ts must exist"
    assert os.path.exists(ts_cfg), "tsconfig.json must exist"
    assert os.path.exists(index_html), "index.html must exist"

    with open(vite_cfg, "r", encoding="utf-8") as f:
        content = f.read()
        assert "react" in content
        assert "proxy" in content

    with open(index_html, "r", encoding="utf-8") as f:
        html = f.read()
        assert '<div id="root"></div>' in html
        assert "AegisData" in html


def test_design_system_css_tokens():
    css_path = os.path.join(SRC_DIR, "index.css")
    assert os.path.exists(css_path), "src/index.css must exist"
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    # Check design tokens
    assert "--bg-primary:" in css
    assert "--border-subtle:" in css
    assert "--accent-cyan:" in css
    assert "--status-good:" in css
    assert ".glass-panel" in css
    assert ".metric-card" in css


def test_typescript_types():
    types_path = os.path.join(SRC_DIR, "types", "index.ts")
    assert os.path.exists(types_path), "src/types/index.ts must exist"
    with open(types_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "export interface Dataset" in content
    assert "export interface QualitySummary" in content
    assert "export interface QualityRule" in content
    assert "export interface QualityIssue" in content
    assert "export interface LineageGraph" in content
    assert "export interface DataContract" in content
    assert "export interface ComplianceControl" in content


def test_api_service_client():
    api_path = os.path.join(SRC_DIR, "services", "api.ts")
    assert os.path.exists(api_path), "src/services/api.ts must exist"
    with open(api_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "apiService" in content
    assert "getDatasets" in content
    assert "getQualitySummary" in content
    assert "getLineageGraph" in content
    assert "executeRemediation" in content
    assert "maskText" in content


def test_ui_components_presence():
    components = [
        os.path.join(SRC_DIR, "components", "layout", "Navbar.tsx"),
        os.path.join(SRC_DIR, "components", "layout", "Sidebar.tsx"),
        os.path.join(SRC_DIR, "components", "dashboard", "ExecutiveView.tsx"),
        os.path.join(SRC_DIR, "components", "catalog", "CatalogView.tsx"),
        os.path.join(SRC_DIR, "components", "quality", "QualityView.tsx"),
        os.path.join(SRC_DIR, "components", "lineage", "LineageView.tsx"),
        os.path.join(SRC_DIR, "components", "contracts", "ContractsView.tsx"),
        os.path.join(SRC_DIR, "components", "governance", "GovernanceView.tsx"),
        os.path.join(SRC_DIR, "components", "ml", "AnomalyView.tsx"),
        os.path.join(SRC_DIR, "App.tsx"),
        os.path.join(SRC_DIR, "main.tsx"),
    ]
    for comp in components:
        assert os.path.exists(comp), f"Component {comp} must exist"


def test_production_build_artifacts():
    dist_dir = os.path.join(FRONTEND_DIR, "dist")
    assert os.path.exists(dist_dir), "frontend/dist must exist after npm run build"
    assert os.path.exists(os.path.join(dist_dir, "index.html")), "frontend/dist/index.html must exist"
    assets_dir = os.path.join(dist_dir, "assets")
    assert os.path.exists(assets_dir), "frontend/dist/assets must exist"
    files = os.listdir(assets_dir)
    assert any(f.endswith(".js") for f in files), "dist/assets must have compiled JS"
    assert any(f.endswith(".css") for f in files), "dist/assets must have compiled CSS"
