# Lab 4 — Synchronous vs. Asynchronous Communication

## 1. What changed since Lab 3

Lab 3 left the system with a clean CQS split (Command Handler → UoW → Repo →
DB) and a write-side that emitted **domain events** that were immediately
published on an in-process `EventBus`. There was already a notion of an
"auxiliary listener" — but every domain reused the same `INotifyService`
contract (`src/shared/infrastructure/notify_service.py`), and every event
subscriber called `notify_service.notify(event)`. There was no separate
audit responsibility, no contract owned by each module, and only one
communication style: handlers wrote to the UoW event buffer and the
dispatcher flushed it to the bus after commit.

Lab 4 changes three things:

1. **`notify_service` and `LoggingNotifyService` are deleted entirely**, along
   with every reference (`grep -rn "notify_service" src tests` is empty).
2. A **per-module `audit_service`** replaces it. Each domain owns its
   contract in the application layer and its implementation in the
   infrastructure layer:

   | Module     | Contract (application)                     | Implementation (infrastructure)                                       |
   | ---------- | ------------------------------------------ | --------------------------------------------------------------------- |
   | auth       | `src/auth/application/audit_service.py`      | `src/auth/infrastructure/audit_service.py` — `LoggingAuthAuditService`     |
   | activity   | `src/activity/application/audit_service.py`  | `src/activity/infrastructure/audit_service.py` — `LoggingActivityAuditService` |
   | nutrition  | `src/nutrition/application/audit_service.py` | `src/nutrition/infrastructure/audit_service.py` — `LoggingNutritionAuditService` |

   The contract is a single async method: `async def record(self, event: Any) -> None`.
   Each implementation writes an `AUDIT <module> | <event_type> | <json>` line
   to a dedicated logger (`audit.auth`, `audit.activity`, `audit.nutrition`).
   Swapping to a persistent audit table or a SIEM later means writing one new
   class — handlers don't move.
3. Both **synchronous and asynchronous** communication styles are wired in
   parallel. Sync uses a direct interface call from inside the Command
   Handler; async uses the existing `IEventBus` plus subscribers registered
   at app startup.

## 2. Which side-operations were extracted and why

The lab brief lists notifications, audit, analytics, and integration as
candidate side-operations. We picked **audit** because:

* Every command in this system has a regulatory/forensic interest — who
  registered, who started a workout, who edited their diary. Notifications
  apply to fewer flows.
* Audit demands a **separate trust boundary**: it must not be rewritable
  by the same code path that produced the action, and the writer should be
  able to live in a different process eventually.
* Audit is a natural example of an *auxiliary* operation: losing one record
  is far less bad than refusing the main operation. That asymmetry justifies
  swallowing errors on the sync path and using a fire-and-forget bus on the
  async path.

Concretely, the audit service is the consumer of these past-tense facts:

* Auth — `UserRegisteredEvent`, `VerificationEmailRequestedEvent`, `PasswordResetRequestedEvent`.
* Activity — `WorkoutSessionStarted`, `WorkoutSessionEnded`,
  `PersonalRecordBeaten`, `WorkoutPlanCreated`, `WorkoutPlanMadePublic`,
  `WorkoutPlanDeleted`.
* Nutrition — `MealEntryAddedEvent`, `MealEntryUpdatedEvent`,
  `MealEntryDeletedEvent`, `DailyDiaryUpdatedEvent`.

All of these are `@dataclass(frozen=True)`, named in the past tense, and
carry enough context (ids, user, timestamps, payload) for a subscriber to
record them without any further DB round-trip.

## 3. Synchronous path

The synchronous path is exercised in three handlers — one per module — to
prove the pattern is portable, not domain-specific:

* `RegisterCommandHandler` (`src/auth/application/handlers/register.py`)
* `StartSessionCommandHandler` (`src/activity/application/handlers/start_session.py`)
* `AddMealEntryCommandHandler` (`src/nutrition/application/handlers/add_meal_entry.py`)

Each handler receives the audit service as a constructor argument typed by
its **interface**, not its implementation:

```python
class StartSessionCommandHandler:
    def __init__(self, uow, bus: IEventBus, audit_service: IActivityAuditService):
        ...
```

After the main transaction commits, the handler issues a direct, in-thread
call:

```python
try:
    await self._audit_service.record(started_event)
except Exception:
    logger.exception("Audit recording failed for WorkoutSessionStarted session_id=%s", session.id)
```

### Decision: roll back or ignore?

We **ignore** audit failures. Justification recorded in the code comment:
audit is auxiliary; the workout/registration/diary entry has already been
persisted, and we will not surface a 5xx to the user because the audit
sink is unavailable. The exception is logged, and the parallel async path
gives the same fact a second chance to land.

If the audit was ever upgraded to a *legal* record (e.g. medical-data
disclosure log), the policy would flip: wrap the main op + audit in a
single distributed transaction or use the **transactional outbox** pattern
so the user can't see a "success" the auditor never saw. That choice is
documented here so a future maintainer doesn't quietly change it.

### Coupling

The handler depends only on the abstract `IActivityAuditService`. It is wired
in the FastAPI dependency function (`get_start_session_handler` →
`LoggingActivityAuditService`). The handler has zero knowledge of where the
record is written. DIP is preserved.

## 4. Asynchronous path

The async path reuses the in-process `EventBus` we already had
(`src/shared/infrastructure/event_bus.py`). The flow:

```
Command Handler → uow.events.append(event)
                → dispatch_domain_events(uow, bus)  # after commit
                → bus.publish(event)                # fire-and-forget
                → asyncio.create_task(_gather_and_log(...))
                → subscriber: audit_service.record(event)
```

`bus.publish` calls `asyncio.create_task(...)` and returns immediately, so
the HTTP response is sent before subscribers finish.

Event contract requirements — all enforced:

* **Past-tense names.** `WorkoutPlanCreated`, `MealEntryAddedEvent`,
  `UserRegisteredEvent`, etc. Verified by
  `tests/unit/test_audit_service.py::test_events_are_immutable_and_past_tense`.
* **Immutability.** All events are `@dataclass(frozen=True)`. Attempting to
  reassign a field raises `FrozenInstanceError`.
* **Sufficient context.** Each event carries every id and value a subscriber
  needs. Subscribers never query the DB to enrich an event.

## 5. Side-by-side comparison

Measured locally with a deliberately slow (50 ms) audit sink to make the
shape of the cost obvious. Numbers are µs per `publish()` call:

| Aspect                | Synchronous (direct call) | Asynchronous (EventBus) |
| --------------------- | ------------------------- | ----------------------- |
| Time added to API     | **~50.14 ms / op**         | **~0.00 ms / op** (subscriber runs in background task) |
| What the client sees on audit failure | 200 OK (we log + swallow). If we did *not* swallow it would be 500. | 200 OK always — error is logged in the background `_gather_and_log` |
| What the client sees on audit slowness | API response time grows linearly with audit latency | API response time is constant; backlog grows in the asyncio loop |
| Coupling | Handler holds an `IAuditService` field; lifetime + injection are explicit | Handler holds an `IEventBus`; subscribers are registered once at startup. Handler does not know any subscriber exists. |
| Local reasoning | Easy — single `await`, one call site | Harder — must reason about delivery order, retries, and unhandled task exceptions |
| Test cost | Inject a fake or a failing fake; assert on it (see `TestSyncAuditPath`) | Inject a `RecordingAuditService` into the registration function; publish; assert (see `TestAsyncAuditPath`) |
| Failure isolation | Subscriber failure does not affect anything else by definition (we caught it). | A failing subscriber must not poison other subscribers — verified by `test_audit_failure_does_not_break_other_subscribers` |
| Delivery guarantee | At-most-once, in the same transaction context | At-most-once *per process* — events are lost if the process dies before the background task runs |

### Behavior under failure (concrete)

* **Audit sink down, sync path:** `await self._audit_service.record(event)`
  raises → caught by `try/except` → `logger.exception(...)` → handler
  returns normally. Tested in
  `tests/unit/test_audit_service.py::test_start_session_swallows_audit_failures`.
* **Audit sink down, async path:** subscriber raises inside the task created
  by `asyncio.create_task` → `_gather_and_log` reports the exception →
  caller has already received the response. The system stays available, but
  an audit record is permanently lost (no retry, no DLQ). This is the
  consequence we accept for the in-process bus.

### Coupling between components

In the sync path the handler depends on an interface (good) but holds a
reference to that interface (limited blast radius — one method, one
direction). In the async path the handler depends on the bus, and the bus
has zero knowledge of the audit service at the call site — they meet only
at app startup in `register_*_event_handlers(bus, audit_service)`. From the
Command Handler's point of view, the async path is the most decoupled —
adding a second subscriber tomorrow needs no change to the handler at all.

### Implementation & testing complexity

Sync is cheaper to implement and reason about (one new constructor arg,
one new line, one try/except). Async needed two pieces of plumbing that
already existed in the project — events and a bus — so the incremental
cost was a registration function per module. Sync tests are direct;
async tests need a recording subscriber and a `publish()` call. Both are
small, and both styles are now under unit-test coverage in
`tests/unit/test_audit_service.py`.

## 6. Which would I pick for production?

**Async by default, sync as an opt-in for audit-equivalents that must
be transactional with the main op.**

Reasoning:

* For ~all of our use cases the user-visible cost of sync (50 ms × N
  subscribers added directly to the HTTP latency) is unacceptable as soon
  as we have more than one side-effect per command.
* Async (with the in-process bus today, RabbitMQ/Kafka tomorrow) makes the
  handler reusable. Adding analytics later is a one-liner — register a new
  subscriber. No change to handlers, no risk of accidentally fanning out a
  slow analytics call inside a request.
* The few flows that **must** be transactional with the main op (e.g. a
  hypothetical legal-disclosure ledger) can keep the sync wiring we already
  built — same interface, same handlers, same DI. The mechanism is
  symmetric; what differs is the policy.

The in-process `EventBus` is a stepping stone: it's fine for an MVP, but a
production deployment with more than one replica needs a durable broker
(we use Redis for queues already; promoting `HybridEventBus` to the
default with a persistent stream is the natural next step). Until then the
risk we take is "one record may be lost if the process crashes mid-task" —
acceptable for non-legal audit.

## 7. Idempotency — what happens if an event is delivered twice?

Today, in-process: an event is delivered exactly once per `publish()` call,
so duplicate delivery does not happen. **But** the moment we move to a real
broker (Redis streams, Rabbit, Kafka), at-least-once delivery is the only
realistic guarantee, so the subscribers must be idempotent on their own.

Status of each subscriber:

* **Logging-only audit sinks (the current implementations).** Not strictly
  idempotent — re-delivery would produce a duplicate `AUDIT` log line.
  That is acceptable for a log-based sink: greppable, easy to dedup
  offline, and never causes a state divergence.
* **Email enqueue in auth subscribers.** The current code calls
  `arq_pool.enqueue_job(...)` unconditionally. Replaying
  `UserRegisteredEvent` would enqueue a second verification email — that
  *is* a user-visible duplicate. To fix when we move to a real broker, the
  job should be enqueued with a deterministic `_job_id` such as
  `f"verify:{user_id}:{event.created_at}"` so arq dedupes; or, equivalently,
  the audit/event itself should carry a `event_id: UUID` and the subscriber
  should check a Redis SET before acting.

So: the **shape** of our subscribers is idempotent-friendly (events carry
enough context to build a stable key), but the **wiring** isn't yet
idempotent. We will add an `event_id` field to each event and a
`processed_events` Redis set the day we promote the bus to a durable
broker. That change is local to the subscribers and does not touch the
Command Handlers.

## 8. Files touched

* Deleted: `src/shared/infrastructure/notify_service.py`,
  `src/shared/infrastructure/logging_notify_service.py`.
* New contracts: `src/{auth,activity,nutrition}/application/audit_service.py`.
* New implementations: `src/{auth,activity,nutrition}/infrastructure/audit_service.py`.
* Sync wiring: `src/auth/application/handlers/register.py`,
  `src/activity/application/handlers/start_session.py`,
  `src/nutrition/application/handlers/add_meal_entry.py`,
  plus DI in `src/{auth,activity,nutrition}/presentation/dependencies.py`.
* Async wiring: `src/{auth,activity,nutrition}/application/event_handlers.py`,
  registered in `src/core/main.py`.
* Tests: `tests/unit/test_audit_service.py` (new), plus updates to
  `tests/conftest.py`, `tests/unit/test_activity.py`,
  `tests/unit/test_activity_event_handlers.py`, `tests/unit/test_auth.py`,
  `tests/unit/test_nutrition.py`.
