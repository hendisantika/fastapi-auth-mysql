from fastapi import FastAPI

import models
from database import Base, engine
from routers import router as items_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Auth MySQL",
    description="FastAPI CRUD API backed by MySQL.",
    version="1.0.0",
    contact={
        "name": "Hendi Santika",
        "email": "hendi.santika@mhdc.co.id",
        "url": "https://github.com/hendisantika",
    },
)

app.include_router(items_router)


@app.get("/")
def home():
    return {"message": "FastAPI CRUD API"}
