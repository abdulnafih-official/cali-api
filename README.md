# California House Price API

A FastAPI service that predicts California house prices from a scikit-learn model hosted on Hugging Face. It includes JWT authentication and role-based rate limiting backed by PostgreSQL.

## Features

- **Prediction endpoint** for the California Housing feature set (8 inputs)
- **JWT auth** with registration and login (bcrypt password hashing)
- **Role-based rate limiting**: per-minute sliding window plus a lifetime request quota
- **Model loaded from Hugging Face Hub** on first request and cached in memory
- **Async stack**: SQLAlchemy 2.0 + asyncpg
- **Docker Compose** setup with PostgreSQL 16

## Tech Stack

FastAPI · SQLAlchemy (async) · PostgreSQL · PyJWT · bcrypt · scikit-learn · joblib · Hugging Face Hub

## Project Structure

```
app/
├── main.py              # App entry point, creates tables on startup
├── api/
│   ├── deps.py          # DB session and current-user dependencies
│   ├── rate_limit.py    # Role-based rate limiting
│   └── routes/
│       ├── auth.py      # /auth/register, /auth/login
│       └── predict.py   # /predict
├── core/
│   ├── config.py        # Settings (env) and role limits
│   └── security.py      # Password hashing, JWT create/decode
├── db/
│   ├── models.py        # User model
│   └── session.py       # Async engine and session factory
├── schemas/             # Pydantic request/response models
└── services/
    └── model_service.py # Downloads and caches the model
```

## Getting Started

### Prerequisites

- Docker and Docker Compose, **or** Python 3.12+ and a PostgreSQL instance
- A scikit-learn model saved with `joblib`, uploaded to a Hugging Face repo

### Configuration

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Async Postgres URL (`postgresql+asyncpg://...`) | required |
| `JWT_SECRET` | Secret used to sign tokens. Use a long random value. | required |
| `HF_REPO_ID` | Hugging Face repo containing the model (`user/repo`) | required |
| `HF_FILENAME` | Model filename in that repo | `model.joblib` |
| `HF_TOKEN` | Hugging Face token (only needed for private repos) | none |

`JWT_ALGORITHM` (`HS256`) and `ACCESS_TOKEN_EXPIRE_MINUTES` (`60`) can also be overridden via env.

### Run with Docker Compose

```bash
docker compose up --build
```

The API is served at `http://localhost:8000`. Inside Compose, `DATABASE_URL` is overridden to point at the `db` service.

### Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Tables are created automatically on startup.

## API

Interactive docs are available at `/docs` (Swagger UI) and `/redoc`.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Create an account |
| POST | `/auth/login` | No | Get an access token (form-encoded) |
| POST | `/predict` | Bearer token | Predict a house price |

### Register

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "your-password"}'
```

### Login

The login endpoint uses the OAuth2 password form, so the email goes in the `username` field.

```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=you@example.com&password=your-password"
```

Response:

```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

### Predict

```bash
curl -X POST http://localhost:8000/predict \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "MedInc": 8.3252,
    "HouseAge": 41.0,
    "AveRooms": 6.98,
    "AveBedrms": 1.02,
    "Population": 322.0,
    "AveOccup": 2.55,
    "Latitude": 37.88,
    "Longitude": -122.23
  }'
```

Response:

```json
{ "prediction": 4.13 }
```

`prediction` is in units of **$100,000** (4.13 ≈ $413,000).

### Input features

| Field | Meaning |
|---|---|
| `MedInc` | Median income in the block group |
| `HouseAge` | Median house age |
| `AveRooms` | Average rooms per household |
| `AveBedrms` | Average bedrooms per household |
| `Population` | Block group population |
| `AveOccup` | Average household occupancy |
| `Latitude` | Block group latitude |
| `Longitude` | Block group longitude |

## Rate Limits

Limits are applied per user based on their `role`. New users start as `free`.

| Role | Requests / minute | Lifetime requests |
|---|---|---|
| `free` | 10 | 1,000 |
| `premium` | 60 | 50,000 |
| `admin` | 600 | Unlimited |

Exceeding a limit returns `429 Too Many Requests`. The per-minute limit includes a `Retry-After` header.

**Notes**

- The per-minute window is stored in process memory, so it is per worker and resets on restart. Use a shared store such as Redis if you run multiple workers or replicas.
- There is no endpoint for changing roles. Update the `role` column in the `users` table directly.

## Error Codes

| Status | Meaning |
|---|---|
| 401 | Invalid or expired token, or bad credentials |
| 409 | Email already registered |
| 422 | Invalid request body |
| 429 | Rate limit or total quota exceeded |
