# Technical Specification — Health Patch

> **Version:** 1.0 · **Date:** 2025
> **Status:** Approved by the team

---

## 1. General Information

| Field | Value |
|-------|-------|
| **Project name** | Health Patch |
| **Product type** | Web API (REST) — backend platform |
| **Implementation language** | Python 3.12+ |
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
          |
          | HTTP/REST + JSON
          v
+-----------------------------+
|    FastAPI Application      |
|                             |
|  Routes -> Services ->      |
|  Repositories -> ORM        |
|  Pydantic validation        |
|  JWT Middleware              |
+--------+----------+--------+
         |          |
         v          v
+----------------+ +----------------+
| PostgreSQL 17  | | Redis 7        |
| (asyncpg 5432)| | (6379)         |
| health_patch   | | OAuth state,   |
|                | | cache, rate    |
|                | | limiting       |
+----------------+ +----------------+
```

**Layer principle:**
- `routes/` — routing, HTTP status codes, service calls
- `services/` — business logic (no logic in route handlers)
- `repositories/` — data access layer (DB queries, Redis operations)
- `models/` — SQLAlchemy ORM models
- `schemas/` — Pydantic schemas for request/response data

---

## 5. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | FastAPI | latest |
| ORM | SQLAlchemy | 2.x async |
| Migrations | Alembic | latest |
| Validation | Pydantic v2 + pydantic-settings | 2.x |
| Database | PostgreSQL | 17-alpine |
| DB Driver | asyncpg | latest |
| Cache/State | Redis | 7-alpine |
| Configuration | pydantic-settings | latest |
| Password hashing | argon2-cffi (Argon2) | latest |
| Authentication | PyJWT (JWT HS256) | latest |
| OAuth | Google, GitHub, Facebook | — |
| 2FA | pyotp (TOTP) | latest |
| Email | fastapi-mail + Jinja2 | latest |
| Scheduler | APScheduler | latest |
| Package manager | uv | latest |
| Containerization | Docker + Docker Compose | v2+ |
| CI/CD | GitHub Actions + Ruff | latest |
| API Documentation | OpenAPI 3.x (built-in Swagger) | — |

---

## 6. Domain Model

The system is divided into **6 isolated domains**:

| # | Domain | Owner | Tables |
|---|--------|-------|--------|
| 1 | Identity & Auth | Marchenko D. | `USER`, `USER_PROFILE`, `REFRESH_TOKEN` |
| 2 | Activity & Workouts | Kramarenko M. | `MUSCLE_GROUP`, `EXERCISE_MUSCLE_GROUP`, `EXERCISE`, `WORKOUT_PLAN`, `PLAN_TRAINING`, `PLAN_TRAINING_EXERCISE`, `WORKOUT_SESSION`, `EXERCISE_SESSION`, `WORKOUT_SET`, `PERSONAL_RECORD` |
| 3 | Nutrition & Diet | Loban M. | `FOOD`, `FOOD_PORTION`, `DAILY_DIARY`, `MEAL_ENTRY` |
| 4 | Social | Kramarenko M. | `PLAN_COMMENT`, `PLAN_LIKE`, `PLAN_BOOKMARK` |
| 5 | Gamification (RPG) | TBD | `CHARACTER`, `CHARACTER_STAT`, `ACHIEVEMENT`, `USER_ACHIEVEMENT` |
| 6 | AI Coach | TBD | `AI_WORKOUT_PLAN` |

---

## 7. Functional Requirements

### 7.1 Identity & Auth

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-01 | Registration | User registers with name, email + password | Email is unique in DB; password hashed with Argon2; verification email sent; returns `201 Created` |
| FR-02 | Authentication | User receives JWT tokens (access + refresh) | Access token signed with HS256; expires in 1h; refresh token expires in 7d; invalid credentials -> `401` |
| FR-03 | Profile | View and update `weight`, `height`, `age`, `gender`, `fitness_goal` | Only the owner can edit; invalid fields -> `422`; BMI calculated on read |
| FR-04 | OAuth Login | Login via Google, GitHub, or Facebook | OAuth state stored in Redis with TTL; user created on first login; tokens issued on callback |
| FR-05 | Email Verification | Verify email via token link | Token sent on registration; `is_verified` set to true; invalid/expired token -> error |
| FR-06 | Password Reset | Reset password via email token | Reset email sent; token validated; new password hashed with Argon2 |
| FR-07 | Two-Factor Auth | Enable/disable TOTP 2FA | QR code generated on enable; TOTP code required to confirm setup; login returns temp token when 2FA enabled |
| FR-08 | Refresh Tokens | Token refresh and session management | Refresh tokens stored in DB with device info; revocation on logout; revoke-all for all devices |

### 7.2 Activity & Workouts

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-09 | Plan CRUD | Create, read, update, delete a workout plan | Author can edit/delete; others can only read public plans |
| FR-10 | Community feed | Paginated list of public plans | Sort by date; max 100/page |
| FR-11 | Plan Trainings | Add/remove named trainings within a plan | Each training has name, weekday, order; exercises attached with targets (sets, reps, weight %) |
| FR-12 | Session logging | Start and end a workout session | `started_at` set on start; `ended_at` on completion; session linked to a plan training or standalone |
| FR-13 | Exercise logging | Add exercises with sets, reps, and weight | Exercise order preserved (`order_num`); multiple sets per exercise; `is_from_template` flag |
| FR-14 | Muscle Groups | Manage muscle group catalog | Create and list muscle groups; exercises linked via primary FK and secondary junction table |
| FR-15 | Exercises | Manage exercise catalog | Create exercises with primary and secondary muscle groups; search with pagination |
| FR-16 | Personal Records | Track personal records per exercise | Unique per `(user_id, exercise_id)`; upsert semantics; `recorded_at` timestamp |

### 7.3 Nutrition & Diet

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-17 | Food database | Search foods with macro data | Only verified entries shown (`is_verified=true`); search by name; includes fdc_id, brand_name |
| FR-18 | Food portions | Define portion sizes per food | Each portion has amount, measure_unit_name, gram_weight |
| FR-19 | Daily diary | Create/update a daily nutrition record | Unique record per `(user_id, target_date)`; fields: `water_ml`, `notes` |
| FR-20 | Meal entry | Add a food item to the diary | Types: Breakfast / Lunch / Dinner / Snack; macros calculated automatically by weight |
| FR-21 | Daily norm | Calculate daily macro norms | Based on user profile (age, weight, height, gender, fitness_goal); requires complete profile |
| FR-22 | Day overview | View daily nutrition summary | Returns norm, consumed, and remaining macros for a given date |

### 7.4 Social

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-23 | Likes | Like/unlike a workout plan | Unique pair `(plan_id, user_id)`; repeated like = unlike |
| FR-24 | Comments | Add a comment to a plan | Authenticated user; `text` non-empty; author can delete |
| FR-25 | Bookmarks | Save a plan to bookmarks | Unique pair `(plan_id, user_id)` |

### 7.5 Gamification

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-26 | Character | Create an RPG character on first login | One character per user; class selection; starting level = 1 |
| FR-27 | XP awarding | XP is awarded after completing a session | Formula defined in config; `current_xp` updated atomically |
| FR-28 | Level up | Automatic level increase | Checked after every XP update; stats (`strength`, `endurance`, `agility`) grow |
| FR-29 | Achievements | Unlocked by XP thresholds | All `ACHIEVEMENT` thresholds checked after XP update; no duplicates |

### 7.6 AI Coach

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-30 | Plan generation | Request to external AI API | Response stored as `raw_ai_response`; `is_accepted=false` by default |
| FR-31 | Plan acceptance | Accept or reject an AI plan | On accept: `WORKOUT_PLAN` is created; on reject: only the flag is updated |

### 7.7 Admin

| ID | Name | Description | Acceptance Criteria |
|----|------|-------------|---------------------|
| FR-32 | Food verification | Admin verifies/rejects food entries | Only `role=admin`; updates `is_verified` |
| FR-33 | Exercise management | CRUD exercises with muscle group classification | Only `role=admin` can edit; exercises linked to muscle groups via FK + junction table |

---

## 8. Non-Functional Requirements

### 8.1 Performance

| ID | Requirement | Value |
|----|-------------|-------|
| NFR-01 | API response time | P95 <= 300 ms (up to 500 concurrent users) |
| NFR-02 | DB query time | <= 100 ms; queries returning > 1000 rows must use pagination |
| NFR-03 | AI generation | <= 60 sec; processed asynchronously |

### 8.2 Security

| ID | Requirement | Value |
|----|-------------|-------|
| NFR-04 | Passwords | Argon2 hashed; plaintext never logged |
| NFR-05 | JWT | HS256; access token expires in 1h; refresh token 7d; validated on every request |
| NFR-06 | Authorization | Users access only their own data; admin endpoints require `role=admin`; user can login with their Google/Github/Facebook accounts; application supports 2FA authentication |
| NFR-07 | Secrets | All keys in `.env` only; never in code or git |
| NFR-08 | Validation | Pydantic schema on all incoming data; invalid input -> `422` |
| NFR-09 | Rate Limiting | IP-based rate limiting via Redis with sliding window; configurable per endpoint |

### 8.3 Reliability

| ID | Requirement | Value |
|----|-------------|-------|
| NFR-10 | Uptime | Target 99.5% (excluding planned maintenance) |
| NFR-11 | Health check | Docker Compose waits for PostgreSQL health check before starting API |
| NFR-12 | Degradation | If AI service is unavailable — all other features continue working |

### 8.4 Scalability

| ID | Requirement | Value |
|----|-------------|-------|
| NFR-13 | Stateless | No server-side state — ready for horizontal scaling |
| NFR-14 | Async I/O | All DB calls via async SQLAlchemy + asyncpg |
| NFR-15 | Pagination | All list endpoints paginated; max page size = 100 |

### 8.5 Data Integrity

| ID | Requirement | Value |
|----|-------------|-------|
| NFR-16 | Foreign keys | All FK enforced at DB level (PostgreSQL constraints) |
| NFR-17 | Unique fields | `USER.email`; `(user_id, exercise_id)` in `PERSONAL_RECORD`; pairs `(plan_id, user_id)` in `PLAN_LIKE` and `PLAN_BOOKMARK`; `(user_id, target_date)` in `DAILY_DIARY` |
| NFR-18 | Macros | `protein + carbs + fat` <= 100 g per 100 g of food |

### 8.6 Maintainability

| ID | Requirement | Value |
|----|-------------|-------|
| NFR-19 | Migrations | All schema changes only via Alembic; manual DDL forbidden |
| NFR-20 | Configuration | All settings via `pydantic-settings` and `.env` |
| NFR-21 | Documentation | Swagger UI at `/docs`, ReDoc at `/redoc` reflect the current API state |

---

## 9. API — General Conventions

- Base URL: `http://localhost:8000`
- Data format: `application/json`
- Dates & times: ISO 8601 UTC (e.g. `2025-03-21T10:00:00Z`)
- Authentication: `Authorization: Bearer <token>`
- HTTP codes: `200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`, `500 Internal Server Error`
- Pagination: `?page=1&size=20` (max size = 100)
- Error response: `{error_code, message, timestamp, path}`

---

## 10. Database Structure (Summary)

| Table | Domain | Key Fields |
|-------|--------|-----------|
| `USER` | Auth | `id`, `name`, `email` (UK), `password_hash` (nullable), `is_verified`, `oauth_provider`, `oauth_provider_id`, `avatar_url`, `totp_secret`, `is_2fa_enabled`, `is_active`, `created_at`, `updated_at` |
| `USER_PROFILE` | Auth | `user_id` (FK), `weight`, `height`, `age`, `gender`, `fitness_goal` |
| `REFRESH_TOKEN` | Auth | `token` (UK), `user_id` (FK), `expires_at`, `is_revoked`, `device_info` |
| `MUSCLE_GROUP` | Workouts | `id`, `name` (UK) |
| `EXERCISE` | Workouts | `name`, `primary_muscle_group_id` (FK, nullable) |
| `EXERCISE_MUSCLE_GROUP` | Workouts | `exercise_id` (FK), `muscle_group_id` (FK) — compound PK |
| `WORKOUT_PLAN` | Workouts | `author_id` (FK), `title`, `description`, `is_public`, `created_at`, `updated_at` |
| `PLAN_TRAINING` | Workouts | `plan_id` (FK), `name`, `weekday`, `order_num` |
| `PLAN_TRAINING_EXERCISE` | Workouts | `plan_training_id` (FK), `exercise_id` (FK), `order_num`, `target_sets`, `target_reps`, `target_weight_pct` |
| `WORKOUT_SESSION` | Workouts | `user_id` (FK), `plan_training_id` (FK, nullable), `started_at`, `ended_at` |
| `EXERCISE_SESSION` | Workouts | `workout_session_id` (FK), `exercise_id` (FK), `order_num`, `is_from_template` |
| `WORKOUT_SET` | Workouts | `exercise_session_id` (FK), `set_number`, `reps`, `weight` |
| `PERSONAL_RECORD` | Workouts | `user_id` (FK), `exercise_id` (FK), `weight`, `recorded_at` — unique on `(user_id, exercise_id)` |
| `PLAN_COMMENT` | Social | `plan_id` (FK), `user_id` (FK), `text` |
| `PLAN_LIKE` | Social | `plan_id` (FK), `user_id` (FK) — compound PK |
| `PLAN_BOOKMARK` | Social | `plan_id` (FK), `user_id` (FK) — compound PK |
| `CHARACTER` | Gamification | `user_id` (FK), `class`, `level`, `current_xp` |
| `CHARACTER_STAT` | Gamification | `character_id` (FK), `strength`, `endurance`, `agility` |
| `ACHIEVEMENT` | Gamification | `title`, `required_xp` |
| `USER_ACHIEVEMENT` | Gamification | `user_id` (FK), `achievement_id` (FK), `unlocked_at` |
| `AI_WORKOUT_PLAN` | AI Coach | `user_id` (FK), `raw_ai_response` (JSON), `is_accepted` |
| `FOOD` | Nutrition | `fdc_id` (UK, nullable), `name`, `brand_name`, `data_type`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `is_verified` |
| `FOOD_PORTION` | Nutrition | `food_id` (FK), `amount`, `measure_unit_name`, `gram_weight` |
| `DAILY_DIARY` | Nutrition | `user_id` (FK), `target_date`, `water_ml`, `notes` — unique on `(user_id, target_date)` |
| `MEAL_ENTRY` | Nutrition | `daily_diary_id` (FK), `food_id` (FK), `meal_type`, `weight_grams` |

---

## 11. Acceptance Criteria Summary

The product is considered ready for delivery when:

- [ ] All FR-01 — FR-33 implemented and pass manual testing
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
