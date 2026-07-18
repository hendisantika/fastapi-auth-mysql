# Postman Collection

API collection for the FastAPI Auth MySQL service.

## Files

- `fastapi-auth-mysql.postman_collection.json` — all endpoints (auth, items,
  users, actuator).
- `fastapi-auth-mysql.postman_environment.json` — a **Dev** environment pointing
  at `https://fastapi.gtilabs.id`.

## Import

1. In Postman: **Import** → drop both JSON files.
2. Select the **FastAPI Auth MySQL - Dev** environment (or edit `baseUrl` to
   `http://127.0.0.1:8000` for local).

## Usage

1. Run **Auth → Register** to create a user.
2. Run **Auth → Login** — a test script captures the JWT into the `token`
   collection variable automatically.
3. All authenticated requests use bearer `{{token}}` via collection-level auth,
   so items/users requests work without pasting the token manually.

> Admin endpoints (**Users**) require the account to have `role = "admin"`.
> Promote it in the database: `UPDATE users SET role='admin' WHERE username='hendi';`

## Variables

| Variable   | Purpose                          |
|------------|----------------------------------|
| `baseUrl`  | API base URL                     |
| `token`    | JWT, auto-set by Login           |
| `username` / `email` / `password` | Register/Login payload |
| `item_id`  | Target item for get/update/delete |
| `user_id`  | Target user for admin actions    |
