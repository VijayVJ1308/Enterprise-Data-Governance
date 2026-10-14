from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    catalog,
    quality,
    issues,
    remediation,
    glossary,
    lineage,
    contracts,
    governance,
    ml,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["Data Catalog"])
api_router.include_router(quality.router, prefix="/quality", tags=["Data Quality"])
api_router.include_router(issues.router, prefix="/issues", tags=["Issue Management"])
api_router.include_router(remediation.router, prefix="/remediation", tags=["Remediation Engine"])
api_router.include_router(glossary.router, prefix="/glossary", tags=["Business Glossary"])
api_router.include_router(lineage.router, prefix="/lineage", tags=["Data Lineage"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["Data Contracts & Drift"])
api_router.include_router(governance.router, prefix="/governance", tags=["Data Governance"])
api_router.include_router(ml.router, prefix="/ml", tags=["ML Anomaly & Rules"])
