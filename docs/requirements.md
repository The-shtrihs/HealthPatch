# Health Patch — Software Requirements Specification

> **Version 1.0 — 2025**
> Use Cases · Functional Requirements · Non-Functional Requirements

---

## 1. Introduction

Health Patch is a full-stack fitness platform combining workout tracking, nutrition logging, RPG gamification, AI coaching, and social community features. This document defines the system's use cases, functional requirements (FR), and non-functional requirements (NFR) to guide development, testing, and stakeholder review.

**Tech stack:** FastAPI (Python 3.12+) · SQLAlchemy async ORM · Alembic · PostgreSQL 17 · Redis 7 · Docker Compose

---

## 2. Use Cases

### 2.1 Identity & Profile

#### UC-01 — Register Account
| Field | Value |
|---|---|
| **Actor** | Guest |
| **Precondition** | User is not registered |
| **Postcondition** | Account created; verification email sent; user can log in after verifying |
| **Description** | A new user creates an account by providing name, email, and password. The system validates uniqueness of email, hashes the password, creates a USER record, and sends a verification email. |
| **Main Flow** | 1. User submits name, email & password<br>2. System validates email uniqueness and password strength (min 8 chars, uppercase, lowercase, digit, special char)<br>3. System hashes password (Argon2)<br>4. USER record created with `is_verified=false`<br>5. Verification email sent as background task<br>6. `201 Created` returned |

#### UC-02 — Log In
| Field | Value |
|---|---|
| **Actor** | Registered User |
| **Precondition** | Valid account exists |
| **Postcondition** | JWT access token and refresh token issued |
| **Description** | A registered user authenticates with email and password to receive tokens for subsequent API calls. If 2FA is enabled, a temporary token is returned requiring TOTP verification. |
| **Main Flow** | 1. User submits credentials<br>2. System verifies Argon2 hash<br>3. If 2FA disabled: access token (1h) + refresh token (7d) generated<br>4. Tokens returned to client |
| **Alternative Flow (2FA)** | 3a. If 2FA enabled: temporary 2FA token returned<br>3b. User submits TOTP code with temp token to `/auth/verify-2fa`<br>3c. System verifies TOTP code<br>3d. Access + refresh tokens issued |

#### UC-03 — OAuth Login
| Field | Value |
|---|---|
| **Actor** | Guest / Registered User |
| **Precondition** | OAuth provider configured (Google, GitHub, or Facebook) |
| **Postcondition** | User authenticated; tokens issued |
| **Description** | User authenticates via a third-party OAuth provider. On first login, a new account is created automatically. |
| **Main Flow** | 1. User navigates to `/oauth/{provider}`<br>2. System generates OAuth state (stored in Redis with 5min TTL) and redirects to provider<br>3. User authenticates with provider<br>4. Provider redirects to callback with auth code<br>5. System verifies state, exchanges code for user info<br>6. If new user: USER created with `oauth_provider` set, `password_hash=NULL`<br>7. Tokens issued and returned |

#### UC-04 — Verify Email
| Field | Value |
|---|---|
| **Actor** | Registered User |
| **Precondition** | User registered; verification email received |
| **Postcondition** | `is_verified` set to true |
| **Description** | User clicks the verification link in their email to confirm their email address. |
| **Main Flow** | 1. User clicks verification link with token<br>2. System validates token (checks expiry and signature)<br>3. `is_verified` updated to true<br>4. Success message returned |

#### UC-05 — Reset Password
| Field | Value |
|---|---|
| **Actor** | Registered User |
| **Precondition** | User has a registered email |
| **Postcondition** | Password updated to new value |
| **Description** | User who forgot their password requests a reset email and sets a new password via a token link. |
| **Main Flow** | 1. User submits email to `/auth/forgot-password` (rate limited: 3/hour)<br>2. System sends reset email with token<br>3. User submits token + new password to `/auth/reset-password`<br>4. System validates token, hashes new password (Argon2)<br>5. Password updated |

#### UC-06 — Manage Profile
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated |
| **Postcondition** | Profile saved with latest values |
| **Description** | User updates personal data: weight, height, age, gender, and fitness goal in USER_PROFILE. Can also update name and avatar URL. |
| **Main Flow** | 1. User submits profile update<br>2. System validates fields (weight 0-700kg, height 0-300cm, age 0-150)<br>3. System persists USER_PROFILE<br>4. Updated profile returned with calculated BMI |

#### UC-07 — Enable Two-Factor Authentication
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated; 2FA not yet enabled |
| **Postcondition** | TOTP secret stored; 2FA enabled after confirmation |
| **Description** | User enables TOTP-based two-factor authentication on their account. |
| **Main Flow** | 1. User requests 2FA setup at `/auth/enable-2fa`<br>2. System generates TOTP secret and QR code<br>3. User scans QR code with authenticator app<br>4. User submits TOTP code to `/auth/confirm-2fa`<br>5. System verifies code; sets `is_2fa_enabled=true` |

---

### 2.2 Social & Plans

#### UC-08 — Create Workout Plan
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated |
| **Postcondition** | WORKOUT_PLAN record created with nested trainings and exercises |
| **Description** | User creates a new workout plan with title, description, visibility setting, and structured trainings containing exercises with target sets, reps, and weight percentages. |
| **Main Flow** | 1. User submits plan data with trainings<br>2. Each training has a name, optional weekday, order, and list of exercises<br>3. Each exercise specifies target sets, reps, and optional weight % of PR<br>4. System validates all exercise IDs exist<br>5. System saves WORKOUT_PLAN with nested PLAN_TRAINING and PLAN_TRAINING_EXERCISE records<br>6. `201 Created` with full plan detail returned |

#### UC-09 — Browse Public Plans
| Field | Value |
|---|---|
| **Actor** | Any User |
| **Precondition** | None (guest access allowed) |
| **Postcondition** | Paginated list of plans returned |
| **Description** | User browses the community feed of public workout plans. |
| **Main Flow** | 1. User requests `/workouts/plans/public`<br>2. System returns paginated list of `is_public=true` plans (default 20/page, max 100) |

#### UC-10 — Like / Comment / Bookmark Plan
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated; plan exists |
| **Postcondition** | PLAN_LIKE / PLAN_COMMENT / PLAN_BOOKMARK record created |
| **Description** | User interacts with a community plan by liking it, leaving a comment, or saving it to bookmarks. |
| **Main Flow** | 1. User opens a plan<br>2. Taps Like, Comment, or Bookmark<br>3. System records interaction<br>4. Counters update in real time |

---

### 2.3 Activity & Tracking

#### UC-11 — Manage Muscle Groups
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated |
| **Postcondition** | MUSCLE_GROUP record created or list returned |
| **Description** | User creates or browses the muscle group catalog used for classifying exercises. |
| **Main Flow** | 1. To list: GET `/workouts/muscle-groups` returns all groups<br>2. To create: POST with name; system validates uniqueness<br>3. `201 Created` with new group returned |

#### UC-12 — Manage Exercises
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated |
| **Postcondition** | EXERCISE record created or search results returned |
| **Description** | User creates exercises with primary and secondary muscle group associations, or searches the exercise catalog. |
| **Main Flow** | 1. To search: GET `/workouts/exercises?search=X&page=1&size=20`<br>2. To create: POST with name, optional primary_muscle_group_id, optional secondary_muscle_group_ids<br>3. System creates EXERCISE and EXERCISE_MUSCLE_GROUP junction records<br>4. Exercise returned with muscle group details |

#### UC-13 — Start Workout Session
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated |
| **Postcondition** | WORKOUT_SESSION created with `started_at` timestamp |
| **Description** | User starts a new workout session, optionally linking it to a plan training. |
| **Main Flow** | 1. User submits start request with optional `plan_training_id`<br>2. If plan_training_id provided: system validates it exists<br>3. System creates WORKOUT_SESSION with `started_at=now()`<br>4. Session returned with id and timestamps |

#### UC-14 — Log Exercise Sets
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | Active WORKOUT_SESSION exists (not ended) |
| **Postcondition** | EXERCISE_SESSION and WORKOUT_SET records created |
| **Description** | During a session, user adds exercises and logs individual sets with reps and weight. |
| **Main Flow** | 1. User adds exercise to session: POST with `exercise_id` and `order_num`<br>2. System validates exercise exists and session is not ended<br>3. EXERCISE_SESSION created<br>4. User logs sets: POST with `set_number`, `reps`, `weight`<br>5. WORKOUT_SET records created<br>6. Progress displayed |

#### UC-15 — End Workout Session
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | Active WORKOUT_SESSION exists |
| **Postcondition** | `ended_at` timestamp recorded |
| **Description** | User finishes a workout session, recording the end time. |
| **Main Flow** | 1. User requests session end at `/workouts/sessions/{id}/end`<br>2. System validates session belongs to user and is not already ended<br>3. `ended_at` set to current timestamp<br>4. Updated session returned with `duration_minutes` |

#### UC-16 — Track Personal Records
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated; exercise exists |
| **Postcondition** | PERSONAL_RECORD created or updated |
| **Description** | User records or updates their personal best weight for an exercise. Uses upsert semantics — one record per (user, exercise). |
| **Main Flow** | 1. User submits `exercise_id` and `weight`<br>2. System checks for existing record for this (user, exercise) pair<br>3. If exists: weight and `recorded_at` updated<br>4. If new: PERSONAL_RECORD created<br>5. Record returned |

---

### 2.4 Gamification (RPG)

#### UC-17 — Create RPG Character
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated; no character exists yet |
| **Postcondition** | CHARACTER + CHARACTER_STAT created at level 1 |
| **Description** | On first use, user creates an RPG character by choosing a class (Warrior, Mage, Rogue, etc.). |
| **Main Flow** | 1. Prompt shown on first login<br>2. User selects class<br>3. System creates CHARACTER record<br>4. Initial CHARACTER_STAT set |

#### UC-18 — Earn XP & Level Up
| Field | Value |
|---|---|
| **Actor** | System |
| **Precondition** | Workout session completed |
| **Postcondition** | `current_xp` and `level` updated; stats incremented |
| **Description** | After completing a workout session, the system awards XP, updates stats, and levels up the character if the threshold is crossed. |
| **Main Flow** | 1. Session marked complete<br>2. System calculates XP reward<br>3. `current_xp` updated<br>4. Level-up check triggered<br>5. Stats incremented |

#### UC-19 — Unlock Achievement
| Field | Value |
|---|---|
| **Actor** | System |
| **Precondition** | User reaches `required_xp` threshold |
| **Postcondition** | USER_ACHIEVEMENT record created with `unlocked_at` |
| **Description** | System evaluates achievement conditions (XP milestones) and creates a USER_ACHIEVEMENT record when a threshold is met. |
| **Main Flow** | 1. XP updated<br>2. System checks all ACHIEVEMENT thresholds<br>3. Unearned achievements evaluated<br>4. Matching achievements unlocked<br>5. Notification sent to user |

---

### 2.5 AI Coach

#### UC-20 — Request AI Workout Plan
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User has a profile and >= 1 session in history |
| **Postcondition** | AI_WORKOUT_PLAN record created; `is_accepted = false` |
| **Description** | User requests a personalised workout plan. The system sends profile and history to the AI model and stores the response. |
| **Main Flow** | 1. User taps Generate Plan<br>2. System collects profile & session history<br>3. Prompt sent to AI model<br>4. Response stored as `raw_ai_response`<br>5. Plan presented to user |

#### UC-21 — Accept / Reject AI Plan
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | AI_WORKOUT_PLAN record exists |
| **Postcondition** | `is_accepted` updated; optionally WORKOUT_PLAN created |
| **Description** | User reviews the generated plan and either accepts it (creating a WORKOUT_PLAN) or rejects it. |
| **Main Flow** | 1. User reviews AI plan<br>2. Taps Accept or Reject<br>3. `is_accepted` flag updated<br>4. If accepted: WORKOUT_PLAN created from AI data |

---

### 2.6 Nutrition & Diet

#### UC-22 — Get Daily Nutrition Norm
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated; complete profile (age, weight, height, gender, fitness_goal) |
| **Postcondition** | Daily macro norms calculated and returned |
| **Description** | System calculates the user's daily calorie, protein, fat, and carb targets based on their profile data. |
| **Main Flow** | 1. User requests `/nutrition/norm`<br>2. System loads user profile<br>3. System calculates daily norm using profile data<br>4. Returns calories, protein_g, fat_g, carbs_g |
| **Error** | If profile is incomplete (missing any required field) -> `400 Bad Request` with list of missing fields |

#### UC-23 — View Day Overview
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated; complete profile |
| **Postcondition** | Overview returned with norm, consumed, and remaining macros |
| **Description** | User views a summary of their nutrition for a specific day, showing targets vs actual consumption. |
| **Main Flow** | 1. User requests `/nutrition/overview?target_date=YYYY-MM-DD`<br>2. System calculates daily norm<br>3. System sums consumed macros from all MEAL_ENTRY records for that date<br>4. Returns norm, consumed, and remaining (norm - consumed) |

#### UC-24 — Log Meal Entry
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated; FOOD record exists |
| **Postcondition** | MEAL_ENTRY created; remaining macros recalculated |
| **Description** | User adds a food item to their daily diary, specifying meal type and weight in grams. |
| **Main Flow** | 1. User submits `food_id`, `meal_type`, `weight_grams`, optional `target_date`<br>2. System finds or creates DAILY_DIARY for the date<br>3. MEAL_ENTRY created<br>4. Remaining macros recalculated<br>5. Returns meal_entry_id, target_date, and remaining macros |

#### UC-25 — Delete Meal Entry
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | MEAL_ENTRY exists and belongs to user |
| **Postcondition** | MEAL_ENTRY deleted; remaining macros recalculated |
| **Description** | User removes a previously logged meal entry from their diary. |
| **Main Flow** | 1. User requests deletion of meal entry<br>2. System validates ownership<br>3. MEAL_ENTRY deleted<br>4. Remaining macros recalculated<br>5. Returns deleted_meal_entry_id, target_date, and updated remaining macros |

#### UC-26 — Update Daily Diary
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated |
| **Postcondition** | DAILY_DIARY record updated |
| **Description** | User updates water intake and personal notes for a specific day. |
| **Main Flow** | 1. User submits `target_date` with optional `water_ml` and/or `notes`<br>2. System finds or creates DAILY_DIARY for the date<br>3. Fields updated<br>4. Updated diary returned |

---

## 3. Functional Requirements

### 3.1 Identity & Profile

| ID | Name | Description |
|---|---|---|
| FR-01 | User Registration | The system shall allow users to register with a unique email address and a securely hashed (Argon2) password. A verification email shall be sent upon registration. |
| FR-02 | Authentication | The system shall authenticate users via email/password and issue a JWT access token (1h) and refresh token (7d). If 2FA is enabled, a temporary token shall be issued first. |
| FR-03 | Profile Management | The system shall allow authenticated users to create and update USER_PROFILE with `weight`, `height`, `age`, `gender`, and `fitness_goal`. BMI shall be calculated on read. |
| FR-04 | OAuth Authentication | The system shall support login via Google, GitHub, and Facebook OAuth providers, with CSRF-protected state stored in Redis. |
| FR-05 | Email Verification | The system shall send verification emails on registration and allow users to verify via a token link. |
| FR-06 | Password Reset | The system shall allow users to request a password reset email and set a new password via a token link. |
| FR-07 | Two-Factor Auth | The system shall support TOTP-based 2FA with QR code setup, confirmation, and verification on login. |
| FR-08 | Session Management | The system shall manage refresh tokens stored in DB with device info, supporting per-token and bulk revocation. |

### 3.2 Social & Plans

| ID | Name | Description |
|---|---|---|
| FR-09 | Plan CRUD | The system shall allow authenticated users to create, read, update, and delete workout plans with title, description, and public/private visibility. |
| FR-10 | Community Feed | The system shall expose a paginated feed of public workout plans sortable by recency. |
| FR-11 | Social Interactions | The system shall support liking, commenting on, and bookmarking workout plans; each interaction shall be stored as an atomic database record. |

### 3.3 Activity & Tracking

| ID | Name | Description |
|---|---|---|
| FR-12 | Session Logging | The system shall create a WORKOUT_SESSION with a `started_at` timestamp when a user begins a workout, and record `ended_at` on completion. Sessions can optionally link to a PLAN_TRAINING. |
| FR-13 | Exercise Tracking | The system shall record individual exercises within a session as EXERCISE_SESSION records, each containing ordered WORKOUT_SET entries with `reps` and `weight`. |
| FR-14 | Muscle Groups | The system shall maintain a MUSCLE_GROUP catalog. Exercises reference a primary muscle group via FK and secondary muscle groups via a junction table (EXERCISE_MUSCLE_GROUP). |
| FR-15 | Exercise Management | The system shall allow creating and searching exercises with primary and secondary muscle group associations and pagination. |
| FR-16 | Plan Trainings | The system shall support structured plan trainings within workout plans, each with a name, optional weekday, order, and exercise templates with target sets, reps, and weight percentages. |
| FR-17 | Personal Records | The system shall track personal records per (user, exercise) pair with upsert semantics and a `recorded_at` timestamp. |

### 3.4 Nutrition & Diet

| ID | Name | Description |
|---|---|---|
| FR-18 | Daily Diary | The system shall create or retrieve a DAILY_DIARY record per user per calendar date and allow updating of `water_ml` and `notes`. |
| FR-19 | Meal Logging | The system shall allow users to add MEAL_ENTRY records to a diary, specifying FOOD item, meal type, and weight in grams; macros shall be computed automatically. |
| FR-20 | Food Database | The system shall maintain a FOOD database with calorie and macronutrient data per 100g, including fdc_id, brand_name, and data_type fields. Food portions shall be defined with measure units and gram weights. |
| FR-21 | Daily Norm | The system shall calculate daily macro norms (calories, protein, fat, carbs) based on user profile data (age, weight, height, gender, fitness_goal). |
| FR-22 | Day Overview | The system shall provide a day overview showing calculated norm, consumed macros, and remaining macros for a given date. |

### 3.5 Gamification

| ID | Name | Description |
|---|---|---|
| FR-23 | Character Creation | The system shall create a CHARACTER record with a chosen class and an associated CHARACTER_STAT record upon first access of the gamification module. |
| FR-24 | XP Awarding | The system shall calculate and award XP to a user's character upon completion of a workout session according to a defined XP formula. |
| FR-25 | Level Up | The system shall automatically increment a character's `level` and update CHARACTER_STAT values when `current_xp` meets or exceeds the level threshold. |
| FR-26 | Achievements | The system shall evaluate all ACHIEVEMENT thresholds after each XP update and create USER_ACHIEVEMENT records for newly met conditions. |

### 3.6 AI Coach

| ID | Name | Description |
|---|---|---|
| FR-27 | Plan Generation | The system shall send user profile and session history to a configurable external AI model and persist the full response as an AI_WORKOUT_PLAN with `raw_ai_response`. |
| FR-28 | Plan Acceptance | The system shall allow users to accept or reject an AI_WORKOUT_PLAN; accepting shall create a corresponding WORKOUT_PLAN record from the AI data. |

### 3.7 Admin

| ID | Name | Description |
|---|---|---|
| FR-29 | Food Verification | The system shall provide admin-level endpoints to verify or reject submitted food entries via the `is_verified` flag. |
| FR-30 | Exercise Management | The system shall allow admins to create, update, and delete EXERCISE records with primary muscle group (FK) and secondary muscle group associations (junction table). |

---

## 4. Non-Functional Requirements

> **Priority levels:** Critical · High · Medium

### 4.1 Performance

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-01 | API Response Time | High | 95th-percentile response time for all REST endpoints shall be <= 300 ms under normal load (up to 500 concurrent users). |
| NFR-02 | Database Query Time | High | All database queries shall execute in <= 100 ms; queries returning > 1 000 rows shall use pagination. |
| NFR-03 | AI Plan Generation | Medium | AI-generated workout plans shall be returned within 10 seconds; the request shall be handled asynchronously with a status-polling endpoint. |

### 4.2 Security

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-04 | Password Storage | Critical | Passwords shall be stored exclusively as Argon2 hashes; plaintext passwords shall never be logged or persisted. |
| NFR-05 | JWT Security | Critical | JWT access tokens shall use HS256 signing, expire within 1 hour, and be validated on every authenticated request. Refresh tokens expire in 7 days and are stored in the database. |
| NFR-06 | Input Validation | High | All request bodies shall be validated via Pydantic schemas before processing; malformed inputs shall return HTTP 422. |
| NFR-07 | Authorization | High | Users shall only access or modify resources they own; plan authors control edit/delete; admin endpoints require `role = admin`. |
| NFR-08 | API Key Protection | High | The AI API key shall be stored exclusively in environment variables, never committed to version control or returned in any API response. |
| NFR-09 | Rate Limiting | High | IP-based rate limiting shall be enforced via Redis with sliding window. Configurable limits per endpoint (e.g., 3/hour for password reset, 5/min for 2FA verification). |
| NFR-10 | OAuth Security | High | OAuth state tokens shall be stored in Redis with 5-minute TTL and consumed on use to prevent CSRF attacks. |

### 4.3 Reliability & Availability

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-11 | Uptime Target | High | The application shall target 99.5% monthly uptime excluding planned maintenance windows. |
| NFR-12 | DB Health Check | High | Docker Compose shall enforce a PostgreSQL health check before starting the API container; the API shall retry DB connection up to 5 times on startup. |
| NFR-13 | Graceful Degradation | Medium | If the external AI service is unavailable, the system shall return a user-friendly error without affecting any other application features. |
| NFR-14 | Data Durability | High | PostgreSQL data shall be persisted via a named Docker volume; database backup strategy shall be configurable via environment variables. |

### 4.4 Scalability

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-15 | Horizontal Scaling | Medium | The FastAPI application shall be stateless to allow horizontal scaling behind a load balancer without session affinity requirements. |
| NFR-16 | Async I/O | High | All database operations shall use SQLAlchemy async sessions with the asyncpg driver; no synchronous blocking calls shall appear in request handlers. |
| NFR-17 | Pagination | Medium | All list endpoints (plans, exercises, sessions, diary entries) shall implement offset-based pagination with a configurable max page size of 100 items. |

### 4.5 Maintainability

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-18 | Migration Management | High | All schema changes shall be managed via Alembic versioned migrations; no manual DDL changes to the production database are permitted. |
| NFR-19 | Layered Architecture | High | The codebase shall follow the layered pattern: Routes -> Services -> Repositories -> ORM Models; business logic shall not reside in route handlers. |
| NFR-20 | Environment Config | High | All configuration values (DB URL, secret key, AI key) shall be externalised via environment variables using `pydantic-settings`; no hardcoded secrets. |
| NFR-21 | API Documentation | Medium | FastAPI shall auto-generate OpenAPI 3.x documentation (Swagger UI at `/docs`, ReDoc at `/redoc`) reflecting all current endpoints and schemas. |

### 4.6 Usability & Compatibility

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-22 | REST Conventions | Medium | The API shall follow REST conventions: correct HTTP verbs (GET/POST/PUT/PATCH/DELETE), meaningful status codes (200/201/204/400/401/403/404/409/422/500), and JSON bodies. |
| NFR-23 | Datetime Format | Medium | All datetime values in requests and responses shall use ISO 8601 format (UTC); non-ISO datetime strings shall be rejected with HTTP 422. |
| NFR-24 | CORS | Medium | The API shall expose configurable CORS headers to allow integration with browser-based and mobile front-end clients. |

### 4.7 Data Integrity

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-25 | Referential Integrity | Critical | All foreign key relationships shall be enforced at the database level via PostgreSQL constraints; orphan records shall not be permitted. |
| NFR-26 | Unique Constraints | High | `USER.email` shall have a UNIQUE constraint; `(user_id, exercise_id)` in `PERSONAL_RECORD`, `(plan_id, user_id)` pairs in `PLAN_LIKE` and `PLAN_BOOKMARK`, and `(user_id, target_date)` in `DAILY_DIARY` shall also be unique at the database level. |
| NFR-27 | Macro Validation | Medium | FOOD macro values (protein + carbs + fat per 100 g) shall be validated so their sum does not exceed 100 g; values approaching the limit shall generate a warning. |

---

## 5. Requirements Traceability Summary

| Domain | Use Cases | Functional Reqs | Non-Functional Reqs |
|---|---|---|---|
| Identity & Profile | UC-01 — UC-07 | FR-01 — FR-08 | NFR-04, NFR-05, NFR-06, NFR-07, NFR-09, NFR-10 |
| Social & Plans | UC-08 — UC-10 | FR-09 — FR-11 | NFR-01, NFR-17, NFR-22 |
| Activity & Tracking | UC-11 — UC-16 | FR-12 — FR-17 | NFR-02, NFR-16 |
| Gamification (RPG) | UC-17 — UC-19 | FR-23 — FR-26 | NFR-02, NFR-25, NFR-26 |
| AI Coach | UC-20 — UC-21 | FR-27 — FR-28 | NFR-03, NFR-08, NFR-13 |
| Nutrition & Diet | UC-22 — UC-26 | FR-18 — FR-22 | NFR-26, NFR-27 |
| Admin | — | FR-29, FR-30 | NFR-07 |
| Cross-cutting | — | — | NFR-11—14, NFR-15—16, NFR-18—21, NFR-23—24 |
