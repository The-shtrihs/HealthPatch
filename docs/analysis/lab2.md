# Lab 2 — Project-Wide Layered-Architecture Analysis

## 1. Scope

Lab 2 asked the team to move HealthPatch from a flat, "by-kind" package layout (all routes together, all services together, etc.) to a **4-layer per-domain** layout.

Current state of the project:

| Domain               | Layered (Lab 2 shape) | Location                               |
| -------------------- | --------------------- | ------------------------------------   |
| Auth / Identity      | Yes                   | [src/auth/](../../src/auth/)           |
| User / Profile       | Yes                   | [src/user/](../../src/user/)           |
| Activity & Workouts  | Yes                   | [src/activity/](../../src/activity/)   |
| Nutrition            | Yes                   | [src/nutrition/](../../src/nutrition/) |
| Social, Gamification | Not started           | —                                      |

## 2. What changed from Lab 1

**Lab 1 shape (horizontal slices):**

```
src/
  routes/       # all HTTP handlers for every domain
  services/     # all business logic for every domain
  repositories/ # all DB access for every domain
  schemas/      # all Pydantic models
  models/       # all SQLAlchemy ORM
```

A feature like "log a workout set" was spread across five packages that mixed unrelated domains together.

**Lab 2 shape (vertical slices per domain):**

```
src/<domain>/
  domain/          # entities, value objects, factories, errors, repository interfaces
  application/     # use cases + command/result DTOs
  infrastructure/  # SQLAlchemy repo + UoW + ORM↔domain mapper
  presentation/    # FastAPI router, Pydantic schemas, DI, error→HTTP mapper
```

Concretely for activity, [src/services/activity.py](../../src/services/activity.py) (~506 LoC, 30+ methods) was split into ~22 use-case classes grouped by aggregate under [src/activity/application/use_cases/](../../src/activity/application/use_cases/). Domain rules that used to live inside service methods (e.g. "session cannot be ended twice", "PR cannot downgrade") moved onto domain entities.

## 3. Benefits observed

**Domain purity is enforceable, not aspirational.** The dependency rule can now be verified by grep:

```bash
grep -rE "^(from|import) (sqlalchemy|fastapi|pydantic|src\.models|src\.core\.redis)" src/activity/domain/
# (empty — no matches)
```

Same check passes for [src/auth/domain/](../../src/auth/domain/) and [src/user/domain/](../../src/user/domain/).

**Real DB-free unit tests.** [tests/unit/test_activity.py](../../tests/unit/test_activity.py) uses an in-memory `FakeActivityRepository` / `FakeUnitOfWork` implementing `IActivityRepository` / `IActivityUnitOfWork`. The suite runs with the Postgres container stopped. Previously, most "unit" tests were integration tests in disguise because the service layer took a live session.

**Dependency Inversion Principle.** Use cases depend on interfaces (`IActivityUnitOfWork` in [src/activity/domain/interfaces.py](../../src/activity/domain/interfaces.py)), not on SQLAlchemy. A use case's import graph no longer reaches `sqlalchemy`.

**Errors are decoupled from transport.** Domain raises `ActivityDomainError` subclasses that carry no HTTP knowledge. Mapping to status codes lives in [src/activity/presentation/error_mapper.py](../../src/activity/presentation/error_mapper.py). The domain could be reused behind a CLI or gRPC without change.

**Feature work touches one folder.** A change to "log a set" edits files inside `src/activity/`, not five distant packages.

## 4. Drawbacks / costs

- **More files per feature.** Each write path passes through a Pydantic schema, a Command dataclass, a use case, a mapper, a repository, an ORM row — six shapes of roughly the same data.
- **Mapper boilerplate.** [src/activity/infrastructure/mapper.py](../../src/activity/infrastructure/mapper.py) is pure translation code. It exists only because we chose to isolate the ORM; a small domain would not earn it back.
- **Duplication at the boundary.** Pydantic `schemas.py` + dataclass Commands in `dto.py` carry overlapping fields. Accepted cost — merging them would drag Pydantic into the domain.
- **Inconsistency across the codebase.** Nutrition still follows the Lab 1 layout. A new hire has to learn two conventions until that domain is migrated.
- **Learning curve.** Junior teammates needed a walkthrough to understand why a "simple CRUD" endpoint traverses four layers.

## 5. How easy is it now to swap a framework or the database?

**Swapping FastAPI for another HTTP framework** — only `presentation/` is affected. For activity: `routes.py`, `error_mapper.py`, `dependencies.py`, `schemas.py`. Everything under `application/`, `domain/`, `infrastructure/` is untouched. The same applies to auth and user.

**Swapping SQLAlchemy / Postgres for a different store** — only `infrastructure/` changes. Replace `SqlAlchemyActivityRepository` and `SqlAlchemyActivityUnitOfWork` with implementations against the new store, keep the interfaces in `domain/interfaces.py`. Use cases would not change at all. The existing fakes in `tests/unit/test_activity.py` already demonstrate that a completely different "storage" (Python dicts) plugs in without touching the application layer.

**Swapping Pydantic for another validator** — only `presentation/schemas.py` per domain. Commands in `application/dto.py` are plain `@dataclass` and survive.

**Swapping Redis (OAuth state, rate limit)** — affects only the Redis-backed adapters in `src/repositories/`; again, no domain change.

This ease is not accidental: it is what the dependency rule *buys*. It was not achievable in Lab 1, where services imported SQLAlchemy directly and routes reached into ORM rows.

## 6. Rich vs. Anemic — per-domain choice

- **Activity → Rich Domain Model.** Many invariants (weight ≥ 0, reps ≥ 1, set number ≥ 1, session end after start, no PR downgrade, non-empty title) naturally belong on entities and VOs. Justified in [ADR 0002](../adr/0002-activity-rich-domain-model.md).
- **Auth → mostly Rich.** `UserDomain` carries behavior like `activate`, `deactivate`, `verify_email`, `mark_password_changed`. See [src/auth/domain/models.py](../../src/auth/domain/models.py).
- **User / Profile → Anemic.** Profile is mostly CRUD of optional fields; adding methods for each setter would be ceremony without payoff.

The choice was made per aggregate, not project-wide — this is the stance the lab recommends.

## 7. Answers to the Lab 2 prompt questions

**(1) What changed architecturally vs. Lab 1?**
Horizontal "by-kind" folders were replaced by vertical "by-domain" packages each split into 4 layers (see §2). ORM is behind mappers; domain models are framework-free dataclasses; repositories exist as interfaces in `domain/` and implementations in `infrastructure/`; HTTP errors are mapped in one place per domain instead of raised from services.

**(2) What are the benefits?**
Domain purity is mechanically verifiable; unit tests run without a database; framework/DB swaps are bounded to a single layer; a change to a feature lives inside one folder. See §3.

**(3) What are the drawbacks?**
Boilerplate (mappers, duplicated DTO/schemas), more files per feature, inconsistency while some domains remain flat, and higher onboarding cost. See §4.

**(4) How easy is it to swap the DB or the web framework?**
Very easy, and we have a concrete proof: [tests/unit/test_activity.py](../../tests/unit/test_activity.py) substitutes the entire storage layer with dict-backed fakes and all use cases run unchanged. Framework swap is similarly bounded to `presentation/`. See §5.

**(5) Rich or Anemic — why?**
Per domain, not globally. Activity is Rich because its invariants are numerous and enforcement-critical; User profile is Anemic because it is CRUD with almost no rules; Auth sits closer to Rich. Full reasoning in [ADR 0002](../adr/0002-activity-rich-domain-model.md) and §6.
