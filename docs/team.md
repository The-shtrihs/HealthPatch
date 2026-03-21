# 🤝 Health Patch — Team

> This document describes the team composition, role distribution, areas of responsibility, communication tools, corporate ethics, and a comparison with an ideal IT team.

---

## 1. Team Composition

| # | Name | GitHub | Role | Domain |
|---|------|--------|------|--------|
| 1 | Daniil Marchenko | [@Alysseum17](https://github.com/Alysseum17) | Backend Developer | Identity & Auth |
| 2 | Maksym Kramarenko | [@Maks9m](https://github.com/Maks9m) | Backend Developer | Activity & Workouts |
| 3 | Mikhailo Loban | [@LobanMihajlo](https://github.com/LobanMihajlo) | Backend Developer | Nutrition & Diet |
| 4 | Oleksandr Bondarchuk | [@0utlaw0](https://github.com/0utlaw0) | Project Manager | Everything and nothing |

---

## 2. Role Distribution & Areas of Responsibility

### Working Principle

Each developer is the **full owner of their domain** — they design the module, write models, schemas, services, routers, and migrations from start to finish. There are no seniors or juniors — only equal contributors with clearly defined boundaries.

---

### 👤 Daniil Marchenko — Identity & Auth

**Area of responsibility:**
- User registration and authentication (JWT)
- Security: password hashing (bcrypt), token validation
- User profile management (`USER`, `USER_PROFILE`)
- Authentication middleware for the entire API
- Protection of other domains' endpoints (`get_current_user` dependency)
- OAuth authentication
- 2FA authentication

**Boundary:** ends where other domains' business logic begins. Provides the auth dependency — does not implement other modules' features.

---

### 🏋️ Maksym Kramarenko — Activity & Workouts

**Area of responsibility:**
- Exercise management (`EXERCISE`)
- Workout session logging (`WORKOUT_SESSION`, `EXERCISE_SESSION`, `WORKOUT_SET`)
- Workout plans and their structure (`WORKOUT_PLAN`)
- Wearable device sync (`DEVICE_SYNC_METRIC`)

**Boundary:** ends after saving the session and awarding XP. Does not handle nutrition display or authentication.

---

### 🥗 Mikhailo Loban — Nutrition & Diet

**Area of responsibility:**
- Food database (`FOOD`) and admin verification
- Daily nutrition diary (`DAILY_DIARY`)
- Meal entries and macro calculation (`MEAL_ENTRY`)
- Food search and filtering

**Boundary:** ends after saving the nutrition record. Does not handle workouts or user profiles.

---

### 📋 Oleksandr Bondarchuk — Project Manager

**Area of responsibility:**
- Task coordination and deadline management
- Communication between team members
- Writing documentation and README
- Making architectural decisions after team discussion
- Approving Pull Requests *(if he manages to open GitHub)*

**Boundary:** infinite and blurry, as with any PM.

---

## 3. Digital Communication Tools

| Tool | Type | Purpose |
|------|------|---------|
| **Telegram** | Asynchronous | Daily communication, discussions, scheduling meetings |
| **Discord** | Synchronous | Voice calls for pair work, code discussions |
| **GitHub** | Asynchronous | Code review, PRs, Issues, CI/CD |
| **GitHub Actions** | Automated | CI pipeline: Ruff linting, auto-fix |

### Communication Rules

- Telegram — for quick questions and coordination. Write **one complete message**, not word by word.
- Discord — when something needs to be discussed verbally or reviewed together. Agree on time in TG first.
- Decisions made in voice calls — must be documented in TG or GitHub Issues.
- Reply to messages within **24 hours** on working days.

---

## 4. Git Policy

```
main ← protected
  ↑
  └── feature/[domain]-[short-description]
        ↑
        └── (developer writes code here)
```

**Rules:**

- ❌ Direct push to `main` — **forbidden**
- ✅ Only Pull Requests from a separate branch
- ✅ PR must pass **CI/CD** (Ruff linting)
- ✅ At least **1 approval** from another team member
- 📝 Branch naming: `feature/auth-jwt`, `fix/nutrition-macros`, `chore/update-readme`
- 📝 Commit messages: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`

---

## 5. Corporate Ethics

### Team Values

**Respect for time** — everyone respects each other's time. If you're running late on something — say so in advance, not after the deadline.

**Transparency** — if something isn't working or there's a blocker — post it in TG immediately, don't wait until the end of the sprint.

**Equality** — no hierarchy between developers. Any technical decision can be challenged with solid arguments.

**Quality over speed** — better to do less, but do it right. Hacks and "we'll fix it later" are only acceptable with a good reason and a GitHub Issue to track it.

**Constructive criticism** — we criticize the code, not the person. In code reviews: explain *why* you're requesting a change, don't just say "rewrite this."

### Code Review Rules

- Don't stay silent when approving — if you have remarks, write them.
- One approval means: "I read this, I understand what's going on, and I see no critical issues."
- Never approve your own PR.
- If a PR is too large — you can ask the author to split it into smaller parts.

### Forbidden

- Pushing directly to `main`
- Merging a PR without approval
- Ignoring review comments for more than 2 days
- Writing code without Pydantic type validation on incoming data
- Hardcoding secrets in code

---

## 6. Comparative Analysis: Our Team vs. Ideal IT Team

| Role | Ideal Team | Our Team | Status |
|------|-----------|----------|--------|
| Product Owner / Business Lead | ✅ Dedicated person | ❌ Absent | Partially covered by PM |
| Project Manager | ✅ Dedicated person | ✅ Oleksandr Bondarchuk | ✅ Present |
| Scrum Master / Agile Coach | ✅ Dedicated person | ❌ Absent | Responsibilities shared across team |
| Backend Developer | ✅ Multiple people | ✅ 3 developers | ✅ Present |
| Frontend Developer | ✅ Present | ❌ Absent | Out of scope for current stage |
| QA Engineer | ✅ Present | ❌ Absent | Each developer tests their own domain |
| DevOps Engineer | ✅ Present | ❌ Absent | Docker Compose + GitHub Actions cover the basics |
| UI/UX Designer | ✅ Present | ❌ Absent | Out of scope |
| Data Engineer / ML | ✅ When needed | ❌ Absent | Out of scope |

### Conclusion

The team is not "ideal" in the classical sense — this is a typical **micro-team in startup format**, where developers combine multiple roles. Each developer acts simultaneously as architect, implementer, and tester of their own domain.

**Strengths:**
- Clear domain separation — no overlap in responsibilities
- Equality — no dependency on a single "knows everything" person
- Automated CI/CD reduces the risk of broken builds

**Weaknesses:**
- No dedicated QA — bugs are found by the developers themselves or after the merge
- No dedicated DevOps — production deployment requires additional planning
- PM is a part-time student — coordination can sometimes be more "asynchronous" than desired

**Are we confident in the team?** Yes. The small team size is compensated by clear boundaries of responsibility and solid communication. Each member knows their part of the product 100%.

---

## 7. Project Topic & Description

**Name:** Health Patch

**Topic:** A gamified platform for tracking physical activity and nutrition with AI coaching.

**Description:**
Health Patch is a full-stack fitness platform that transforms the training process into an RPG adventure. A user registers, creates a character, logs workouts, tracks nutrition, and receives personalized plans from an AI coach. Completing workouts earns XP, unlocks achievements, and levels up character stats.

**Stack:** FastAPI · SQLAlchemy Async · Alembic · PostgreSQL 17 · Docker Compose · GitHub Actions

**Repository:** [github.com/Alysseum17/health-patch](https://github.com/Alysseum17/health-patch)

**Current stage:** Backend MVP — implementation of 6 domains, REST API, migrations, CI/CD pipeline.
