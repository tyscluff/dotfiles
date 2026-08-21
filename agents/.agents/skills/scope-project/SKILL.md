---
name: scope-project
description: Run a structured, code-change-free scoping session for a Linear project across four gated phases (Requirements, Context gathering, Alignment, Scoping) that ends by creating Linear tickets. Use when the user types /scope-project followed by a Linear project name, or asks to scope, plan, or break down a project into tickets.
---

# Scope Project

Run a facilitated scoping session for a Linear project. The output is **Linear
tickets**, not code. You write **zero** code this whole session — no edits, no
files, no scaffolding. If you feel the urge to implement, you have left scoping.

The project name is passed as the argument. If none is given, ask for it and stop.

## Your stance: scope like a planner, not an implementer

A great scoper is trying to *understand and divide the work*, not start it. Hold
this posture the entire session, and pull the user into it too:

- **Think in outcomes and seams, not files.** What does "done" look like? Where
  are the natural fracture lines the work breaks along? Implementation detail is
  a distraction until the seams are clear.
- **Surface unknowns early and loudly.** The most valuable thing you produce is a
  named list of decisions and risks. "We don't know X yet" is a finding, not a
  failure. Chase the questions whose answers change the shape of the work.
- **Right-size, don't over-plan.** Enough scoping to divide the work confidently,
  no more. Resist gold-plating the plan.
- **Slice into shippable PRs.** Each ticket = one PR (~≤500 LOC target), cut
  vertically through the layers of **one** service — not a horizontal "do all
  the DB work" layer, and not a multi-service mega-ticket. Prefer many thin
  slices over few thick ones; don't micro-split the same concern.
- **Group PRs into single-service stacks.** Use Linear milestones as GitHub PR
  stacks: one milestone, one service (`api` / `web-app` / `caged_wisdom` / …),
  independently shippable as a group.
- **Sequence by dependency and risk.** What unblocks the most? What retires the
  scariest unknown first? Order tickets (stack order) and milestones (cross-service
  order) so the riskiest assumptions get tested early.
- **Coach the user.** When they drift into "how do we build it", gently pull them
  back to "what are we building and how does it divide". Ask the planner's
  questions out loud so they start asking them too.

## Setup: resolve the project

Use `mcp__linear-server__list_projects` to find the project by the given name.
If there is no clean match, show the closest candidates and ask which one. Read
the project (`mcp__linear-server__get_project`), its description, and any linked
documents so you enter the session grounded. Note the project's **team** — you
need its ID for ticket creation later.

## The four phases

Move through them in order. **Each phase is gated:** end it with a short summary
of what was established, then explicitly ask the user to confirm before advancing.
Do not race ahead. If an earlier phase's assumptions crack later, go back.

### Phase 1 — Requirements

Establish *what we're doing and why*, at a high level. Not solutions — the goal.

- What problem does this project solve, and for whom?
- What's the outcome that means "done"? What's explicitly **out** of scope?
- Any hard constraints (deadlines, dependencies, non-negotiables)?

Keep it high-level. Don't let the conversation dive into implementation yet.
Gate: reflect the requirements back in a few bullets and get confirmation.

### Phase 2 — Context gathering

Now *you* do the work: thoroughly understand the existing code and systems this
project will touch. This is the phase where you read, a lot. Read-only.

- Consult `CONTEXT-MAP.md` at the repo root and the relevant per-context
  `CONTEXT.md` files to find the right subproject(s) and domain language.
- Read the relevant subproject `CLAUDE.md` files (`api/`, `web-app/`,
  `mobile-app/`, `gob/`, `agents/`) for the areas in play.
- Check the auto-memory index (`MEMORY.md`) — this project or its initiative may
  already have a memory file with prior decisions.
- Search the monorepo for the entities, routes, services, and components the
  project names. Use the `Explore` agent for broad fan-out; read key files
  directly once located.

Gate: report back what exists today — the relevant architecture, what's already
there to reuse, and where new work will have to live. Confirm your mental model
with the user before moving on.

### Phase 3 — Alignment

Discuss the high-level design and the important technical decisions. This is
where unknowns get resolved. Drive it as a conversation, one decision at a time.

- Enumerate the real decision points — the forks where the work could go
  materially different ways. For each: the options, the tradeoffs, a
  recommendation, and the user's call.
- Name the risks and open questions. Decide which must be resolved now versus
  which can be deferred into a ticket.
- If the design is contentious or has many interacting decisions, load and
  follow **`.agents/skills/grill-me/SKILL.md`** (repo-local; read the file) to
  stress-test the emerging plan.

Gate: produce a short list of the decisions made and questions still open.
Confirm before scoping.

### Phase 4 — Scoping

Break the aligned work into tickets **and milestones** that map cleanly onto
**GitHub stacked PRs**. This is the division step — still no code.

#### Shipping units (non-negotiable framing)

| Unit | Maps to | Rule |
|------|---------|------|
| **1 Linear ticket** | **1 PR** (branch + PR title = ticket id, e.g. `LIG-518`) | One concern, independently reviewable |
| **1 Linear milestone** | **1 GitHub stack** of those PRs (`gh stack`) | Ordered chain; lower PRs base upper ones |
| **PR size** | Aim **≤ ~500 lines** changed per PR | Smaller is fine; don't micro-split one concern across many PRs |
| **Stack / milestone scope** | **One service only** | A given stack touches only one of `api/`, `web-app/`, `caged_wisdom/`, `mobile-app/`, `gob/` (etc.). Cross-service work → **separate milestones/stacks**, sequenced by dependency |

Keep stacks **independently shippable groups**: landing a milestone should leave
the product in a coherent state without requiring a sibling stack from another
service to merge in the same breath (unless you explicitly call out a temporary
contract/feature-flag bridge in Alignment).

#### How to draft the breakdown

1. **Group by service first.** If the project needs api + web-app + agents,
   plan **separate milestones** (e.g. "API: …", "Web: …"), not one mixed stack.
2. **Within a service, slice into tickets ≈ PRs.** Each ticket is a vertical
   slice through that service's layers only — thin, complete, verifiable.
3. **Size-check every ticket against ~500 LOC.** You will not know exact line
   counts; estimate from surface area (files/endpoints/components touched).
   If a slice is likely much larger, split along natural seams. If two slices
   are tiny and the same concern, merge them rather than over-fragmenting.
4. **Order tickets inside a milestone** by dependency (blockers first). That
   order **is** the stack order for `start-stack` / `gh stack init` → `add`.
5. **Order milestones** when one service's stack must land before another's
   (e.g. api contract before web-app consumers).

#### Present to the user

- Group the draft under **proposed milestones** (each = one stack / one service).
- Under each milestone, numbered tickets with: **title**, one-line **what to
  build** (outcome, not layer-by-layer), **blocked by**, and a rough **size
  note** if a slice is at risk of blowing past ~500 LOC.
- Quiz: right service boundaries? stack/milestone splits? granularity? deps?
  anything to split, merge, or cut?
- Iterate until they approve. **Do not create any tickets or milestones before
  approval.**

## Creating milestones and tickets

Only after the user approves the breakdown.

### Milestones (stacks)

For each approved stack group, create or reuse a Linear **milestone** on the
project (`mcp__linear-server__create_milestone` / project milestone APIs as
available). Name it so the service + outcome are obvious (e.g.
`API: complications catalog`). One milestone = one GitHub PR stack.

### Tickets (PRs)

For each slice, create a Linear issue with `mcp__linear-server__save_issue`:

- **Team**: the project's team (from setup).
- **Project**: link every ticket to this project.
- **Milestone**: the stack milestone this PR belongs to.
- **Status**: `Todo`. Resolve the exact status via
  `mcp__linear-server__list_issue_statuses` for the team and pick the one named
  "Todo" (an unstarted-type status).
- **Assignee**: the user running this skill. Resolve their user ID via
  `mcp__linear-server__list_users` matching their email
  (`tyson.cluff@lighthousefh.com`); reuse it for every ticket.
- **Body**: use the template below.

Create in dependency order (blockers first) so you can reference real issue
identifiers in "Blocked by". After creating, report:

1. Milestones (each = intended `gh stack`)
2. Tickets under each, in stack order, with identifiers and URLs

Remind the user: implement with `/start-stack` (or `/start-ticket` for a lone
PR); ship via `just ship` / GitHub stacked PRs — not Graphite.

<issue-template>
## What to build

Concise description of this vertical slice — the end-to-end behavior, not a
layer-by-layer plan. Avoid file paths and code snippets; they go stale.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Blocked by

Reference to blocking ticket(s), or "None — can start immediately".

## Open questions

Any unresolved decisions carried out of the Alignment phase (omit if none).
</issue-template>
