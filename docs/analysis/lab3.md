# Lab 3 — CQS Refactor of the Activity Domain

## 1. Scope

Lab 3 asked the team to split **write** and **read** operations at the Application Layer — Command-Query Separation (CQS). Commands mutate state and return nothing meaningful (at most an identifier); queries return data and do not touch the domain. The activity domain was chosen as the pilot since it already had the richest invariants after Lab 2.

Current state:

| Layer                          | Before Lab 3 (Lab 2 shape)                     | After Lab 3                                                                                   |
| ------------------------------ | ---------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Application write path         | `UseCase.execute(cmd) -> domain aggregate`  | `CommandHandler.handle(cmd) -> None \| int`                                                |
| Application read path          | `UseCase.execute(query) -> domain aggregate` | `QueryHandler.handle(query) -> ReadModel`                                                   |
| DTOs                           | single `application/dto.py`                    | `commands.py` + `queries.py` + `read_models.py`                                               |
| HTTP layer                     | routes call use cases, then pass domain through `response_builders.py` to Pydantic | routes build Command/Query → `handler.handle(...)` → return `IdResponse` or validate a Read Model through Pydantic response_model |
| Read repository                | none — reads went through the same write repo | `SqlAlchemyActivityReadRepository` — SELECT-only, returns Read Model dataclasses directly     |

File-by-file layout mirrors the convention already used by [src/auth/application/](../../src/auth/application/) and [src/user/application/](../../src/user/application/): a flat `commands.py` / `queries.py` / `read_models.py` plus one class per operation under `handlers/`.

## 2. Write path — Commands

All command dataclasses are collected in [src/activity/application/commands.py](../../src/activity/application/commands.py). Each command is paired with a single-purpose handler in [src/activity/application/handlers/](../../src/activity/application/handlers/).

Two rules that did not hold before Lab 3:

- **Commands return nothing meaningful.** Creates return the new entity `id: int` so the HTTP layer can build a `Location`-style response; updates/deletes return `None`. No handler returns a domain aggregate.
- **Writes go through the domain.** A handler obtains the Unit of Work, loads or constructs a domain entity, runs invariants on it, and persists via the write repository. Example — [log_set.py](../../src/activity/application/handlers/log_set.py) still loads the session, checks "not ended", creates a `WorkoutSet` through `WorkoutSetFactory`, and auto-upserts the personal record when a new max is hit. None of that logic leaked into the controller.

Unit tests at [tests/unit/test_activity.py](../../tests/unit/test_activity.py) now assert the shape of the return value (`isinstance(new_id, int)` for creates, `assert result is None` for void commands) and invariant violations by exception type. 38 unit tests run with the database container stopped.

## 3. Read path — Queries

Query dataclasses live in [src/activity/application/queries.py](../../src/activity/application/queries.py). Their handlers **bypass the domain layer entirely** and talk to a dedicated read repository.

- Read repository: [src/activity/infrastructure/read_repository.py](../../src/activity/infrastructure/read_repository.py). It issues SELECTs against the ORM and maps rows directly into plain-dataclass Read Models — no domain entity is ever constructed.
- Read Models: [src/activity/application/read_models.py](../../src/activity/application/read_models.py). Shaped to match the HTTP response contract. Pydantic's `from_attributes=True` then validates them through the schemas in [presentation/schemas.py](../../src/activity/presentation/schemas.py) with no hand-written converter.

The practical benefit is immediate: paginated list endpoints no longer hydrate aggregates they do not need. `GET /workouts/plans/public` returns summaries without loading any training rows. `GET /workouts/sessions/{id}` issues a single selectinload for exercises + sets instead of going through `SqlAlchemyActivityMapper.to_domain(...)` and then back out through a response builder.

The old `presentation/response_builders.py` — roughly 150 lines of domain→Pydantic translation — was deleted. Its role is now split cleanly: query handlers shape data on the read path; controllers do nothing.

## 4. Controllers

Routes in [src/activity/presentation/routes.py](../../src/activity/presentation/routes.py) are now mechanical:

```python
@router.post("/plans", response_model=IdResponse, status_code=201)
async def create_plan(
    payload: CreateWorkoutPlanRequest,
    handler: CreateWorkoutPlanCommandHandler = Depends(get_create_workout_plan_handler),
    current_user: User = Depends(get_current_user),
):
    new_id = await handler.handle(CreateWorkoutPlanCommand(author_id=current_user.id, ...))
    return IdResponse(id=new_id)
```

No domain imports, no branching, no response construction. A grep confirms:

```bash
grep -rE "^(from|import) src\.activity\.domain" src/activity/presentation/routes.py
# (empty)
```

Dependencies are wired per handler in [src/activity/presentation/dependencies.py](../../src/activity/presentation/dependencies.py): command handlers receive `IActivityUnitOfWork`, query handlers receive `SqlAlchemyActivityReadRepository` — the asymmetry is visible at the DI layer, not buried in implementation.

## 5. Benefits observed

**Write/read asymmetry is explicit, not implied.** Before Lab 3, the same use-case class could return either a full aggregate or a detail snapshot depending on which method a caller used; the contract was "whatever the author felt like". After Lab 3, a method named `handle` on a `*CommandHandler` cannot return a domain object — the type annotation is `None | int`.

**Controllers are trivially reviewable.** Each endpoint is ~10 lines: map request → Command/Query, call `handle`, return. PRs that change HTTP shape no longer accidentally touch domain logic.

**Read paths are cheaper.** List endpoints skip domain hydration and ORM→domain→Pydantic triple translation. Detail endpoints use selectinload sized for the response, not for the aggregate.

**Tests split along the seam.** Unit tests cover commands (fakes, no DB, 38 tests). Integration tests cover queries + command smoke (real Postgres through HTTP, 78 tests). Previously query logic was tested only by exercising the full stack.

**Response shaping lives in one place.** A Read Model defines its own shape; Pydantic validates that shape; there is no `response_builders.py` layer to drift.

## 6. Drawbacks / costs

- **More files.** 24 handler files instead of 4 use-case files. Navigation depends on editor search, not folder memory.
- **Read models duplicate Pydantic schemas.** `PlanDetailResponse` (Pydantic) and `WorkoutPlanDetailReadModel` (dataclass) carry the same fields. Merging them would pull Pydantic into the application layer — rejected, same reasoning as Lab 2's DTO/schema duplication.
- **Read repository is separate from write repository.** Two SQL surfaces over the same tables. Acceptable: the read surface is SELECT-only and can be tuned (projections, joins) without risk of mutating the write contract.
- **DI surface grew.** `dependencies.py` went from ~20 to ~35 factories. FastAPI absorbs the cost, but the file is longer.
- **Inconsistency across the codebase.** Nutrition still uses Lab 1 service classes; auth/user already had flat-handlers per Lab 2; only activity is full CQS. A new hire now sees three conventions.

## 7. Answers to the Lab 3 prompt questions

**(1) Did you split write and read at the Application Layer?**
Yes. Commands in [commands.py](../../src/activity/application/commands.py), queries in [queries.py](../../src/activity/application/queries.py), separate handler classes under [handlers/](../../src/activity/application/handlers/). Writes flow through the domain via `IActivityUnitOfWork`; reads flow through `SqlAlchemyActivityReadRepository` and skip the domain.

**(2) Do commands return data?**
Only an `id: int` for creates (so the client can follow up with a GET) and `None` for updates/deletes. No command handler returns domain entities or detail snapshots.

**(3) Do queries touch the domain?**
No. Query handlers depend on the read repository, which maps ORM rows directly to Read Model dataclasses in [read_models.py](../../src/activity/application/read_models.py). The domain layer is never imported from the read path.

**(4) What did you gain?**
Explicit contracts at the handler boundary, thinner controllers, cheaper reads, a clean split between DB-free unit tests (commands) and HTTP integration tests (queries). See §5.

**(5) What did it cost?**
More files, duplicated shapes between Read Models and Pydantic schemas, a second SQL surface for reads, and inconsistency with domains that have not been migrated. See §6.
