from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from logging_config import get_logger

logger = get_logger("app.actuator")

router = APIRouter(prefix="/actuator", tags=["actuator"])

APP_NAME = "fastapi-auth-mysql"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "FastAPI CRUD API backed by MySQL."


@router.get("")
def index():
    """Actuator index listing available endpoints (Spring Boot style)."""
    return {
        "_links": {
            "self": {"href": "/actuator"},
            "health": {"href": "/actuator/health"},
            "info": {"href": "/actuator/info"},
        }
    }


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """Liveness/readiness probe; reports DB connectivity."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "UP"
    except Exception:
        logger.error("Health check failed: database is unreachable", exc_info=True)
        db_status = "DOWN"

    status = "UP" if db_status == "UP" else "DOWN"
    payload = {"status": status, "components": {"db": {"status": db_status}}}
    return JSONResponse(
        status_code=200 if status == "UP" else 503,
        content=payload,
    )


@router.get("/info")
def info():
    """Application metadata."""
    return {
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "description": APP_DESCRIPTION,
        }
    }
