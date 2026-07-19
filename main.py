import time

from fastapi import FastAPI, Request

from actuator import router as actuator_router
from apm import init_apm
from auth import router as auth_router
from logging_config import configure_logging, get_logger
from routers import router as items_router
from users import router as users_router

# Database schema is managed by Alembic migrations (see `migrations/`).
# Run `alembic upgrade head` to create/update tables.

configure_logging()
logger = get_logger("app.request")

app = FastAPI(
    title="FastAPI Auth MySQL",
    description="FastAPI CRUD API backed by MySQL.",
    version="1.0.0",
    contact={
        "name": "Hendi Santika",
        "email": "hendisantika@yahoo.co.id",
        "url": "https://github.com/hendisantika",
    },
)

# Attach Elastic APM (no-op unless ELASTIC_APM_SERVER_URL is set).
init_apm(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every API call with method, path, status, and duration.

    2xx/3xx -> INFO, 4xx -> WARNING, 5xx -> ERROR, unhandled -> ERROR.
    """
    start = time.perf_counter()
    client = request.client.host if request.client else "-"
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "%s %s from %s failed after %.1fms",
            request.method,
            request.url.path,
            client,
            duration_ms,
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    if response.status_code >= 500:
        level = "error"
    elif response.status_code >= 400:
        level = "warning"
    else:
        level = "info"
    getattr(logger, level)(
        "%s %s from %s -> %d (%.1fms)",
        request.method,
        request.url.path,
        client,
        response.status_code,
        duration_ms,
    )
    return response


app.include_router(actuator_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(items_router)


@app.get("/")
def home():
    return {"message": "FastAPI CRUD API"}
