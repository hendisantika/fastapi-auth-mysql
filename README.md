# fastapi-auth-mysql

[![CI](https://github.com/hendisantika/fastapi-auth-mysql/actions/workflows/ci.yml/badge.svg)](https://github.com/hendisantika/fastapi-auth-mysql/actions/workflows/ci.yml)

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

## Docker

### Run locally with Docker Compose

Brings up MySQL and the API (runs migrations automatically on startup):

```bash
docker compose up --build
```

The API is then available at `http://127.0.0.1:8000`.

### Pull the published image

Images are published to Docker Hub as
[`hendisantika/fastapi-auth-mysql`](https://hub.docker.com/r/hendisantika/fastapi-auth-mysql).
Each push to `main` publishes a tag equal to the GitHub Actions run number, plus
`latest`:

```bash
docker pull hendisantika/fastapi-auth-mysql:latest

docker run -p 8000:8000 \
  -e DATABASE_URL="mysql+pymysql://root:password@host.docker.internal:3306/fastapi_auth" \
  -e SECRET_KEY="change-me-in-production" \
  hendisantika/fastapi-auth-mysql:latest
```

> Publishing requires two repository secrets: `DOCKERHUB_USERNAME` and
> `DOCKERHUB_TOKEN` (a Docker Hub access token).

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
| PATCH  | `/users/{user_id}/role` | Update a user's role (admin only) 🔒👑 |
| DELETE | `/users/{user_id}` | Delete a user (admin only) 🔒👑 |
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

## curl Examples

Assuming the API runs at `http://127.0.0.1:8000`.

### Register a user

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "hendi", "email": "hendi@example.com", "password": "secret123"}'
```

### Login and capture the token

```bash
# Login uses form-encoded fields (OAuth2 password flow)
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=hendi&password=secret123"

# Save the token directly into a shell variable
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=hendi&password=secret123" | jq -r .access_token)
```

### Get the current user

```bash
curl http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Create an item

```bash
curl -X POST http://127.0.0.1:8000/items/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Phone", "price": 499.99}'
```

### List items (pagination, filtering, sorting)

```bash
curl -G http://127.0.0.1:8000/items/ \
  -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "skip=0" \
  --data-urlencode "limit=20" \
  --data-urlencode "name=phone" \
  --data-urlencode "min_price=100" \
  --data-urlencode "mine=true" \
  --data-urlencode "sort_by=price" \
  --data-urlencode "order=desc"
```

### Get, update, and delete an item

```bash
curl http://127.0.0.1:8000/items/1 \
  -H "Authorization: Bearer $TOKEN"

curl -X PUT http://127.0.0.1:8000/items/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Phone Pro", "price": 799.99}'

curl -X DELETE http://127.0.0.1:8000/items/1 \
  -H "Authorization: Bearer $TOKEN"
```

### Admin: list users and update a role

```bash
# Requires a token belonging to a user whose role is "admin"
curl -G http://127.0.0.1:8000/users/ \
  -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "limit=20" \
  --data-urlencode "is_active=true"

curl -X PATCH http://127.0.0.1:8000/users/2/role \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'

curl -X DELETE http://127.0.0.1:8000/users/2 \
  -H "Authorization: Bearer $TOKEN"
```

## Author

- **Hendi Santika** — hendisantika@yahoo.co.id — [github.com/hendisantika](https://github.com/hendisantika)
