from fastapi import APIRouter
import time

router = APIRouter()

START_TIME = time.time()


@router.get("/health", summary="Health Check")
def health_check():
    """Returns application health status, uptime, and system info."""
    uptime_seconds = round(time.time() - START_TIME, 2)
    return {
        "status": "healthy",
        "service": "Enterprise Data Quality & Data Governance API",
        "uptime_seconds": uptime_seconds,
        "version": "1.0.0",
    }
