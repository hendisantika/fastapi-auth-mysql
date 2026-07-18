from fastapi import FastAPI

from routers import router as items_router

# Database schema is managed by Alembic migrations (see `migrations/`).
# Run `alembic upgrade head` to create/update tables.

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

app.include_router(items_router)


@app.get("/")
def home():
    return {"message": "FastAPI CRUD API"}
