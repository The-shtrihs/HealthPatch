# Health Patch — Software Requirements Specification

> **Version 1.0 — 2025**
> Use Cases · Functional Requirements · Non-Functional Requirements

---

## 1. Introduction

Health Patch is a full-stack fitness platform combining workout tracking, nutrition logging, RPG gamification, AI coaching, and social community features. This document defines the system's use cases, functional requirements (FR), and non-functional requirements (NFR) to guide development, testing, and stakeholder review.

**Tech stack:** FastAPI (Python 3.11+) · SQLAlchemy async ORM · Alembic · PostgreSQL 17 · Docker Compose

---

## 2. Use Cases

### 2.1 Identity & Profile

#### UC-01 — Register Account
| Field | Value |
|---|---|
| **Actor** | Guest |
| **Precondition** | User is not registered |
| **Postcondition** | Account created; user can log in |
| **Description** | A new user creates an account by providing email and password. The system validates uniqueness of email, hashes the password, and creates a USER record. |
| **Main Flow** | 1. User submits email & password<br>2. System validates email uniqueness<br>3. System hashes password (bcrypt)<br>4. USER record created<br>5. Confirmation returned |

#### UC-02 — Log In
| Field | Value |
|---|---|
| **Actor** | Registered User |
| **Precondition** | Valid account exists |
| **Postcondition** | JWT auth token issued |
| **Description** | A registered user authenticates with email and password to receive a session token for subsequent API calls. |
| **Main Flow** | 1. User submits credentials<br>2. System verifies bcrypt hash<br>3. JWT token generated<br>4. Token returned to client |

#### UC-03 — Manage Profile
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated |
| **Postcondition** | Profile saved with latest values |
| **Description** | User updates personal data: weight, height, and fitness goal in USER_PROFILE. |
| **Main Flow** | 1. User opens profile settings<br>2. Edits weight / height / goal<br>3. Submits form<br>4. System persists USER_PROFILE |

---

### 2.2 Social & Plans

#### UC-04 — Create Workout Plan
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated |
| **Postcondition** | WORKOUT_PLAN record created |
| **Description** | User creates a new workout plan with title, description, and visibility setting (public / private). |
| **Main Flow** | 1. User fills plan form<br>2. Submits plan data<br>3. System saves WORKOUT_PLAN<br>4. Plan appears in user's dashboard |

#### UC-05 — Browse Public Plans
| Field | Value |
|---|---|
| **Actor** | Any User |
| **Precondition** | None (guest access allowed) |
| **Postcondition** | Paginated list of plans returned |
| **Description** | User browses the community feed of public workout plans, applying filters by muscle group or popularity. |
| **Main Flow** | 1. User opens community feed<br>2. Applies optional filters<br>3. System returns paginated list of `is_public=true` plans |

#### UC-06 — Like / Comment / Bookmark Plan
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated; plan exists |
| **Postcondition** | PLAN_LIKE / PLAN_COMMENT / PLAN_BOOKMARK record created |
| **Description** | User interacts with a community plan by liking it, leaving a comment, or saving it to bookmarks. |
| **Main Flow** | 1. User opens a plan<br>2. Taps Like, Comment, or Bookmark<br>3. System records interaction<br>4. Counters update in real time |

---

### 2.3 Activity & Tracking

#### UC-07 — Start Workout Session
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated |
| **Postcondition** | WORKOUT_SESSION created with `started_at` timestamp |
| **Description** | User starts a new workout session, optionally linking it to an existing workout plan. |
| **Main Flow** | 1. User selects plan (optional)<br>2. Taps Start Workout<br>3. System creates WORKOUT_SESSION<br>4. Timer begins |

#### UC-08 — Log Exercise Sets
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | Active WORKOUT_SESSION exists |
| **Postcondition** | EXERCISE_SESSION and WORKOUT_SET records created |
| **Description** | During a session, user logs individual exercises with sets, reps, and weight. |
| **Main Flow** | 1. User selects exercise<br>2. Enters sets, reps, weight<br>3. System creates EXERCISE_SESSION + WORKOUT_SET records<br>4. Progress displayed |

#### UC-09 — Sync Wearable Device
| Field | Value |
|---|---|
| **Actor** | Authenticated User / System |
| **Precondition** | User has a connected wearable device |
| **Postcondition** | DEVICE_SYNC_METRIC record created for `sync_date` |
| **Description** | User or background service syncs wearable metrics (steps, heart rate, sleep hours). |
| **Main Flow** | 1. Sync triggered (manual or scheduled)<br>2. Device data retrieved<br>3. System stores DEVICE_SYNC_METRIC<br>4. Dashboard updated |

---

### 2.4 Gamification (RPG)

#### UC-10 — Create RPG Character
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated; no character exists yet |
| **Postcondition** | CHARACTER + CHARACTER_STAT created at level 1 |
| **Description** | On first use, user creates an RPG character by choosing a class (Warrior, Mage, Rogue, etc.). |
| **Main Flow** | 1. Prompt shown on first login<br>2. User selects class<br>3. System creates CHARACTER record<br>4. Initial CHARACTER_STAT set |

#### UC-11 — Earn XP & Level Up
| Field | Value |
|---|---|
| **Actor** | System |
| **Precondition** | Workout session completed |
| **Postcondition** | `current_xp` and `level` updated; stats incremented |
| **Description** | After completing a workout session, the system awards XP, updates stats, and levels up the character if the threshold is crossed. |
| **Main Flow** | 1. Session marked complete<br>2. System calculates XP reward<br>3. `current_xp` updated<br>4. Level-up check triggered<br>5. Stats incremented |

#### UC-12 — Unlock Achievement
| Field | Value |
|---|---|
| **Actor** | System |
| **Precondition** | User reaches `required_xp` threshold |
| **Postcondition** | USER_ACHIEVEMENT record created with `unlocked_at` |
| **Description** | System evaluates achievement conditions (XP milestones) and creates a USER_ACHIEVEMENT record when a threshold is met. |
| **Main Flow** | 1. XP updated<br>2. System checks all ACHIEVEMENT thresholds<br>3. Unearned achievements evaluated<br>4. Matching achievements unlocked<br>5. Notification sent to user |

---

### 2.5 AI Coach

#### UC-13 — Request AI Workout Plan
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User has a profile and ≥ 1 session in history |
| **Postcondition** | AI_WORKOUT_PLAN record created; `is_accepted = false` |
| **Description** | User requests a personalised workout plan. The system sends profile and history to the AI model and stores the response. |
| **Main Flow** | 1. User taps Generate Plan<br>2. System collects profile & session history<br>3. Prompt sent to AI model<br>4. Response stored as `raw_ai_response`<br>5. Plan presented to user |

#### UC-14 — Accept / Reject AI Plan
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | AI_WORKOUT_PLAN record exists |
| **Postcondition** | `is_accepted` updated; optionally WORKOUT_PLAN created |
| **Description** | User reviews the generated plan and either accepts it (creating a WORKOUT_PLAN) or rejects it. |
| **Main Flow** | 1. User reviews AI plan<br>2. Taps Accept or Reject<br>3. `is_accepted` flag updated<br>4. If accepted: WORKOUT_PLAN created from AI data |

---

### 2.6 Nutrition & Diet

#### UC-15 — Log Daily Nutrition
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated |
| **Postcondition** | DAILY_DIARY record created or updated |
| **Description** | User opens or creates a DAILY_DIARY for today and logs water intake and personal notes. |
| **Main Flow** | 1. User opens Nutrition tab<br>2. System finds/creates DAILY_DIARY for today<br>3. User enters `water_ml` and notes<br>4. Record saved |

#### UC-16 — Log Meal Entry
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | DAILY_DIARY exists; FOOD record exists |
| **Postcondition** | MEAL_ENTRY created; macros calculated |
| **Description** | User adds a food item to a meal in the daily diary, specifying meal type and weight in grams. |
| **Main Flow** | 1. User searches food database<br>2. Selects food item<br>3. Chooses meal type & weight in grams<br>4. System creates MEAL_ENTRY<br>5. Daily macro totals recalculated |

#### UC-17 — Browse Food Database
| Field | Value |
|---|---|
| **Actor** | Authenticated User |
| **Precondition** | User authenticated |
| **Postcondition** | List of matching FOOD records returned |
| **Description** | User searches the food database with verified entries to find calorie and macronutrient information. |
| **Main Flow** | 1. User types food name<br>2. System queries FOOD table (verified only)<br>3. Results shown with macro data per 100 g<br>4. User selects item to log or view details |

---

## 3. Functional Requirements

### 3.1 Identity & Profile

| ID | Name | Description |
|---|---|---|
| FR-01 | User Registration | The system shall allow users to register with a unique email address and a securely hashed (bcrypt) password. |
| FR-02 | Authentication | The system shall authenticate users via email/password and issue a JWT token valid for a configurable duration. |
| FR-03 | Profile Management | The system shall allow authenticated users to create and update USER_PROFILE with `weight`, `height`, and `fitness_goal`. |

### 3.2 Social & Plans

| ID | Name | Description |
|---|---|---|
| FR-04 | Plan CRUD | The system shall allow authenticated users to create, read, update, and delete workout plans with title, description, and public/private visibility. |
| FR-05 | Community Feed | The system shall expose a paginated feed of public workout plans filterable by muscle group and sortable by popularity or recency. |
| FR-06 | Social Interactions | The system shall support liking, commenting on, and bookmarking workout plans; each interaction shall be stored as an atomic database record. |

### 3.3 Activity & Tracking

| ID | Name | Description |
|---|---|---|
| FR-07 | Session Logging | The system shall create a WORKOUT_SESSION with a `started_at` timestamp when a user begins a workout, and record `ended_at` on completion. |
| FR-08 | Exercise Tracking | The system shall record individual exercises within a session as EXERCISE_SESSION records, each containing ordered WORKOUT_SET entries with `reps` and `weight`. |
| FR-09 | Device Sync | The system shall accept and store wearable device metrics (steps, heart rate, sleep hours) as DEVICE_SYNC_METRIC records keyed by user and date. |

### 3.4 Gamification

| ID | Name | Description |
|---|---|---|
| FR-10 | Character Creation | The system shall create a CHARACTER record with a chosen class and an associated CHARACTER_STAT record upon first access of the gamification module. |
| FR-11 | XP Awarding | The system shall calculate and award XP to a user's character upon completion of a workout session according to a defined XP formula. |
| FR-12 | Level Up | The system shall automatically increment a character's `level` and update CHARACTER_STAT values when `current_xp` meets or exceeds the level threshold. |
| FR-13 | Achievements | The system shall evaluate all ACHIEVEMENT thresholds after each XP update and create USER_ACHIEVEMENT records for newly met conditions. |

### 3.5 AI Coach

| ID | Name | Description |
|---|---|---|
| FR-14 | Plan Generation | The system shall send user profile and session history to a configurable external AI model and persist the full response as an AI_WORKOUT_PLAN with `raw_ai_response`. |
| FR-15 | Plan Acceptance | The system shall allow users to accept or reject an AI_WORKOUT_PLAN; accepting shall create a corresponding WORKOUT_PLAN record from the AI data. |

### 3.6 Nutrition & Diet

| ID | Name | Description |
|---|---|---|
| FR-16 | Daily Diary | The system shall create or retrieve a DAILY_DIARY record per user per calendar date and allow updating of `water_ml` and `notes`. |
| FR-17 | Meal Logging | The system shall allow users to add MEAL_ENTRY records to a diary, specifying FOOD item, meal type, and weight in grams; macros shall be computed automatically. |
| FR-18 | Food Database | The system shall maintain a FOOD database with calorie and macronutrient data per 100 g; only admin-verified entries (`is_verified = true`) shall be shown to users. |

### 3.7 Admin

| ID | Name | Description |
|---|---|---|
| FR-19 | Food Verification | The system shall provide admin-level endpoints to verify or reject submitted food entries via the `is_verified` flag. |
| FR-20 | Exercise Management | The system shall allow admins to create, update, and delete EXERCISE records including `muscle_group` classification. |

---

## 4. Non-Functional Requirements

> **Priority levels:** 🔴 Critical · 🟠 High · 🟡 Medium

### 4.1 Performance

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-01 | API Response Time | 🟠 High | 95th-percentile response time for all REST endpoints shall be ≤ 300 ms under normal load (up to 500 concurrent users). |
| NFR-02 | Database Query Time | 🟠 High | All database queries shall execute in ≤ 100 ms; queries returning > 1 000 rows shall use pagination. |
| NFR-03 | AI Plan Generation | 🟡 Medium | AI-generated workout plans shall be returned within 10 seconds; the request shall be handled asynchronously with a status-polling endpoint. |
| NFR-04 | Device Sync Throughput | 🟡 Medium | The system shall handle burst device sync ingestion of up to 1 000 records per minute without performance degradation. |

### 4.2 Security

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-05 | Password Storage | 🔴 Critical | Passwords shall be stored exclusively as bcrypt hashes (cost factor ≥ 12); plaintext passwords shall never be logged or persisted. |
| NFR-06 | JWT Security | 🔴 Critical | JWT tokens shall use HS256 or RS256 signing, expire within 24 hours, and be validated on every authenticated request. |
| NFR-07 | Input Validation | 🟠 High | All request bodies shall be validated via Pydantic schemas before processing; malformed inputs shall return HTTP 422. |
| NFR-08 | Authorization | 🟠 High | Users shall only access or modify resources they own; plan authors control edit/delete; admin endpoints require `role = admin`. |
| NFR-09 | AI API Key Protection | 🟠 High | The AI API key shall be stored exclusively in environment variables, never committed to version control or returned in any API response. |

### 4.3 Reliability & Availability

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-10 | Uptime Target | 🟠 High | The application shall target 99.5% monthly uptime excluding planned maintenance windows. |
| NFR-11 | DB Health Check | 🟠 High | Docker Compose shall enforce a PostgreSQL health check before starting the API container; the API shall retry DB connection up to 5 times on startup. |
| NFR-12 | Graceful Degradation | 🟡 Medium | If the external AI service is unavailable, the system shall return a user-friendly error without affecting any other application features. |
| NFR-13 | Data Durability | 🟠 High | PostgreSQL data shall be persisted via a named Docker volume; database backup strategy shall be configurable via environment variables. |

### 4.4 Scalability

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-14 | Horizontal Scaling | 🟡 Medium | The FastAPI application shall be stateless to allow horizontal scaling behind a load balancer without session affinity requirements. |
| NFR-15 | Async I/O | 🟠 High | All database operations shall use SQLAlchemy async sessions with the asyncpg driver; no synchronous blocking calls shall appear in request handlers. |
| NFR-16 | Pagination | 🟡 Medium | All list endpoints (plans, exercises, diary entries) shall implement cursor- or offset-based pagination with a configurable max page size of 100 items. |

### 4.5 Maintainability

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-17 | Migration Management | 🟠 High | All schema changes shall be managed via Alembic versioned migrations; no manual DDL changes to the production database are permitted. |
| NFR-18 | Layered Architecture | 🟠 High | The codebase shall follow the layered pattern: Routers → Services → ORM Models; business logic shall not reside in route handlers. |
| NFR-19 | Environment Config | 🟠 High | All configuration values (DB URL, secret key, AI key) shall be externalised via environment variables using `pydantic-settings`; no hardcoded secrets. |
| NFR-20 | API Documentation | 🟡 Medium | FastAPI shall auto-generate OpenAPI 3.x documentation (Swagger UI at `/docs`, ReDoc at `/redoc`) reflecting all current endpoints and schemas. |

### 4.6 Usability & Compatibility

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-21 | REST Conventions | 🟡 Medium | The API shall follow REST conventions: correct HTTP verbs (GET/POST/PUT/DELETE), meaningful status codes (200/201/400/401/403/404/422/500), and JSON bodies. |
| NFR-22 | Datetime Format | 🟡 Medium | All datetime values in requests and responses shall use ISO 8601 format (UTC); non-ISO datetime strings shall be rejected with HTTP 422. |
| NFR-23 | CORS | 🟡 Medium | The API shall expose configurable CORS headers to allow integration with browser-based and mobile front-end clients. |

### 4.7 Data Integrity

| ID | Name | Priority | Description |
|---|---|---|---|
| NFR-24 | Referential Integrity | 🔴 Critical | All foreign key relationships shall be enforced at the database level via PostgreSQL constraints; orphan records shall not be permitted. |
| NFR-25 | Unique Constraints | 🟠 High | `USER.email` shall have a UNIQUE constraint; `(plan_id, user_id)` pairs in PLAN_LIKE and PLAN_BOOKMARK shall also be unique at the database level. |
| NFR-26 | Macro Validation | 🟡 Medium | FOOD macro values (protein + carbs + fat per 100 g) shall be validated so their sum does not exceed 100 g; values approaching the limit shall generate a warning. |

---

## 5. Requirements Traceability Summary

| Domain | Use Cases | Functional Reqs | Non-Functional Reqs |
|---|---|---|---|
| Identity & Profile | UC-01, UC-02, UC-03 | FR-01, FR-02, FR-03 | NFR-05, NFR-06, NFR-07, NFR-08 |
| Social & Plans | UC-04, UC-05, UC-06 | FR-04, FR-05, FR-06 | NFR-01, NFR-16, NFR-21 |
| Activity & Tracking | UC-07, UC-08, UC-09 | FR-07, FR-08, FR-09 | NFR-02, NFR-04, NFR-15 |
| Gamification (RPG) | UC-10, UC-11, UC-12 | FR-10, FR-11, FR-12, FR-13 | NFR-02, NFR-24, NFR-25 |
| AI Coach | UC-13, UC-14 | FR-14, FR-15 | NFR-03, NFR-09, NFR-12 |
| Nutrition & Diet | UC-15, UC-16, UC-17 | FR-16, FR-17, FR-18 | NFR-26, NFR-25 |
| Admin | — | FR-19, FR-20 | NFR-08 |
| Cross-cutting | — | — | NFR-10–11, NFR-13–15, NFR-17–23 |
