# Agile Methodology — Health Patch Team

## Team Context

We are a micro-team of 4: three backend developers with clearly separated domains — **Identity & Auth** (Daniil), **Activity & Workouts** (Maksym), **Nutrition & Diet** (Mykhailo) — and a **Project Manager** (Oleksandr). We are building a FastAPI/PostgreSQL backend MVP for Health Patch, a gamified fitness platform.

**Tools already in place:**
- GitHub Project (Kanban board: `Todo → In Progress → Done`)
- Pull Request review as a mandatory merge gate
- Regular sync meetings in Discord
- Async coordination via Telegram
- CI with Ruff on every PR

---

## Proposed Methodology: Scrumban Hybrid

Classic Scrum for a 4-person team (where one is a part-time PM and the rest are KPI students with their own academic deadlines) is overhead. Classic Kanban is too passive — no rhythm, no cadence. So we took the best of both worlds: **Scrumban** — ceremonies and cadence from Scrum, flow visualization and WIP limits from Kanban.

---

## What We Took from Scrum

**2-week sprints** as the planning unit. A shorter horizon reduces scope creep risk (explicitly listed as High-impact in `techreq.md`) and gives the team a sense of progress. Longer sprints break against academic load.

**Three core ceremonies, kept lean:**

| Ceremony | Duration | Purpose |
|---|---|---|
| Sprint Planning | ~30 min | Each domain owner adds 2–4 issues they can realistically close in two weeks. PM moderates and flags cross-domain dependencies. |
| Weekly Sync | 15–20 min | Classic format: done / blocked / next. Daily standups for 4 parallel-domain developers are shame-driven performance, not real coordination. |
| Sprint Retro | 20–30 min | What worked, what hurt, one concrete change for the next sprint. |

> **No Sprint Review** as a separate event — its role is covered by PR review, where code is demonstrated and discussed in the context of real changes.

---

## What We Took from Kanban

**Flow visualization** via GitHub Project with three states (`Todo → In Progress → Done`) — the board already exists and works.

**WIP limit = 1** per developer in-progress at a time. When each person is the sole owner of their domain, running two tasks in parallel means two half-finished modules instead of one done one.

**Pull model** — a task moves to *In Progress* only when the developer is ready to pick it up, not because the PM pushed it there. This respects each person's academic schedule.

---

## Agile Principles We Ground This In

From the Agile Manifesto, four principles resonate most for our context:

1. **Working software over comprehensive documentation** — we already have full tech docs (`requirements.md`, `techreq.md`, ER diagram). Going forward we focus on code; docs only update when API contracts or DB schema change.
2. **Responding to change over following a plan** — requirements are frozen at v1.0, but sprint-level priorities shift. If someone discovers a layer responsibility leak (like issue #33 currently in Todo), it goes into the next sprint without bureaucracy.
3. **Individuals and interactions over processes and tools** — decisions happen in Discord calls, not formal documents. We only document the outcome in TG/Issues.
4. **Customer collaboration** — our "customer" is the reviewing lecturer and each other as first users. A Pull Request is a negotiation about quality, not a rubber stamp.

---

## Who Owns the Process

In a 4-person team, a dedicated Scrum Master is a luxury we skip. Instead:

**PM (Oleksandr)** acts as process facilitator: moderates Planning and Retro, keeps the board reflecting reality, surfaces blockers. He does *not* assign tasks and does *not* dictate how they get done.

**Each developer** owns their domain and is personally responsible for respecting the WIP limit, keeping card statuses up to date, and opening PRs on time. This is a direct consequence of the equality principle from `team.md`.

**The team collectively** governs process health through Retro: if something breaks, we fix the process at retro — not the person.

**CI (GitHub Actions + Ruff)** is the automated technical quality gate, independent of human factors.

---

## Why Scrumban — Three "Whys"

**Why Scrumban and not pure Scrum?**
Pure Scrum assumes a cross-functional team where anyone can pick up any task. Our domains are personal: Maksym won't touch Identity, Daniil won't touch Nutrition. A classic sprint backlog doesn't work here — we effectively have three parallel mini-backlogs. A Kanban flow acknowledges this honestly.

**Why Scrumban and not pure Kanban?**
Without the rhythm of sprints and Retro, a student team drifts — academic deadlines crowd out project work. The two-week cadence creates an "artificial" deadline that maintains momentum and a regular reflection point.

**Why WIP = 1 and pull model?**
It directly reflects the `team.md` principle of *Quality over speed*. Every domain is critical for MVP — if Identity isn't ready, nothing works. Better to close one task completely than keep three half-open.

---

## What One Sprint Cycle Looks Like in Practice

```
Week 1 — Monday
  └─ 30-min Planning in Discord
     Each developer commits to 2–4 issues
     PM pins sprint goals in Telegram

Week 1–2 — Ongoing
  └─ Develop → open PR → review (≥1 teammate) → merge → card to Done
     Wednesday sync: 15 min

Week 2 — End
  └─ 20-min Retro
     One process change decision → logged in docs/retro-log.md
     Immediately followed by next Sprint Planning
```

---

## What Agile Actually Is — Short and Honest

Agile is not a methodology — it's a set of values about how teams respond to uncertainty. The core idea: big six-month plans almost always turn out wrong, so instead of one big plan we run many short cycles — plan for 1–4 weeks, build, look at the result, adjust. Scrum, Kanban, XP, SAFe are all concrete recipes for implementing that idea. Our Scrumban is also a recipe, tailored to our team's size and reality.

The key thing to understand: **Agile is not about having no documentation, no plan, or no discipline.** It is about the discipline of short feedback loops — from users, from code (tests/CI), from the team (Retro). Everything else follows from that.
