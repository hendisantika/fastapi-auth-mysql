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

5. Run database migrations to create the tables:

   ```bash
   alembic upgrade head
   ```

## Database Migrations

Schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/).

Migration files follow a Flyway-style naming convention:

```
V<version>_DDMMYYYY_HHMM__<description>.py
```

For example: `V1_18072026_0900__create_items_table.py`.

```bash
# Apply all pending migrations
alembic upgrade head

# Autogenerate a new migration after changing the models
# Pass an explicit, incrementing version via --rev-id
alembic revision --autogenerate --rev-id 2 -m "add users table"

# Roll back the most recent migration
alembic downgrade -1
```

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

| Method | Path               | Description             |
|--------|--------------------|-------------------------|
| GET    | `/`                | Health/welcome          |
| POST   | `/auth/register`   | Register a new user     |
| POST   | `/auth/login`      | Obtain a JWT token      |
| GET    | `/auth/me`         | Current user (JWT auth) |
| GET    | `/users/`          | List users (paginated, admin only) 🔒👑 |
| POST   | `/items/`          | Create an item 🔒       |
| GET    | `/items/`          | List items (paginated) 🔒 |
| GET    | `/items/{item_id}` | Get an item by ID 🔒    |
| PUT    | `/items/{item_id}` | Update an item 🔒       |
| DELETE | `/items/{item_id}` | Delete an item 🔒       |

> 🔒 Requires a valid JWT bearer token (see [Authentication](#authentication)).

### Listing items

`GET /items/` supports pagination, filtering, and sorting via query parameters:

| Param       | Default | Description                                       |
|-------------|---------|---------------------------------------------------|
| `skip`      | `0`     | Number of records to skip (offset)                |
| `limit`     | `10`    | Max records to return (1–100)                     |
| `name`      | –       | Filter by name (partial, case-insensitive match)  |
| `min_price` | –       | Minimum price                                     |
| `max_price` | –       | Maximum price                                     |
| `mine`      | `false` | Only items created by the current user            |
| `created_by`| –       | Filter by creator username (ignored when `mine`)  |
| `sort_by`   | `id`    | `id`, `name`, `price`, `created_at`, `updated_at` |
| `order`     | `asc`   | `asc` or `desc`                                   |

Example: `GET /items/?skip=0&limit=20&name=phone&min_price=100&sort_by=price&order=desc`

The response is an envelope: `{ "total", "skip", "limit", "items": [...] }`.

## Authentication

The API uses OAuth2 password flow with JWT bearer tokens.

1. `POST /auth/register` with a JSON body: `{ "username", "email", "password" }`.
2. `POST /auth/login` with form fields `username` and `password` to receive an
   `access_token`.
3. Send the token on protected endpoints via the
   `Authorization: Bearer <token>` header (or the **Authorize** button in Swagger).

### Roles

Each user has a `role` (`user` by default). Admin-only endpoints (e.g. listing
all users) require `role = "admin"`. New registrations are always created as
`user`; promote an account by updating its `role` to `admin` in the database:

```sql
UPDATE users SET role = 'admin' WHERE username = 'your_username';
```

## Author

- **Hendi Santika** — hendisantika@yahoo.co.id — [github.com/hendisantika](https://github.com/hendisantika)
