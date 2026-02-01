# System Design Mentor - Backend

AI-powered system design mentoring platform for students and early-career engineers.

## 🎯 What Makes This Special

This is not just another LLM wrapper. It's a **hybrid analysis system** that combines:

1. **Rule-Based Analysis** (Primary) - Fast, deterministic, always available
2. **LLM Enhancement** (Secondary) - Adds depth when available, gracefully degrades

### Why This Design?

| Approach | Speed | Cost | Reliability | Explanation Quality |
|----------|-------|------|-------------|---------------------|
| Pure LLM | Slow | High | Depends on API | Excellent |
| Pure Rules | Fast | Free | 100% | Basic |
| **Hybrid (This)** | Fast | Low | 100% | Good to Excellent |

> The system works perfectly without LLM, but adds rich explanations when available.

## ✨ Key Features

### 1. Design Memory (Version History)
Every time you update your design, the system creates a snapshot:
- Track progress over time
- See how your design evolved
- Never lose past work

### 2. Intelligent Suggestion Tracking
Suggestions have 3 states:
- **OPEN** - Needs attention
- **ADDRESSED** - Auto-detected or manually marked done
- **IGNORED** - Not applicable to this design

When you add keywords like "redis" or "cache", the system automatically marks "Add Caching" as addressed!

### 3. Maturity Score (0-5)
Simple concept-based scoring:
| Concept | Adds to Score |
|---------|---------------|
| API layer defined | +1 |
| Database strategy | +1 |
| Caching layer | +1 |
| Scaling strategy | +1 |
| Safety measures (auth, validation) | +1 |

### 4. Evolution Timeline
Visual progress tracking:
```
Version 1 → 12 suggestions, maturity 1/5
Version 2 → 8 suggestions, maturity 2/5  
Version 3 → 3 suggestions, maturity 4/5  ✓ Great progress!
```

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ANALYSIS PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Check Addressed Suggestions                                 │
│     ↓ (auto-mark based on keywords)                            │
│                                                                 │
│  2. Calculate Maturity Score                                    │
│     ↓ (5 concept buckets)                                      │
│                                                                 │
│  3. Rule-Based Analysis ────────┐                              │
│     ↓ (12 concept rules)        │                              │
│                                  │  Parallel                    │
│  4. LLM Enrichment ─────────────┤  (optional)                  │
│     ↓ (explanations)            │                              │
│                                  │                              │
│  5. Merge Results ←─────────────┘                              │
│     ↓                                                          │
│                                                                 │
│  6. Create Version Snapshot                                    │
│     ↓                                                          │
│                                                                 │
│  7. Update Project Maturity                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Framework**: FastAPI (async)
- **ORM**: Prisma Client Python
- **Database**: PostgreSQL
- **Authentication**: JWT tokens with bcrypt password hashing
- **LLM**: Google Gemini (optional, graceful fallback)

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/        # Route handlers
│   │       │   ├── auth.py       # Authentication routes
│   │       │   ├── projects.py   # Project CRUD
│   │       │   └── analysis.py   # Design analysis + evolution
│   │       └── router.py         # API router aggregator
│   ├── core/
│   │   ├── config.py             # App configuration
│   │   ├── database.py           # Prisma client setup
│   │   ├── deps.py               # Shared dependencies
│   │   └── security.py           # Auth utilities
│   ├── llm/                      # LLM integration (optional)
│   │   ├── client.py             # Gemini client with fallback
│   │   ├── prompts.py            # Explanation prompts
│   │   └── schemas.py            # LLM response schemas
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── services/                 # Business logic layer
│   │   ├── user_service.py       # User operations
│   │   ├── project_service.py    # Project operations
│   │   └── analysis_service.py   # Hybrid analysis engine
│   └── main.py                   # FastAPI app entry point
├── prisma/
│   └── schema.prisma             # Database schema
├── requirements.txt
└── .env.example
```

## Database Schema

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│    User     │────<│     Project     │────<│  DesignDetails   │
└─────────────┘     ├─────────────────┤     └──────────────────┘
                    │ maturity_score  │            
                    │ maturity_reason │────<┌──────────────────┐
                    └─────────────────┘     │  DesignVersion   │
                           │                │ (history)        │
                           │                └──────────────────┘
                           │
                           ↓
                    ┌─────────────────┐
                    │   Suggestion    │
                    ├─────────────────┤
                    │ status: OPEN    │
                    │   ADDRESSED     │
                    │   IGNORED       │
                    │ trigger_keywords│
                    └─────────────────┘
```

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Node.js (for Prisma CLI)
- Google Gemini API key (optional, for LLM enrichment)

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
   # GEMINI_API_KEY is optional
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

### Analysis (Enhanced)

| Method | Endpoint                                        | Description                     |
| ------ | ----------------------------------------------- | ------------------------------- |
| POST   | `/api/v1/analysis/{id}`                         | Trigger analysis (with history) |
| GET    | `/api/v1/analysis/{id}/suggestions`             | Get suggestions (with filter)   |
| PATCH  | `/api/v1/analysis/suggestions/{id}/status`      | Update suggestion status        |
| GET    | `/api/v1/analysis/{id}/evolution`               | Get version history timeline    |

#### Analysis Response (Enhanced)

```json
{
  "project_id": 1,
  "design_version": 3,
  "suggestions_count": 5,
  "maturity_score": 3,
  "maturity_reason": "Good design (3/5): ✓ API Layer defined, ✓ Database strategy present, ✓ Caching layer considered",
  "newly_addressed_count": 2,
  "message": "🎉 2 suggestion(s) addressed! Found 1 new area(s) for improvement. Maturity: 3/5. Keep improving!",
  "suggestions": [...]
}
```

## Analysis Rules (12 Concept Buckets)

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

### 5. Run Analysis (Enhanced)

```bash
curl -X POST http://localhost:8000/api/v1/analysis/1 \
  -H "Authorization: Bearer <token>"

# Response includes maturity score and addressed suggestions!
```

### 6. View Evolution

```bash
curl http://localhost:8000/api/v1/analysis/1/evolution \
  -H "Authorization: Bearer <token>"

# Shows version history with progress
```

### 7. Update Suggestion Status

```bash
curl -X PATCH http://localhost:8000/api/v1/analysis/suggestions/5/status \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "IGNORED"}'
```

## How Auto-Detection Works

When you run analysis:

1. System checks all OPEN suggestions
2. For each suggestion, looks for trigger keywords in your design
3. If keywords found → mark as ADDRESSED automatically

Example:
- Suggestion: "Add Caching Layer" (trigger: `["cache", "redis", "memcached"]`)
- Your design: "We use **Redis** for session storage"
- Result: Suggestion auto-marked as ADDRESSED ✓

## Future Improvements

- [ ] Add Redis queue for async analysis (Step 6)
- [ ] Implement difficulty levels (beginner/intermediate/advanced)
- [ ] Add design pattern detection
- [ ] Export designs as PDF/Markdown
- [ ] Collaborative editing

---

Built with ❤️ for aspiring system designers

