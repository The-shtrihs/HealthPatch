# CLAUDE.md - Health Patch Project Guide

## Project Overview

Health Patch is a gamified backend platform for tracking physical activity and nutrition with RPG elements and AI coaching. It is a **REST API only** (no frontend). Current stage: Backend MVP.

## Tech Stack

- **Language:** Python 3.12+
- **Framework:** FastAPI (async)
- **ORM:** SQLAlchemy 2.x async + asyncpg
- **Migrations:** Alembic
- **Validation:** Pydantic v2 + pydantic-settings
- **Database:** PostgreSQL 17
- **Cache/State:** Redis 7 (via redis.asyncio)
- **Auth:** JWT (PyJWT, HS256), Argon2 password hashing, OAuth2 (Google/GitHub/Facebook), TOTP 2FA
- **Email:** fastapi-mail + Jinja2 templates
- **Scheduler:** APScheduler
- **Package manager:** uv (not pip)
- **Linter/Formatter:** Ruff
- **Containerization:** Docker + Docker Compose

## Quick Commands

```bash
# Start all services (DB, Redis, API)
docker compose up --build

# Run API locally (requires DB + Redis running)
uv run uvicorn src.core.main:app --host 0.0.0.0 --port 8000 --reload

# Install dependencies
uv sync

# Install dev dependencies
uv sync --dev

# Lint and format
ruff check . --fix
ruff format .

# Run tests
pytest

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Architecture

### Layer Structure (strict separation)

```
src/
  core/         # App config, DB engine, Redis pool, base classes, exceptions, scheduler
  models/       # SQLAlchemy ORM models only
  schemas/      # Pydantic request/response schemas only
  repositories/ # Data access layer (DB queries, Redis operations)
  services/     # Business logic (NO logic in routes)
  routes/       # HTTP routing, status codes, dependency injection, service calls
  templates/    # Jinja2 email templates
  scripts/      # One-off data loading scripts
```

**Flow:** Route -> Service -> Repository -> Model/DB

### Key Conventions

- **Routes** (`src/routes/`): Use `APIRouter` with `prefix` and `tags`. Inject services via FastAPI `Depends()`. No business logic here - only HTTP concerns (status codes, calling services, returning responses).
- **Dependencies** (`src/routes/dependencies.py`): Central file for all FastAPI dependency injection functions. Services and repos are wired here.
- **Services** (`src/services/`): Business logic lives here. Services receive repositories via constructor injection. Use `get_settings()` for config.
- **Repositories** (`src/repositories/`): Data access only. SQL repos take `AsyncSession`, Redis repos extend `BaseRedisRepository`. Two patterns exist:
  - Instance-based: `__init__(self, db)` with instance methods (e.g., `UserRepository`)
  - Static methods: `@staticmethod` with `db` as first param (e.g., `NutritionRepository`)
- **Models** (`src/models/`): SQLAlchemy declarative models using `Mapped[]` + `mapped_column()`. Inherit from `Base`. Use `TimestampMixin` and `IsActiveMixin` from `src/core/base.py`. All models must be re-exported in `src/models/__init__.py` (required for Alembic).
- **Schemas** (`src/schemas/`): Pydantic v2 `BaseModel` classes for request/response. Use `Field()` for validation constraints. Use `field_validator` and `model_validator` for complex validation.

### Database Patterns

- All models inherit from `Base` (in `src/core/base.py`)
- Use `Mapped[type]` type annotations with `mapped_column()`
- Use `TYPE_CHECKING` imports for relationship type hints to avoid circular imports
- Foreign keys use `ondelete="CASCADE"` or `"RESTRICT"` or `"SET NULL"`
- Unique constraints via `UniqueConstraint` in `__table_args__`
- Enums use `StrEnum` mapped to `SQLAlchemyEnum`
- Timestamps: `TimestampMixin` provides `created_at`/`updated_at` with timezone-aware datetimes

### Error Handling

- Custom exception hierarchy in `src/core/exceptions.py`
- Base: `AppError(message, status_code, error_code)`
- Subclasses: `BadRequestError`, `UnauthorizedError`, `ForbiddenError`, `NotFoundError`, `ConflictError`, etc.
- Domain-specific: `InvalidCredentialsError`, `EmailAlreadyExistsError`, `OAuthStateMismatchError`, etc.
- All errors return `ErrorResponse` JSON: `{error_code, message, timestamp, path}`
- Global exception handlers registered in `setup_exception_handlers()` for `AppError`, `HTTPException`, `IntegrityError`, `RequestValidationError`, and unhandled `Exception`

### Configuration

- All settings via `pydantic-settings` in `src/core/config.py`
- Access via `get_settings()` (cached with `lru_cache`)
- All secrets in `.env` file (never in code)
- Key env vars: `DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`, OAuth client IDs/secrets, SMTP credentials

### Redis

- Connection pool initialized in app lifespan (`src/core/main.py`)
- Access via `src/core/redis.get_redis()`
- Redis repositories extend `BaseRedisRepository` (`src/repositories/redis_base.py`)
- Used for: OAuth state (CSRF protection), caching

## Code Style (Ruff)

- **Target:** Python 3.12
- **Line length:** 150 characters
- **Lint rules:** E (pycodestyle errors), F (pyflakes), I (isort), N (pep8-naming), UP (pyupgrade)
- **Migrations exempt** from E501 (line length)
- Use `str | None` union syntax (not `Optional[str]`) - PEP 604
- Use `list[...]` not `List[...]` - PEP 585
- Imports sorted by isort rules (stdlib, third-party, local)

## Domain Structure

The system has 6 isolated domains, each owned by a team member:

| Domain | Status | Key Files |
|--------|--------|-----------|
| Identity & Auth | Implemented | `models/user.py`, `services/auth.py`, `services/oauth.py`, `routes/auth.py`, `routes/oauth.py` |
| Activity & Workouts | Models defined | `models/activity.py`, `models/social.py` |
| Nutrition & Diet | Implemented | `models/nutrition.py`, `services/nutrition.py`, `routes/nutrition.py` |
| Social | Models defined | `models/social.py` |
| Gamification (RPG) | Not started | - |
| AI Coach | Not started | - |

## Migrations

- All schema changes via Alembic only (no manual DDL)
- Migration files in `migrations/versions/`
- `migrations/env.py` uses async engine and imports `Base` from `src.models`
- New models MUST be imported in `src/models/__init__.py` for autogenerate to detect them

## CI/CD

- GitHub Actions (`.github/workflows/ci.yml`)
- Runs on push/PR to `main`
- Auto-fixes lint/format with Ruff and commits changes
- PRs require at least one team member approval

## Testing

- Framework: pytest + pytest-asyncio
- Async mode: auto (`asyncio_mode = "auto"`)
- Test directory: `tests/`

## Security Rules

- Passwords: Argon2 hashing only, never logged in plaintext
- JWT: HS256, 1h access token, 7d refresh token (rotated on use)
- OAuth state: stored in Redis with TTL, consumed on use (CSRF protection)
- All user input validated via Pydantic schemas
- Users can only access their own data
- All secrets in `.env`, never committed to git
