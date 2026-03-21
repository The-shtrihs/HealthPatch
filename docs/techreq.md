# 📄 Technical Specification — Health Patch

> **Version:** 1.0 · **Date:** 2025  
> **Status:** Approved by the team

---

## 1. General Information

| Field | Value |
|-------|-------|
| **Project name** | Health Patch |
| **Product type** | Web API (REST) — backend platform |
| **Implementation language** | Python 3.11+ |
| **Framework** | FastAPI |
| **Database** | PostgreSQL 17 |
| **ORM / Migrations** | SQLAlchemy Async + Alembic |
| **Containerization** | Docker / Docker Compose |
| **Team** | Marchenko D., Kramarenko M., Loban M., Bondarchuk O. (PM) |

---

## 2. Goal & Purpose

**Problem:** Most fitness applications are either too simple (just a tracker) or too complex (commercial platforms). There is no long-term motivation mechanism to retain users.

**Solution:** Health Patch — a gamified platform for tracking physical activity and nutrition with RPG elements and AI coaching.

**Target users:** People who want to track workouts and nutrition, receive personalized recommendations, and stay motivated through game-like progression.

**What is NOT in the current scope (out of scope):**
- Mobile application / frontend
- Real-time notifications (WebSocket)
- Payment system
- Video workout content support
- Integration with specific wearable device brands

---

## 3. System Boundaries & Deadlines

| Element | Value |
|---------|-------|
| **Current stage** | Backend MVP |
| **Frozen requirements** | Version 1.0 — changes only through team discussion |
| **Estimation** | Each domain is estimated separately by its owner |

---

## 4. System Architecture

```
Client (Browser / Mobile / Postman)
          │
          │ HTTP/REST + JSON
          ▼
┌─────────────────────────────┐
│    FastAPI Application      │
│                             │
│  Routers → Services → ORM   │
│  Pydantic validation        │
│  JWT Middleware             │
└────────────┬────────────────┘
             │ asyncpg (TCP 5432)
             ▼
┌─────────────────────────────┐
│   PostgreSQL 17 (Alpine)    │
│   Database: health_patch    │
└─────────────────────────────┘
```

**Layer principle:**
- `routers/` — routing, HTTP status codes, service calls
- `services/` — business logic (no logic in route handlers)
- `models/` — SQLAlchemy ORM models
- `schemas/` — Pydantic schemas for request/response data

---

## 5. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | FastAPI | latest |
| ORM | SQLAlchemy | 2.x async |
| Migrations | Alembic | latest |
| Validation | Pydantic v2 | 2.x |
| Database | PostgreSQL | 17-alpine |
| DB Driver | asyncpg | latest |
| Configuration | pydantic-settings | latest |
| Password hashing | argon2 | latest |
| Authentication | python-jose (JWT) | latest |
| Containerization | Docker + Docker Compose | v2+ |
| CI/CD | GitHub Actions + Ruff | latest |
| API Documentation | OpenAPI 3.x (built-in Swagger) | — |

---

## 6. Domain Model

The system is divided into **6 isolated domains**:

| # | Domain | Owner | Tables |
|---|--------|-------|--------|
| 1 | Identity & Auth | Marchenko D. | `USER`, `USER_PROFILE` |
| 2 | Activity & Workouts | Kramarenko M. | `WORKOUT_PLAN`, `WORKOUT_SESSION`, `EXERCISE`, `EXERCISE_SESSION`, `WORKOUT_SET`, `DEVICE_SYNC_METRIC` |
| 3 | Nutrition & Diet | Loban M. | `FOOD`, `DAILY_DIARY`, `MEAL_ENTRY` |
| 4 | Social | Kramarenko M. | `PLAN_COMMENT`, `PLAN_LIKE`, `PLAN_BOOKMARK` |
| 5 | Gamification (RPG) | TBD | `CHARACTER`, `CHARACTER_STAT`, `ACHIEVEMENT`, `USER_ACHIEVEMENT` |
| 6 | AI Coach | TBD | `AI_WORKOUT_PLAN` |

---

## 7. Functional Requirements

### 7.1 Identity & Auth

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-01 | Registration | User registers with email + password | Email is unique in DB; password hashed with bcrypt; returns `201 Created` |
| FR-02 | Authentication | User receives a JWT token | Token signed with HS256; expires in 24h; invalid credentials → `401` |
| FR-03 | Profile | View and update `weight`, `height`, `fitness_goal` | Only the owner can edit; invalid fields → `422` |

### 7.2 Activity & Workouts

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-04 | Plan CRUD | Create, read, update, delete a workout plan | Author can edit/delete; others can only read public plans |
| FR-05 | Community feed | Paginated list of public plans with filters | Filters: muscle group, sort by date/popularity; max 100/page |
| FR-06 | Session logging | Start and end a workout session | `started_at` set on start; `ended_at` on completion; session linked to a plan or standalone |
| FR-07 | Exercise logging | Add exercises with sets, reps, and weight | Exercise order preserved (`order_num`); multiple sets per exercise |
| FR-08 | Device sync | Save metrics: steps, heart rate, sleep | Unique by `(user_id, sync_date)`; data updated on re-sync |

### 7.3 Nutrition & Diet

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-09 | Food database | Search foods with macro data | Only verified entries shown (`is_verified=true`); search by name |
| FR-10 | Daily diary | Create/update a daily nutrition record | Unique record per `(user_id, target_date)`; fields: `water_ml`, `notes` |
| FR-11 | Meal entry | Add a food item to the diary | Types: Breakfast / Lunch / Dinner / Snack; macros calculated automatically by weight |

### 7.4 Social

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-12 | Likes | Like/unlike a workout plan | Unique pair `(plan_id, user_id)`; repeated like = unlike |
| FR-13 | Comments | Add a comment to a plan | Authenticated user; `text` non-empty; author can delete |
| FR-14 | Bookmarks | Save a plan to bookmarks | Unique pair `(plan_id, user_id)` |

### 7.5 Gamification

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-15 | Character | Create an RPG character on first login | One character per user; class selection; starting level = 1 |
| FR-16 | XP awarding | XP is awarded after completing a session | Formula defined in config; `current_xp` updated atomically |
| FR-17 | Level up | Automatic level increase | Checked after every XP update; stats (`strength`, `endurance`, `agility`) grow |
| FR-18 | Achievements | Unlocked by XP thresholds | All `ACHIEVEMENT` thresholds checked after XP update; no duplicates |

### 7.6 AI Coach

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-19 | Plan generation | Request to external AI API | Response stored as `raw_ai_response`; `is_accepted=false` by default |
| FR-20 | Plan acceptance | Accept or reject an AI plan | On accept: `WORKOUT_PLAN` is created; on reject: only the flag is updated |

### 7.7 Admin

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-21 | Food verification | Admin verifies/rejects food entries | Only `role=admin`; updates `is_verified` |
| FR-22 | Exercise management | CRUD exercises with classification | Only `role=admin` can edit |

---

## 8. Non-Functional Requirements

### 8.1 Performance

| ID | Requirement | Value |
|----|-------------|-------|
| NFR-01 | API response time | P95 ≤ 300 ms (up to 500 concurrent users) |
| NFR-02 | DB query time | ≤ 100 ms; queries returning > 1000 rows must use pagination |
| NFR-03 | AI generation | ≤ 60 sec; processed asynchronously |

### 8.2 Security

| ID | Requirement | Value |
|----|-------------|-------|
| NFR-04 | Passwords | encrypted only (cost ≥ 12); plaintext never logged |
| NFR-05 | JWT | HS256; expires in 1h; validated on every request |
| NFR-06 | Authorization | Users access only their own data; admin endpoints require `role=admin`; user can login with their Google/Github/Facebook accounts; application supports 2FA authentication |
| NFR-07 | Secrets | All keys in `.env` only; never in code or git |
| NFR-08 | Validation | Pydantic schema on all incoming data; invalid input → `422` |

### 8.3 Reliability

| ID | Requirement | Value |
|----|-------------|-------|
| NFR-09 | Uptime | Target 99.5% (excluding planned maintenance) |
| NFR-10 | Health check | Docker Compose waits for PostgreSQL health check before starting API |
| NFR-11 | Degradation | If AI service is unavailable — all other features continue working |

### 8.4 Scalability

| ID | Requirement | Value |
|----|-------------|-------|
| NFR-12 | Stateless | No server-side state — ready for horizontal scaling |
| NFR-13 | Async I/O | All DB calls via async SQLAlchemy + asyncpg |
| NFR-14 | Pagination | All list endpoints paginated; max page size = 100 |

### 8.5 Data Integrity

| ID | Requirement | Value |
|----|-------------|-------|
| NFR-15 | Foreign keys | All FK enforced at DB level (PostgreSQL constraints) |
| NFR-16 | Unique fields | `USER.email`; pairs `(plan_id, user_id)` in `PLAN_LIKE` and `PLAN_BOOKMARK` |
| NFR-17 | Macros | `protein + carbs + fat` ≤ 100 g per 100 g of food |

### 8.6 Maintainability

| ID | Requirement | Value |
|----|-------------|-------|
| NFR-18 | Migrations | All schema changes only via Alembic; manual DDL forbidden |
| NFR-19 | Configuration | All settings via `pydantic-settings` and `.env` |
| NFR-20 | Documentation | Swagger UI at `/docs`, ReDoc at `/redoc` reflect the current API state |

---

## 9. API — General Conventions

- Base URL: `http://localhost:8000`
- Data format: `application/json`
- Dates & times: ISO 8601 UTC (e.g. `2025-03-21T10:00:00Z`)
- Authentication: `Authorization: Bearer <token>`
- HTTP codes: `200 OK`, `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `422 Unprocessable Entity`, `500 Internal Server Error`
- Pagination: `?page=1&size=20`

---

## 10. Database Structure (Summary)

| Table | Domain | Key Fields |
|-------|--------|-----------|
| `USER` | Auth | `id`, `email` (UK), `password_hash`, `created_at` |
| `USER_PROFILE` | Auth | `user_id` (FK), `weight`, `height`, `fitness_goal` |
| `WORKOUT_PLAN` | Workouts | `author_id` (FK), `title`, `is_public` |
| `WORKOUT_SESSION` | Workouts | `user_id` (FK), `plan_id` (FK, nullable), `started_at`, `ended_at` |
| `EXERCISE` | Workouts | `name`, `muscle_group` |
| `EXERCISE_SESSION` | Workouts | `workout_session_id` (FK), `exercise_id` (FK), `order_num` |
| `WORKOUT_SET` | Workouts | `exercise_session_id` (FK), `set_number`, `reps`, `weight` |
| `DEVICE_SYNC_METRIC` | Workouts | `user_id` (FK), `sync_date`, `steps_count`, `avg_heart_rate`, `sleep_hours` |
| `PLAN_COMMENT` | Social | `plan_id` (FK), `user_id` (FK), `text` |
| `PLAN_LIKE` | Social | `plan_id` (FK), `user_id` (FK) — compound PK |
| `PLAN_BOOKMARK` | Social | `plan_id` (FK), `user_id` (FK) — compound PK |
| `CHARACTER` | Gamification | `user_id` (FK), `class`, `level`, `current_xp` |
| `CHARACTER_STAT` | Gamification | `character_id` (FK), `strength`, `endurance`, `agility` |
| `ACHIEVEMENT` | Gamification | `title`, `required_xp` |
| `USER_ACHIEVEMENT` | Gamification | `user_id` (FK), `achievement_id` (FK), `unlocked_at` |
| `AI_WORKOUT_PLAN` | AI Coach | `user_id` (FK), `raw_ai_response` (JSON), `is_accepted` |
| `FOOD` | Nutrition | `name`, `calories_per_100g`, macros, `is_verified` |
| `DAILY_DIARY` | Nutrition | `user_id` (FK), `target_date`, `water_ml`, `notes` |
| `MEAL_ENTRY` | Nutrition | `daily_diary_id` (FK), `food_id` (FK), `meal_type`, `weight_grams` |

---

## 11. Acceptance Criteria Summary

The product is considered ready for delivery when:

- [ ] All FR-01 — FR-22 implemented and pass manual testing
- [ ] API documented in Swagger (`/docs` displays all endpoints)
- [ ] All migrations apply cleanly with `alembic upgrade head`
- [ ] `docker compose up --build` starts the system from scratch without manual intervention
- [ ] GitHub Actions CI passes on every PR (Ruff linting)
- [ ] No secrets in code or git history
- [ ] PR to `main` only after at least one team member's approval

---

## 12. Risks & Constraints

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| AI API unavailable | Medium | Medium | Graceful degradation — rest of the API works independently |
| Scope creep | High | High | Requirements frozen at v1.0; changes only via Issues after discussion |
| Domain delivery delay | Medium | Medium | Domains are independent — others are not blocked |
| No dedicated QA | High | Medium | Each developer tests their own domain; code review is mandatory |

---

*Document prepared by the Health Patch team. Version 1.0 is fixed and approved.*
