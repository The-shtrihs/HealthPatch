# Laboratory Work No. 5 — Modular Monolith in HealthPatch

---

## 1. Lab 5 Analysis

### 1.1. Choosing Context and Module Boundaries

The system is divided into **two macro-contexts** (Bounded Contexts):

| Macro-context | Purpose | Repository Path |
|---|---|---|
| **Core** | Active business logic: identity, activities, nutrition, gamification, profile | `src/core_context/` |
| **Analytics** | Read-only consumer: audit log and read-models (projections) for reporting | `src/analytics_context/` |

Within **Core**, five independent modules (mini-bounded contexts) are defined, each with a full DDD stack (`domain / application / infrastructure / presentation`):

- `auth` — registration, login, tokens, OAuth, 2FA;
- `user` — user profile, fitness data;
- `activity` — workouts, plans, personal records;
- `nutrition` — nutrition diary, daily norms;
- `gamification` — XP, levels, rewards.

**Division Principle.** Module boundaries were chosen based on **aggregate invariants** and **transactional boundaries**: data that must change together within a single request with consistency guarantees belong to one module. For example, `MealEntry` and `DailyDiary.totals` represent a single transactional invariant (Nutrition); awarding XP for the exact same event is a separate invariant (Gamification), as business logic dictates it has the right to be asynchronous and may even be delayed.

**Why Analytics is a separate macro-context.** Audit and read-models are *secondary* representations of the system's state, required for reporting and compliance. Extracting them into a separate context:
- relieves the aggregation load from Core (the write-path remains fast);
- allows Analytics to evolve independently (new dashboards, new projections without risking the business write-path);
- naturally establishes the direction of dependency: **Analytics depends on Core, but not vice versa** (this is strictly enforced by `import-linter`).

### 1.2. How ACL Protects Modules

Each module exposes only the `contracts/` package:
- `contracts/dtos.py` — public DTOs (Pydantic v2, frozen);
- `contracts/events.py` — past-tense integration events (`WorkoutCompleted`, `MealEntryAdded`, ...);
- `contracts/ports.py` — interface ports (`IUserDirectory`, `IExerciseCatalog`, ...);
- `contracts/dependencies.py` — public FastAPI dependencies (e.g., `get_current_user` for Auth).

All other module layers (`domain`, `application`, `infrastructure`, `presentation`) are **private**. The prohibition against directly "leaking" into foreign private layers is formalized declaratively in `pyproject.toml` via `import-linter` (contract `Core modules expose only contracts/`). Any attempt to use `from src.core_context.user.domain.models import ...` from the Nutrition side will fail the CI lint.

The **ACL (Anti-Corruption Layer)** resides in the `acl/` packages of the consumer module. An example is `src/core_context/gamification/acl/translators.py`. Instead of receiving `WorkoutCompletedEvent` from `activity.domain` or `MealEntryAdded` from nutrition.contracts directly, Gamification:

1. subscribes to the **integration event** from `activity.contracts.events.WorkoutCompleted` (minimal contract: `user_id`, `duration_minutes`, `total_volume_kg`);
2. passes it through `from_workout_completed(event) -> XpAwardCommand` — this is the ACL boundary;
3. further internal logic operates exclusively on `XpAwardCommand` — the native language of the Gamification module.

Another ACL example is Analytics→Core: `src/analytics_context/audit/acl/translators.py`. Any integration event from `auth.contracts.events`, `activity.contracts.events`, `nutrition.contracts.events` is transformed into an internal `AuditEntry`. Core types do not escape beyond this file.

How the Analytics module uses a translated type, `UserProfileDTO`, provided by the User module, is demonstrated by another example: Nutrition receives `FitnessGoal`/`Gender` not from `user.domain`, but from `user.contracts.dtos` — the same `StrEnum`, but declared in a public contract, thus the presence of an ACL translation itself is not needed (the contract is specifically designed to be suitable for direct consumption).

### 1.3. Strong vs Eventual Consistency — Rationale for Division

| Guarantee | Where applied | Implementation |
|---|---|---|
| **Strong consistency** | Within a single module, inside one UoW: `MealEntry` + `DailyDiary.totals` + `MealEntryAddedEvent` (internal) are committed in one PostgreSQL transaction. | `src/shared/infrastructure/base_uow.py` (savepoint-aware async UoW) + `dispatch_domain_events` after successful `commit`. |
| **Eventual consistency** | Across modules: Gamification's reactions to `WorkoutCompleted`; audit writing in Analytics; updating projections. | The event is published to the `EventBus` after the source module commits. Consumers execute either synchronously (`mode="sync"` — for UX-critical paths like XP) or asynchronously via arq (`mode="async"` — for audit, projections, email). |

**Argumentation.** Stretching transactions across multiple modules via 2PC or XA ruins the very idea of modularity: a failure in one module blocks the entire system, schemas become entangled, and testing becomes a nightmare. Instead:

- **Within a module**, a transaction is cheap, invariants are simple, and the user has the right to expect "all or nothing." Strong consistency here is free.
- **Across modules**, it is acceptable that awarding XP, writing to an audit log, or updating a leaderboard "catches up" a second later. Eventual consistency instead provides failure isolation (Analytics can be down — Core keeps working) and the ability to scale workers independently.

The exception to the eventual rule is **Gamification XP/level-up**: the user must see the new XP amount immediately in the response to the request that triggered the event. Therefore, these subscriptions are explicitly registered with `mode="sync"` and execute within the same request cycle. Audit and projections are `mode="async"` because the user's wait time should not depend on the speed of the Analytics disk.

### 1.4. ADR — Context Boundaries

# ADR-005: Modular Monolith with two macro-contexts (Core / Analytics)
Status: Accepted (Lab 5)
Context: HealthPatch grew out of a DDD-monolith with a shared `src/models/` and
  direct cross-module imports. This blocked (a) independent team evolution
  by domains, (b) the ability to extract Analytics into a separate process
  in the future, (c) automated verification of architectural rules.
Decision: Divide src/ into src/core_context/ (5 modules) and
  src/analytics_context/ (audit + projections); expose only the contracts/
  package from each module; all cross-module communication — via
  IntegrationEvent on a shared bus (sync for UX-critical reactions,
  async via arq for everything else); verify boundaries with import-linter in CI.
Consequences:
  + Clear code ownership; CI guards the borders.
  + Analytics can be extracted into its own deployment without rewriting Core.
  + Async-path naturally provides DLQ (arq failed jobs) and retry-semantics.
  - Increased number of files (contracts/, acl/, integration_publishers).
  - Eventual consistency adds latency and complicates local debugging.
  - Serializing events to JSON for arq limits payload types.
Alternatives rejected:
  - Microservices with separate DBs — for a team of 1-2 developers per module,
    the operational overhead is unjustified; we choose a "monolith we can later split".
  - Leave as is (DDD-monolith with shared models) — does not scale
    organizationally and prevents automated boundary checks.

---

## 2. Course Retrospective: Lab 1 → Lab 5

### 2.1. Architectural Evolution of HealthPatch

| Lab | Architecture State | Key Achievement |
| --- | --- | --- |
| **Lab 1** | Classic layered FastAPI: `routes / services / repositories / models`. A single `src/models/` package. No domain events. | Basic EXECUTABLE skeleton: Alembic migrations, JWT, Pydantic schemas. |
| **Lab 2** | Integrated Domain-Driven Design: each module received `domain / application / infrastructure / presentation` subdirectories; aggregates appeared (`UserDomain`, `WorkoutSessionDomain`), Unit of Work. | Clear separation of business logic from HTTP and ORM. |
| **Lab 3** | CQRS-like division: separate `commands.py` / `queries.py` / `read_models.py`. Repositories specialized (write/read). | Read-models are cheap to extend, write-aggregates remained clean. |
| **Lab 4** | Domain events + EventBus (in-memory + arq), `dispatch_domain_events` in UoW. First asynchronous side-effects extracted (email). | Transition from "call a function" to "publish an event". |
| **Lab 5** | Modular monolith with contracts and ACL; Analytics macro-context; integration events; `import-linter` boundary checking; hybrid sync/async bus. | Architectural boundaries became an **executable** part of the code. |

### 2.2. Most Valuable Architectural Decisions

1. **EventBus + UoW outbox (Lab 4-5).** This is the single change that yielded the biggest payoff: all subsequent requirements (asynchronous audit, projections, XP calculation, email, leaderboard) fit onto a ready-made template without ad-hoc code.
2. **DDD layering from the start (Lab 2).** Without `domain/application/infrastructure/presentation`, Lab 5 would have been impossible: module boundaries would have to be invented from scratch. Thanks to layering, Lab 5 boiled down to "cut private dependencies and substitute contracts/".
3. **Pydantic v2 frozen DTO as a contract.** Cheap in syntax, provides validation for free, serialization for arq, and immutability — an ideal material for a cross-context payload.
4. **Per-handler delivery mode (`sync`/`async`) on a single bus.** Instead of supporting two separate bus implementations — one class with a subscription parameter. Reduced cognitive load and removed duplicated infrastructure.

### 2.3. What I Would Do Differently

* **Introduce contracts/ back in Lab 2.** Then there wouldn't have been 121 cross-module imports that had to be refactored in Lab 5.
* **Not keep `src/models/` as a god-package.** A shared package of ORM models became a center of gravity for all modules and distorted boundaries. It would have been better to put ORM in `<module>/infrastructure/orm.py` from the start and configure Alembic for discovery.
* **Extract audit into its own module immediately.** Instead of duplicating `IAuditService` in three domains and then merging them into Analytics, I would have had one centralized event consumer right away.
* **Strictly type IDs immediately.** Half the modules use `int` (Postgres serial), and in Lab 5 I almost had to sweep through all contracts with UUIDs. Consistent typing at an early stage is zero work; at a late stage, it's refactoring 20 files.

### 2.4. Observed Trade-offs "Simplicity vs Flexibility"

| Issue | Simpler | More Flexible | What I Chose and Why |
| --- | --- | --- | --- |
| Shared ORM models | A single `src/models/` | Per-module ORM | Lab 1-4: shared (fast). Lab 5: migration started (prepares extraction of module to a separate service). |
| Cross-module call | Direct import + `await service.method()` | Integration event + ACL | Up to Lab 4 — direct calls. From Lab 5 — events. Latency increased by ~5-10 ms, but failure isolation and team autonomy outweighed it. |
| Handler delivery | All sync | All async | Hybrid: UX-critical sync, background async. Avoided both "long requests from user" and "where is my XP — oh, it's in the queue". |
| Boundary checking | Code review | `import-linter` in CI | Code review misses 1 out of 5 cross-module imports — experience from Lab 2-4. Linter catches 5 out of 5 and never gets tired. |
| Eventually consistent read (audit/projection) | Query Core DB directly | Separate Analytics table, updated by events | Separate table: more expensive in storage, cheaper in latency, and perfectly replicates reality of production analytics (data warehouse). |

### 2.5. Overall Conclusion

The most important lesson from the five labs is that **architectural decisions must be executable, not just documented**. A layer diagram in README does not stop a developer from `from src.core_context.user.domain import ...`; `import-linter` stops them. A document about "events for cross-module communication" does not turn a function call into an event; a hybrid `EventBus` with a `mode` parameter makes this transition a single signature change.

HealthPatch at the end of the course is not a "monolith we wish we could split", but a **"monolith we can split if we ever need to"**: boundaries are formalized in code, all cross-module communications go through serialized events, and isolating Analytics into a separate process is a matter of `docker-compose.yml`, not refactoring.

