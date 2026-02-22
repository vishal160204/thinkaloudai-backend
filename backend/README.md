# ThinkAloud.ai Backend

Multi-agentic DSA practice platform backend built with FastAPI, PostgreSQL, Redis, Celery, and Mem0.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### Start Services

```bash
# Copy environment file
cp backend/.env.example backend/.env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Run Migrations

```bash
# Generate migration (after model changes)
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py         # Auth endpoints
│   │   │   ├── users.py        # User endpoints
│   │   │   ├── problems.py     # Problem endpoints
│   │   │   └── router.py       # API router
│   │   └── deps.py             # Dependencies
│   ├── core/
│   │   ├── security.py         # JWT & password
│   │   └── exceptions.py       # Custom exceptions
│   ├── db/
│   │   ├── database.py         # SQLAlchemy setup
│   │   └── redis.py            # Redis client
│   ├── models/
│   │   ├── user.py             # User model
│   │   └── problem.py          # Problem models
│   ├── schemas/
│   │   ├── user.py             # User schemas
│   │   └── problem.py          # Problem schemas
│   ├── tasks/
│   │   ├── celery_app.py       # Celery config
│   │   ├── analysis.py         # Analysis tasks
│   │   ├── feedback.py         # Feedback tasks
│   │   └── maintenance.py      # Cleanup tasks
│   ├── config.py               # Settings
│   └── main.py                 # App entry
├── alembic/                    # Migrations
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 🔑 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT
- `POST /api/v1/auth/refresh` - Refresh access token

### Users
- `GET /api/v1/users/me` - Get current user
- `PATCH /api/v1/users/me` - Update profile

### Problems
- `GET /api/v1/problems` - List problems (with filters)
- `GET /api/v1/problems/{slug}` - Get problem details
- `POST /api/v1/problems` - Create problem (auth required)
- `GET /api/v1/problems/tags/` - List tags
- `GET /api/v1/problems/difficulties/` - List difficulties

## 🛠️ Development

```bash
# Install dependencies locally
cd backend
pip install -r requirements.txt

# Run locally (requires DB and Redis)
uvicorn app.main:app --reload

# Run tests
pytest
```
