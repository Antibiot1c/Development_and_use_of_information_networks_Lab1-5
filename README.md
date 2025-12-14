# InstaLite — Web Labs 1–5 (InstagramLite)

A small InstagramLite web application built for university labs 1–5:
backend + database + HTML pages + REST API + deployment/performance notes + security checks.

---

## Features
- User registration & login (HTML forms)
- Password hashing (secure)
- JWT stored in **HttpOnly cookie** for browser sessions
- Feed page (`/app`) with user actions stored in DB:
  - create posts
  - like / unlike
  - comments
  - follow / unfollow (if enabled)
- Static pages: `/` and `/about`
- REST API documented in Swagger: `/docs`
- Admin role support (`is_admin`) (if enabled in code)

---

## Tech Stack
- **FastAPI** (Python)
- **SQLAlchemy** + SQLite (default)
- **Jinja2** templates + static assets (CSS)
- Uvicorn ASGI server

---

## Project Structure
```
backend/
  app/
    main.py
    routers/
    templates/
    static/
    models.py
    db.py
    auth.py
  requirements.txt
```

---

## Quick Start (Windows)
```bat
cd backend
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Open:
- `http://127.0.0.1:8000/` — landing
- `http://127.0.0.1:8000/register` — register
- `http://127.0.0.1:8000/login` — login
- `http://127.0.0.1:8000/app` — feed (requires login)
- `http://127.0.0.1:8000/docs` — API docs

Stop server: **CTRL + C**

---

## Database
Default database is **SQLite**. Tables are created on startup.

If you want a clean database:
- stop the server
- delete the local `.db` file (if present in the project)
- start the server again

---

## How Auth Works (simple)
- Browser auth is done via **HTML routes**:
  - `GET /login` + `POST /login`
  - `GET /register` + `POST /register`
- After successful login, the server sets a cookie: `access_token` (HttpOnly JWT)
- Protected pages (like `/app`) require that cookie

> If you open `http://127.0.0.1:8000/api/auth/token` in a browser, you will see JSON (`access_token`).
> That endpoint is for API clients (Postman/React/curl), not for the HTML UI.

---

## REST API
Swagger: `http://127.0.0.1:8000/docs`

Typical endpoints:
- `POST /api/auth/register`
- `POST /api/auth/token`
- `GET /api/auth/me`
- `GET /api/posts`
- `POST /api/posts`
- `POST /api/posts/{id}/like`
- `POST /api/posts/{id}/comment`

Example login (curl):
```bat
curl -X POST "http://127.0.0.1:8000/api/auth/token" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=Test1&password=123123123"
```

---

## Labs Overview

### Lab 1 — Backend
- FastAPI backend
- Database integration (SQLAlchemy)
- Dynamic HTML pages (Jinja2 templates)
- Static content (CSS, favicon, about page)
- Registration & login for users
- User actions stored on server (posts, likes, comments)
- Admin role support (`is_admin`) if enabled

### Lab 2 — Frontend
- Browser UI (templates + CSS) and/or separate frontend (if included)
- User actions update the interface
- Session stored locally (cookie; optionally localStorage for SPA mode)

### Lab 3 — Web Services / API
- REST API endpoints for data retrieval and user actions
- Auth required for protected endpoints
- Swagger documentation at `/docs`
- API can be tested via Swagger or curl/Postman

### Lab 4 — Deployment & Performance
- Runs on localhost via Uvicorn
- Performance measurement can be done with `ab` / `wrk` / `k6`

Example with ApacheBench (`ab`):
```bash
ab -n 500 -c 20 http://127.0.0.1:8000/
ab -n 500 -c 20 http://127.0.0.1:8000/api/posts
```

What to report:
- average response time
- requests/sec (RPS)
- error rate
- comparison: localhost vs deployed server (if deployed)

### Lab 5 — Security
Static analysis (Bandit):
```bat
python -m pip install bandit
python -m bandit -r app -ll
```

Dependency audit (pip-audit):
```bat
python -m pip install pip-audit
python -m pip_audit
```

---

## Troubleshooting

### 1) `/register` returns 500: `NOT NULL constraint failed: users.email`
Your DB model requires `email`, but the register form/backend did not send it.
Fix:
- add `<input name="email" ...>` to `register.html`
- accept `email: str = Form(...)` in `POST /register`
- save `email=email` into the `User(...)`

### 2) Browser shows JSON token instead of a page
You opened an API endpoint in a browser (e.g. `/api/auth/token`).
Use:
- `GET /login` for the UI login page
- `GET /register` for the UI register page

### 3) ModuleNotFoundError: No module named 'app'
Run from the correct folder:
```bat
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

---

## License
Educational project for university labs.
