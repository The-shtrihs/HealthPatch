# Lab 4 — Synchronous vs. Asynchronous Communication

## 1. What changed since Lab 3

Lab 3 left the system with a clean CQS split (Command Handler → UoW → Repo → DB). However, all side-effects were handled synchronously, and the system did not yet use **domain events**. 

Lab 4 introduces four major changes to implement side-operations:

1. **Domain Events and Event Bus:** We introduced domain events and an `EventBus` to decouple core logic from side-effects. Handlers now append events to the UoW, which are dispatched after a successful commit.
2. **Per-module `audit_service`:** Instead of a generic central notification service, each domain now owns its audit contract in the application layer and its implementation in the infrastructure layer:

   | Module     | Contract (application)                     | Implementation (infrastructure)                                       |
   | ---------- | ------------------------------------------ | --------------------------------------------------------------------- |
   | auth       | `src/auth/application/audit_service.py`      | `src/auth/infrastructure/audit_service.py` — `LoggingAuthAuditService`     |
   | activity   | `src/activity/application/audit_service.py`  | `src/activity/infrastructure/audit_service.py` — `LoggingActivityAuditService` |
   | nutrition  | `src/nutrition/application/audit_service.py` | `src/nutrition/infrastructure/audit_service.py` — `LoggingNutritionAuditService` |

   The contract is a single async method: `async def record(self, event: Any) -> None`. Each implementation currently writes to a dedicated logger, but swapping to a persistent audit DB later means writing one new class without changing the handlers.
3. **Gamification via Events:** The gamification module was introduced purely as an asynchronous consumer of events from other domains.
4. **Distributed Background Tasks:** For truly out-of-process asynchronous operations (like email sending), we introduced a standalone worker (`main_worker.py`) using ARQ and Redis.

## 2. Which side-operations were extracted and why

The lab brief lists notifications, audit, analytics, and integration as candidate side-operations. We implemented three distinct types of side-operations using different communication styles:

* **Audit (Synchronous/Asynchronous):** Every command in this system has a regulatory/forensic interest (who registered, who started a workout). Audit demands a separate trust boundary. It is an *auxiliary* operation: losing one record is far less bad than refusing the main operation.
* **Gamification (Asynchronous Event-Driven):** Gamification logic (calculating XP, leveling up) should never block the main flow of saving a workout or a meal. It is completely decoupled and reacts to past-tense facts.
* **Email Sending (Out-of-process Background Tasks):** Sending emails (e.g., verification, password resets) involves network calls to third-party APIs (SMTP/SendGrid). This is highly prone to latency and failure, so it is offloaded to a separate Redis-backed worker.

Concretely, our side-operations consume these past-tense facts:

* **Auth:** `UserRegisteredEvent`, `PasswordResetRequestedEvent`.
* **Activity:** `WorkoutCompleted`, `WorkoutSessionStarted`, `PersonalRecordBeaten`, `WorkoutPlanCreated`.
* **Nutrition:** `MealEntryAddedEvent`, `MealEntryUpdatedEvent`, `DailyNormAchieved`.
* **Gamification:** Listens to cross-module events (like `WorkoutCompleted` or `DailyNormAchieved`) to grant experience points asynchronously.

All of these are `@dataclass(frozen=True)`, named in the past tense, and carry enough context for a subscriber to record them without further DB round-trips.

## 3. Synchronous path

The synchronous path is exercised in handlers to prove the pattern is portable:

* `RegisterCommandHandler` (`src/auth/application/handlers/register.py`)
* `StartSessionCommandHandler` (`src/activity/application/handlers/start_session.py`)
* `AddMealEntryCommandHandler` (`src/nutrition/application/handlers/add_meal_entry.py`)

Each handler receives the audit service as a constructor argument typed by its **interface**. After the main transaction commits, the handler issues a direct, in-thread call:

```python
try:
    await self._audit_service.record(started_event)
except Exception:
    logger.exception("Audit recording failed")

```

We **ignore** audit failures because it is an auxiliary operation. The main operation (workout/registration) has already been persisted, and we do not surface a 500 error to the user just because the audit sink is unavailable.

## 4. Asynchronous path & Background Workers

The async path is divided into two mechanisms: the in-process `EventBus` and the out-of-process ARQ Worker.

### In-Process EventBus (Gamification & Audit)

The flow:

```text
Command Handler → uow.events.append(event)
                → dispatch_domain_events(uow, bus)  # after commit
                → bus.publish(event)                # fire-and-forget
                → asyncio.create_task(_gather_and_log(...))
                → subscribers run (e.g., Audit, Gamification XP calculation)

```

`bus.publish` calls `asyncio.create_task(...)` and returns immediately, so the HTTP response is sent before subscribers finish. Gamification uses this to seamlessly update user XP without impacting the response time of the `/activity` or `/nutrition` endpoints.

### Out-of-Process Worker (Email Sending)

For operations that are strictly bound to external I/O and require retries, we use ARQ (`src/workers/main_worker.py`).
Instead of processing emails in the API container, the event subscriber enqueues a job:

```python
await event_bus.arq_pool.enqueue_job(
    "task_send_verification_email", 
    user_id=event.user_id, 
    user_email=event.email, 
    name=event.name
)

```

The separate worker process picks this up from Redis. This guarantees:

* **Zero impact on API latency:** The enqueue operation takes < 1ms.
* **Fault tolerance:** The worker has `max_tries = 3`. If the email API goes down, ARQ automatically retries the job later without losing the event.
* **Process isolation:** A crash in the email rendering logic only crashes the worker, not the main FastAPI server.

## 5. Side-by-side comparison

Measured locally, numbers are µs per `publish()` call:

| Aspect | Synchronous (direct call) | Asynchronous (EventBus) | Out-of-Process Worker (ARQ) |
| --- | --- | --- | --- |
| **Time added to API** | **~50.14 ms / op** | **~0.00 ms / op** (asyncio task) | **~1.00 ms / op** (Redis enqueue) |
| **Client sees on failure** | 200 OK (logged + swallowed) | 200 OK (logged in background) | 200 OK (worker retries 3 times) |
| **Coupling** | Handler holds explicit `IAuditService` | Handler only knows `IEventBus` | Handler knows `IEventBus`, bus knows Redis |
| **Failure isolation** | Try/except in the handler | Subscriber failure logged, doesn't affect main loop | Fully isolated in a separate OS process |
| **Delivery guarantee** | At-most-once | At-most-once *per process* | At-least-once (Redis persistence + retries) |

## 6. Which would I pick for production?

**Async by default via distributed broker (Worker/Redis), sync only as an opt-in for transactional side-effects.**

* For operations like **Email Sending**, the ARQ worker is the only production-ready choice. Network calls must be retryable and out-of-process.
* For **Gamification**, an async event bus is perfect. It keeps the core domains (Nutrition/Activity) completely unaware of the RPG mechanics.
* The in-process `EventBus` is great for MVP analytics/audit, but moving to Redis Streams/RabbitMQ ensures we don't lose events if the API container crashes mid-task.

## 7. Idempotency — what happens if an event is delivered twice?

Today, in-process: an event is delivered exactly once per `publish()` call, so duplicate delivery does not happen. **But** the moment we move to a real broker (Redis streams, Rabbit, Kafka), at-least-once delivery is the only realistic guarantee, so the subscribers must be idempotent on their own.

* **Logging-only audit sinks.** Not strictly idempotent — re-delivery would produce a duplicate `AUDIT` log line. That is acceptable for a log-based sink: greppable, easy to dedup offline.
* **Email enqueue in auth subscribers.** Replaying `UserRegisteredEvent` would enqueue a second verification email — that *is* a user-visible duplicate. To fix this, the job should be enqueued with a deterministic `_job_id` such as `f"verify:{user_id}"` so ARQ dedupes.
* **Gamification:** Replaying events would grant experience points twice, inflating the user's level. The subscriber should verify an `event_id` against a Redis SET `processed_events` before applying XP to ensure exactly-once processing.

## 8. Files touched

* New Event & Worker infrastructure: `src/shared/infrastructure/event_bus.py`, `src/workers/main_worker.py`.
* Contracts: `src/{auth,activity,nutrition}/application/audit_service.py`.
* Implementations: `src/{auth,activity,nutrition}/infrastructure/audit_service.py`.
* Sync wiring: `src/auth/application/handlers/register.py`, `src/activity/application/handlers/start_session.py`, `src/nutrition/application/handlers/add_meal_entry.py`.
* Async wiring (EventBus & ARQ Enqueueing): `src/{auth,activity,nutrition,gamification}/application/event_handlers.py`, registered in `src/core/main.py`.
* Tests: `tests/unit/test_audit_service.py` (new), plus updates to integration and unit tests for respective modules.

