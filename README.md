# System Design Mentor - Backend

AI-powered system design mentoring platform for students and early-career engineers.

## Tech Stack

- **Framework**: FastAPI (async)
- **ORM**: Prisma Client Python
- **Database**: PostgreSQL
- **Authentication**: JWT tokens with bcrypt password hashing

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/        # Route handlers
│   │       │   ├── auth.py       # Authentication routes
│   │       │   ├── projects.py   # Project CRUD
│   │       │   └── analysis.py   # Design analysis
│   │       └── router.py         # API router aggregator
│   ├── core/
│   │   ├── config.py             # App configuration
│   │   ├── database.py           # Prisma client setup
│   │   ├── deps.py               # Shared dependencies
│   │   └── security.py           # Auth utilities
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── services/                 # Business logic layer
│   │   ├── user_service.py       # User operations
│   │   ├── project_service.py    # Project operations
│   │   └── analysis_service.py   # Rule-based analysis engine
│   └── main.py                   # FastAPI app entry point
├── prisma/
│   └── schema.prisma             # Database schema
├── requirements.txt
└── .env.example
```

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Node.js (for Prisma CLI)

### Installation

1. Create virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:

   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. Create database:

   ```bash
   createdb design_mentor
   ```

5. Generate Prisma client and run migrations:

   ```bash
   prisma generate
   prisma db push
   ```

6. Start development server:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Once running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication

| Method | Endpoint              | Description                 |
| ------ | --------------------- | --------------------------- |
| POST   | `/api/v1/auth/signup` | Register new user           |
| POST   | `/api/v1/auth/login`  | Login, get JWT token        |
| GET    | `/api/v1/auth/me`     | Get current user profile    |
| PUT    | `/api/v1/auth/me`     | Update current user profile |

### Projects

| Method | Endpoint                       | Description                  |
| ------ | ------------------------------ | ---------------------------- |
| GET    | `/api/v1/projects`             | List user's projects         |
| POST   | `/api/v1/projects`             | Create new project           |
| GET    | `/api/v1/projects/{id}`        | Get project details          |
| PUT    | `/api/v1/projects/{id}`        | Update project metadata      |
| DELETE | `/api/v1/projects/{id}`        | Delete project               |
| PUT    | `/api/v1/projects/{id}/design` | Update design details        |
| GET    | `/api/v1/projects/{id}/full`   | Get project with suggestions |

### Analysis

| Method | Endpoint                            | Description      |
| ------ | ----------------------------------- | ---------------- |
| POST   | `/api/v1/analysis/{id}`             | Trigger analysis |
| GET    | `/api/v1/analysis/{id}/suggestions` | Get suggestions  |

## Analysis Rules

The analysis engine checks for:

1. **Caching** - Redis, Memcached, CDN
2. **Horizontal Scaling** - Load balancers, K8s
3. **Rate Limiting** - API quotas, throttling
4. **Database Indexing** - Query optimization
5. **Authentication/Authorization** - JWT, OAuth, RBAC
6. **Error Handling** - Retry, circuit breaker
7. **Monitoring** - Logging, metrics, alerting
8. **Backup/DR** - Replication, snapshots
9. **API Versioning** - Version strategy
10. **Database Sharding** - Partitioning
11. **Message Queues** - Async processing
12. **Input Validation** - Sanitization

## Example Usage

### 1. Sign Up

```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123", "full_name": "John Doe"}'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=user@example.com&password=secret123"
```

### 3. Create Project

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "URL Shortener", "description": "Design a URL shortening service"}'
```

### 4. Update Design

```bash
curl -X PUT http://localhost:8000/api/v1/projects/1/design \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "The system uses a PostgreSQL database with a REST API..."}'
```

### 5. Run Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analysis/1 \
  -H "Authorization: Bearer <token>"
```
