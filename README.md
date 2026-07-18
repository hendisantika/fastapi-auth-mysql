# fastapi-auth-mysql

A simple FastAPI CRUD API backed by MySQL using SQLAlchemy.

## Features

- FastAPI REST API with full CRUD for items
- MySQL persistence via SQLAlchemy ORM
- Pydantic request/response schemas
- Auto-generated Swagger docs at `/docs`

## Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [PyMySQL](https://pymysql.readthedocs.io/)
- [Uvicorn](https://www.uvicorn.org/)

## Requirements

- Python 3.10+
- MySQL server

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create the database in MySQL:

   ```sql
   CREATE DATABASE fastapi_auth;
   ```

4. Configure environment variables. Copy `.env.example` to `.env` and update it
   with your credentials:

   ```bash
   cp .env.example .env
   ```

   ```env
   DATABASE_URL=mysql+pymysql://root:password@localhost:3306/fastapi_auth
   ```

   Tables are created automatically on application startup.

## Running

```bash
uvicorn main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

## API Documentation

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI spec: `http://127.0.0.1:8000/openapi.json`

## Endpoints

| Method | Path               | Description        |
|--------|--------------------|--------------------|
| GET    | `/`                | Health/welcome     |
| POST   | `/items/`          | Create an item     |
| GET    | `/items/`          | List all items     |
| GET    | `/items/{item_id}` | Get an item by ID  |
| PUT    | `/items/{item_id}` | Update an item     |
| DELETE | `/items/{item_id}` | Delete an item     |

## Author

- **Hendi Santika** — hendisantika@yahoo.co.id — [github.com/hendisantika](https://github.com/hendisantika)
