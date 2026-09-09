# Cheetah API

FastAPI backend for an **InterCity Transportation Aggregator** platform. Search schedules across providers, create bookings (user or guest), handle payments, and auto-issue free accident insurance + Wi‑Fi codes after a booking.

Interactive docs: **`/docs`** (Swagger) and **`/redoc`** when `DEBUG=true`.

## Stack

| Layer | Choice |
| --- | --- |
| API | FastAPI + Uvicorn |
| ORM / models | SQLAlchemy 2 + SQLModel |
| Migrations | Alembic |
| DB | PostgreSQL (`psycopg2` / `asyncpg`) |
| Auth | JWT (`python-jose`) + password hashing (`passlib` / bcrypt) |
| Cache | Redis (optional via `REDIS_URL`) |
| Packaging | [uv](https://github.com/astral-sh/uv) + `pyproject.toml` (Python 3.13+) |
| Deploy | Multi-stage `Dockerfile` |
| API testing | [`cheetah-api.postman_collection.json`](./cheetah-api.postman_collection.json) |

## Features (from routers)

- **Auth** (`/auth`) — register, token/login, current user, password reset, logout, token verify
- **Users** (`/users`) — profile CRUD, user bookings / insurance / Wi‑Fi, guest lookup, admin search & activate/deactivate
- **Bookings** (`/bookings`) — cities, multi-provider search & price comparison, create/cancel booking, guest + user history, admin confirm/list
- **Payments** (`/payments`) — initialize / verify (Paystack-oriented), refunds, totals, methods, webhooks stubs
- **Insurance** (`/insurance-policies`) — policies by user/guest, claims, coverage details, admin stats
- **Wi‑Fi** (`/wifi-codes`) — codes + QR, activate, usage stats, extend (admin)
- **Providers** (`/providers`) — list/create/update providers, schedules, batch upload stub, schedule webhooks
- **Analytics** (`/admin/analytics`) — booking trends, demographics, provider performance, revenue, system stats, dashboard (admin)

Booking creation kicks off background tasks for insurance enrolment, Wi‑Fi code generation, and notifications (email/SMS helpers in services).

## Project layout

```text
app/
├─ main.py                 # FastAPI app, CORS, lifespan, router mounts
├─ database/
│   ├─ config.py           # pydantic-settings (env)
│   ├─ database.py         # engine / sessions / lifespan
│   └─ models.py           # User, Provider, Route, Schedule, Booking, Insurance, Wifi…
├─ routers/                # auth, users, bookings, payments, insurance, wifi, providers, analytics
└─ services/               # business logic + mock transport/insurance/wifi clients
alembic/                   # migrations
scripts/                   # db setup + seed helpers
Dockerfile
cheetah-api.postman_collection.json
MIGRATION_GUIDE.md
```

## Setup

### Prerequisites

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- Redis (optional; default URL points at localhost)

### Environment

Create `.env.local` (loaded by `app/database/config.py`). **Required:**

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL URL |
| `SECRET_KEY` | JWT signing key |

**Common optional vars** (names only — do not commit secrets):

- `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DEBUG`, `APP_NAME`, `APP_VERSION`, `SQL_ECHO`
- `CORS_ALLOW_ORIGINS`, `CORS_ALLOW_CREDENTIALS`, `CORS_ALLOW_METHODS`, `CORS_ALLOW_HEADERS`
- `REDIS_URL`
- `ENABLED_PROVIDERS`
- `INSURANCE_API_URL`, `INSURANCE_API_KEY`, `WIFI_API_URL`, `WIFI_API_KEY`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMS_API_KEY`

Example shape (replace with your own values):

```bash
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/cheetah_db
SECRET_KEY=change-me
DEBUG=true
REDIS_URL=redis://localhost:6379/0
```

### Local (uv)

```bash
git clone https://github.com/dotunv/cheetah-api.git
cd cheetah-api
uv sync

# apply migrations
uv run alembic upgrade head

# optional seed (see scripts/)
uv run python scripts/seed_database.py

# run API
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check: `GET /health`  · Welcome: `GET /`  · Docs: `http://localhost:8000/docs`

### Docker

```bash
docker build -t cheetah-api .
docker run --env-file .env.local -p 8000:8000 cheetah-api
```

The image runs `uvicorn app.main:app` on port **8000**.

## Migrations (Alembic)

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "describe change"
uv run alembic current
uv run alembic history
```

Full workflow notes: [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md).

## API overview

| Prefix | Tag | What it covers |
| --- | --- | --- |
| `/auth` | Authentication | Register, login/token, me, password reset, logout |
| `/users` | Users | Profile, bookings, policies, Wi‑Fi, admin user ops |
| `/bookings` | Bookings | Search, book, cancel, guest/user history, admin |
| `/payments` | Payments | Initialize, verify, refund, totals, webhooks |
| `/insurance-policies` | Insurance | Policies, claims, coverage, stats |
| `/wifi-codes` | WiFi | Codes, QR, activate, usage, admin extend |
| `/providers` | Transport Providers | CRUD-ish provider + schedule management |
| `/admin/analytics` | Analytics | Trends, demographics, revenue, dashboard |

Import the Postman collection for end-to-end request examples:  
[`cheetah-api.postman_collection.json`](./cheetah-api.postman_collection.json)

## Development

```bash
uv add <package>
uv add --dev <package>   # e.g. ruff is already in the dev group
uv run ruff check .
```

## License

Use / contribute under the terms of this repository unless otherwise noted.
