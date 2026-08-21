---
name: start-stack
description: >
  Bootstrap work on a Linear milestone as a GitHub stacked-PR chain: load the milestone and its tickets, read the end-to-end code, grill for alignment, then implement bottom-up — one ticket per PR, branch LIG-XXX, ship each PR as soon as it's ready so later stack work can proceed in parallel with review. Use when the user runs /start-stack with a milestone name or ID, or asks to start a stack, milestone stack, GitHub stack, stacked PRs, or multi-PR Linear milestone.
---

# Start Stack

Bootstrap work on a **Linear project milestone** where the milestone is the unit of work that maps to a **GitHub stack of pull requests**: each ticket in the milestone becomes one PR, stacked in dependency order, shipped as soon as that ticket is ready so the user can review lower PRs while upper ones are still being built.

This is the multi-PR counterpart to `start-ticket`. Same load-context-and-grill discipline up front; then implement and ship the stack ticket-by-ticket instead of stopping after alignment.

## Mental model

| Concept | Mapping |
|---------|---------|
| Linear **project** | Product/initiative container |
| Linear **milestone** | The whole GitHub PR stack (end goal of this run) |
| Linear **ticket** (`LIG-NNN`) | One commit series → one branch → one PR |
| GitHub **stack** | Ordered PRs via `gh stack`; lower PRs are bases for upper ones |
| Branch / PR title | Ticket id only: `LIG-NNN` (no summary, no milestone prefix) |

Do **not** treat the milestone as a single branch or a single PR. Do **not** batch the whole stack and only open PRs at the end.

## Arguments

Parse the argument string after `/start-stack` (or freeform equivalent). Accept any of:

- Milestone name (e.g. `Complications catalog`)
- Milestone + project (e.g. `project:Roleplay milestone:Complications catalog`)
- A ticket id that belongs to the milestone (e.g. `LIG-520`) — resolve its milestone and load the full stack
- Empty — ask for the **project** and **milestone** (name or id) and stop until provided

Normalize ticket ids to uppercase (`lig-520` → `LIG-520`).

## Workflow

Phases A–D are setup and alignment. **Do not write product code until the grill (phase D) is done** and the stack order is agreed. Phase E is implementation + ship.

### A. Resolve the milestone and its tickets

Use the Linear MCP.

1. If only a ticket id was given: `get_issue` → read its project + milestone → continue with that milestone.
2. If project is unknown: `list_projects` / `get_project` (with `includeMilestones: true`) to find the right project. Prefer an exact name match; if ambiguous, ask.
3. Load the milestone: `get_milestone` with `project` + `query` (name or id). Also pull milestone comments via `list_comments` with `milestoneId` when you have the UUID.
4. List all issues in the project (`list_issues` with `project`, high `limit`, paginate with `cursor`). Filter to issues whose milestone matches. If the API surface returns milestone on each issue, use that; otherwise match using issue details / `get_issue` as needed.
5. For **each** milestone ticket, fetch full detail + comments:
   - `get_issue`
   - `list_comments` (`issueId`)
6. Note for each ticket: id, title, description, acceptance criteria, status, blocked-by / blocks / related, parent/sub-issues, and any linked design docs.

Present a short stack inventory to the user before deep code reading if the set is large or ambiguous (wrong project, cancelled tickets, etc.). Drop tickets that are Done/Canceled only if the user confirms they are out of scope; otherwise keep them as context for already-landed base work.

### B. Derive stack order (before grilling)

Propose a bottom-up stack order using, in priority:

1. Explicit Linear **blocked-by** / **blocks** relations
2. Ticket descriptions that say “depends on LIG-…” / “after …”
3. Natural layering in this monorepo (e.g. api migration/schema → api handlers → agents/web/mobile consumers)
4. Parent/sub-issue structure if present
5. Numeric ticket order only as a weak fallback

Output an ordered list like:

```text
1. LIG-518 — … (stack base / first PR)
2. LIG-519 — … (stacks on LIG-518)
3. LIG-520 — … (stacks on LIG-519)
```

Flag uncertainty. Ordering is a first-class grill topic — do not invent a confident order from weak signals.

### C. Read the pertinent code (whole stack, not one ticket)

The grill is useless without a grounded end-state picture.

- Read root `CONTEXT-MAP.md` and the relevant per-context `CONTEXT.md` files for domain language.
- Read every subproject `CLAUDE.md` / package guide the stack will touch (`api/`, `web-app/`, `mobile-app/`, `gob/`, `agents/`, etc.).
- Search for entities, routes, components, services, migrations, and tests named by **any** ticket in the milestone — not only the base ticket.
- Use a broad explore pass when surface area is wide; then deep-read the hot files.
- Check auto-memory (`MEMORY.md` / linked memory) for prior work on this initiative.
- Note shared touch points and merge risks across tickets (same files, same schema, OpenAPI regen, etc.).

Aim to enter the grill knowing:

- What “done” looks like for the **whole milestone**
- Where each ticket’s changes will live
- Which tickets share files or contracts
- What already exists vs what must be created

### D. Grill the stack (`grill-me`)

Load and follow the repo-local skill at **`.agents/skills/grill-me/SKILL.md`** (read the file; do not look for a global/`Skill` tool install). Run a full alignment session **before implementing**.

Ground questions in the milestone goal, per-ticket acceptance criteria, and the code you read. Prefer real decision points over generic process questions. Cover at least:

- End state of the milestone (user-visible + technical)
- Confirmed stack order and dependency edges
- Slice boundaries — what must not leak into the wrong PR
- Shared contracts (API shapes, schema, events) and which ticket owns each
- Test strategy per slice and what can wait for upper PRs
- Out of scope / follow-ups that must not bloat this stack
- Anything ticket comments already decided (do not re-litigate settled calls unless the code contradicts them)

Ask one question at a time (per `.agents/skills/grill-me/SKILL.md`). Recommend an answer each time. Explore the codebase instead of asking when the code can answer.

**Stop after the grill** until the user agrees the approach and order. Then proceed to phase E unless they want to pause.

### E. Implement and ship ticket-by-ticket

After alignment, work **bottom-up**. Finish and ship each ticket’s PR before starting the next ticket’s implementation. The user reviews lower PRs while you continue up the stack.

#### E.1 Preflight each ticket

- Working tree clean (`git status --porcelain`). If dirty, stop and surface it — do not stash or discard.
- You are about to work on exactly one ticket id: `LIG-NNN`.
- Ensure GitHub CLI stacked PRs are available: `gh stack --help`. If missing: `gh extension install github/gh-stack`. If install fails, stop — do not silently fall back to a flat branch-per-ticket workflow that loses the stack, unless the user opts into that.

#### E.2 Branch naming (enforced)

- Branch name is **only** the ticket id, uppercase: `LIG-518`.
- No prefixes (`feature/`, `tyson/`), no suffixes, no milestone names in the branch.
- PR **title** is only the ticket id (`LIG-518`). Context goes in the PR body.

#### E.3 Create / checkout the branch (GitHub stack)

- **Base (first) ticket:** from up-to-date `main`:
  - `git checkout main && git pull`
  - `gh stack init LIG-518` (creates/adopts the first layer on trunk). If the branch already exists and is already in a local stack, check it out instead.
- **Subsequent tickets:** branch **off the previous ticket’s branch**, not off `main`:
  - Stay on the parent branch (already shipped/submitted).
  - `gh stack add LIG-519` (adds a layer on the current tip and checks it out).
- Never force-push, never `reset --hard`, never rewrite published history unless the user explicitly asks.

#### E.4 Implement only that ticket’s scope

- Stay inside the agreed slice for `LIG-NNN`.
- Do not “helpfully” pull in the next ticket’s work.
- Follow repo conventions (format, tests, OpenAPI regen, architecture boundaries). Prefer package commands documented in the monorepo (`just`, `npm`, etc.).
- Run the relevant checks for touched packages before shipping.

#### E.5 Ship immediately when the ticket is ready

As soon as that ticket’s work is complete and checks look good, **submit the PR before starting the next ticket**.

Prefer the repo’s ship command when present (this monorepo):

```bash
just ship "Imperative summary of what this ticket changed and why"
```

That flow is expected to: prepare/format/OpenAPI as needed → commit if dirty → ensure local `gh stack` → restack upstack → `gh stack submit --auto --open` → force PR title to the ticket id only.

If `just ship` is not available in the current repo, use:

```bash
gh stack rebase --upstack --no-trunk
gh stack submit --auto --open
gh pr edit --title "LIG-NNN"   # per open stack PR / branch
```

and still enforce:

- Branch name = `LIG-NNN`
- PR title = `LIG-NNN` only
- PR opened/updated **before** moving on

After a successful ship, briefly report to the user: ticket id, PR URL if known, and that you are moving to the next ticket (or that the stack is complete).

#### E.6 Move to the next ticket

- Restack if needed (`gh stack rebase` / via `just ship` restack behavior) so upper work sits on the latest lower commits.
- Repeat E.1–E.5 for the next ticket in the agreed order.
- If review feedback lands on a lower PR while you are higher in the stack, prefer fixing the lower branch and restacking before piling more work on a stale base — call this out to the user if it interrupts flow.

#### E.7 Stack complete

When every in-scope milestone ticket has a submitted PR:

- Summarize the stack (ordered ticket ids + PR links)
- Note any deferred follow-ups agreed in the grill
- Do not merge unless the user asks; shipping for review is the default

## Hard rules

1. **Milestone = GitHub PR stack**, not one mega-PR.
2. **One ticket → one branch → one PR.** Branch and PR title are `LIG-XXX` only.
3. **Push/submit each PR as soon as that ticket is ready** — do not wait until the whole milestone is implemented.
4. **Bottom-up only.** Do not implement ticket N+1 before N is shipped (unless the user explicitly reorders mid-flight).
5. **Grill before code.** Phases A–D complete and agreed before phase E. Grill via `.agents/skills/grill-me/SKILL.md` only.
6. **No destructive git.** No force-push, hard reset, or discarding user work.
7. **Clean tree** before starting each ticket branch.
8. **Scope discipline.** Do not leak later-ticket changes into earlier PRs.
9. Prefer **`just ship`** in this monorepo over hand-rolled `gh stack submit` / forgetting prepare/OpenAPI.
10. **No Graphite.** Do not use `gt` / Graphite for new stacks.

## Relationship to `start-ticket`

| | `start-ticket` | `start-stack` |
|--|----------------|---------------|
| Input | One issue id | Milestone (or issue → its milestone) |
| Context | That issue | Whole milestone + ordered tickets |
| Grill | Implementation of one ticket | End state of stack + order + slice boundaries |
| After grill | Stops (user drives implement) | Implements and ships each PR in order |
| Git | Single branch `LIG-NNN` (often via `gh stack init`) | Stacked branches via `gh stack init` / `add` |

If the user only has one ticket and no milestone stack, prefer `start-ticket`.

## Notes

- Linear milestones require a **project**; always resolve project + milestone together.
- Comments on tickets and on the milestone often hold decisions — read them.
- If the milestone is empty or has a single ticket, say so and offer to fall back to `start-ticket`.
- If stack order cannot be derived confidently, that is the first grill thread — do not invent order silently.
- This skill is agent-facing instructions, not user documentation. Optimize for correct execution.
