from fastapi import FastAPI

import models
from database import Base, engine
from routers import router as items_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(items_router)


@app.get("/")
def home():
    return {"message": "FastAPI CRUD API"}
