# Workforce Analytics API

A production-ready RESTful API for workforce analytics, featuring job postings, skills tracking, JWT authentication, rate limiting, and comprehensive CRUD operations.

## Features

- **RESTful API Design** - Complete CRUD operations with proper HTTP methods and status codes
- **JWT Authentication** - Secure token-based auth with role-based access control (RBAC)
- **Rate Limiting** - Redis-powered sliding window rate limiting to prevent abuse
- **Async Operations** - Background task processing and async external API calls
- **Production Patterns** - Structured logging, request ID tracking, health checks, exception handling
- **Comprehensive Testing** - 81% test coverage with unit and integration tests
- **Dockerized** - Complete Docker setup with docker-compose for local development

## Tech Stack

- **Framework**: FastAPI 0.100+
- **Server**: Uvicorn
- **Database**: SQLite (development) / PostgreSQL (production-ready)
- **Caching**: Redis
- **Authentication**: JWT (PyJWT, passlib)
- **Testing**: pytest, pytest-cov
- **Deployment**: Docker, docker-compose

## Quick Start

### Using Docker (Recommended)
```bash
# clone repository
git clone <your-repo-url>
cd workforce-analytics-api

# start all services
docker compose up -d

# view logs
docker compose logs -f api

# api will be available at http://localhost:8000
# docs at http://localhost:8000/docs
```

### Local Development
```bash
# create virtual environment
python -m venv venv
source venv/bin/activate  # on windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# set up environment variables
cp .env.example .env
# edit .env with your configuration

# start redis (required for rate limiting)
docker run -d -p 6379:6379 redis:latest

# run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Environment Variables

Key environment variables (see `.env.example` for full list):
```bash
# Application
APP_NAME="Workforce Analytics API"
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=sqlite:///./workforce_analytics.db

# JWT
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Rate Limiting
RATE_LIMIT_REQUESTS=100  # requests per window
RATE_LIMIT_WINDOW=3600   # window in seconds
```

## API Endpoints

### Authentication (`/v1/auth`)
- `POST /v1/auth/register` - Register new user
- `POST /v1/auth/login` - Login and get JWT token
- `GET /v1/auth/me` - Get current user info

### Job Postings (`/v1/jobs`)
- `POST /v1/jobs/` - Create job posting (employer/admin only)
- `GET /v1/jobs/` - List jobs (supports filtering, sorting, pagination)
- `GET /v1/jobs/{id}` - Get specific job
- `PUT /v1/jobs/{id}` - Update job (owner/admin only)
- `PATCH /v1/jobs/{id}/deactivate` - Deactivate job
- `DELETE /v1/jobs/{id}` - Delete job (admin only)

### Skills (`/v1/skills`)
- `POST /v1/skills/` - Create skill (admin only)
- `GET /v1/skills/` - List skills (supports filtering, sorting, pagination)
- `GET /v1/skills/{id}` - Get specific skill
- `GET /v1/skills/name/{name}` - Get skill by name
- `PUT /v1/skills/{id}` - Update skill (admin only)
- `DELETE /v1/skills/{id}` - Delete skill (admin only)
- `GET /v1/skills/trending/top` - Get trending skills

### Health (`/health`)
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health with dependency status

## User Roles

- **user** - Can view jobs and skills, manage own profile
- **employer** - Can create/update/deactivate job postings
- **admin** - Full access to all resources

## Testing
```bash
# run all tests
pytest

# run with coverage
pytest --cov=app --cov-report=html

# run specific test file
pytest tests/test_auth.py

# view coverage report
open htmlcov/index.html
```

Current test coverage: **81%**

## Rate Limiting

The API implements sliding window rate limiting:
- Default: 100 requests per hour per IP
- Rate limit info returned in headers:
  - `X-RateLimit-Limit` - Max requests allowed
  - `X-RateLimit-Remaining` - Requests remaining
  - `X-RateLimit-Reset` - Time window in seconds
- 429 status code when limit exceeded

## Architecture
```
app/
├── main.py              # FastAPI application & middleware
├── config.py            # Configuration management
├── database.py          # Database setup
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── routers/             # API endpoints
├── dependencies/        # Auth & rate limiting
├── middleware/          # Request logging & tracking
├── utils/               # Security & exceptions
└── services/            # External API integrations
```

## Deployment

### Docker Production Build
```bash
# build production image
docker build -t workforce-api:latest .

# run with production settings
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_HOST=redis \
  -e SECRET_KEY=your-production-secret \
  workforce-api:latest
```

### Cloud Deployment

This API is ready to deploy to:
- Railway
- Render
- Heroku
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Apps

## License

MIT

## Author

Sam Pomeroy - Columbia University Applied AI Solutions Engineering

Built as a demonstration of production-ready API development patterns including authentication, authorization, rate limiting, async processing, comprehensive testing, and deployment best practices.

## AI Tool Use Disclosure

I used LLM-based assistants (Claude and ChatGPT) as development support tools for this project. They were primarily used for architectural scaffolding, reviewing patterns, and debugging test failures (particularly around authentication and password hashing). All implementation decisions, code integration, and test design were performed and validated by me.
