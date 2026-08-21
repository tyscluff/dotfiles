---
name: start-ticket
description: Start work on a Linear ticket end-to-end — branch via GitHub stacked PRs, read the ticket, read the relevant code, then grill the implementation. Use when the user types /start-ticket followed by a Linear ticket ID (e.g. LIG-496), or asks to "start", "pick up", or "begin work on" a Linear ticket.
---

# Start Ticket

Bootstrap work on a Linear ticket: get on a branch, load the ticket and its
surrounding code into context, then run a grilling session to align on the
implementation before writing any code.

The ticket ID is passed as the argument (e.g. `LIG-496`). Normalize it to
uppercase. If no argument is given, ask for the ticket ID and stop.

## Workflow

Do these in order. Steps 1 and 2 can run in parallel — start the git work and
the Linear fetch in the same turn.

### 1. Branch (GitHub stack)

Branch name is the ticket ID, uppercase, nothing else (e.g. `LIG-496`).
PR title (when shipped later) is the same ticket id only.

- Check working tree is clean first (`git status --porcelain`). If there are
  uncommitted changes, stop and surface them — do NOT stash or discard.
- Ensure GitHub stacked PRs are available: `gh stack --help`. If missing:
  `gh extension install github/gh-stack`. If install fails, stop and say so
  (do not silently invent a non-stack workflow unless the user opts in).
- If the branch already exists:
  - Check it out (`git checkout LIG-496`).
  - If it is not in a local stack (`gh stack view` fails), adopt it with
    `gh stack init LIG-496` (or `gh stack checkout LIG-496` if it already
    exists as a remote stack).
- Otherwise create it from an up-to-date `main` as a one-layer stack:
  `git checkout main && git pull && gh stack init LIG-496`.
- Never force-push, reset, or touch other branches.
- Do **not** use Graphite (`gt`).

If this ticket is meant to sit **on top of** another open ticket/PR (part of a
milestone stack), prefer `/start-stack` or stay on the parent branch and run
`gh stack add LIG-496` instead of basing off `main`.

### 2. Read the ticket

Fetch the full issue via the Linear MCP: `mcp__linear-server__get_issue` with
the ticket ID. Also pull its comments (`mcp__linear-server__list_comments`) —
decisions and clarifications often live there, not in the description.

Note the ticket's title, description, acceptance criteria, linked
issues/parent/milestone, and any design docs or Linear documents it references.

If the ticket belongs to a **milestone with sibling tickets**, mention that to
the user — a multi-PR stack may want `/start-stack` instead of a lone branch
off `main`.

### 3. Read the pertinent code

Figure out what this ticket touches and read it before grilling — the grill is
only useful if the implementation is grounded in the actual code.

- Consult `CONTEXT-MAP.md` at the repo root and the relevant per-context
  `CONTEXT.md` to locate the right subproject(s) and domain language.
- Read the relevant subproject `CLAUDE.md` files (`api/`, `web-app/`,
  `mobile-app/`, `gob/`, `agents/`) for the areas the ticket touches.
- Search the monorepo for the entities, routes, components, and services the
  ticket names. Use the Explore agent for broad fan-out when the surface area
  is wide; read the key files directly once located.
- Check the auto-memory index (`MEMORY.md`) for prior context on this ticket or
  its initiative — many tickets have a linked memory file.

Aim to enter the grill knowing where the change will live and what it will
touch, not just what the ticket says.

### 4. Grill the implementation

Load and follow the repo-local skill at **`.agents/skills/grill-me/SKILL.md`**
(read the file; do not look for a global/`Skill` tool install). Use it to
interrogate the implementation approach until you and the user reach shared
understanding. Ground the grilling in the ticket's acceptance criteria and the
code you just read — surface the real decision points, ambiguities, and
tradeoffs, not generic questions.

## Notes

- This skill sets up and aligns; it does not implement. Writing code happens
  after the grill, once the approach is agreed.
- When implementing later in this monorepo, ship with
  `just ship "what changed and why"` (prepare → commit → `gh stack submit` →
  PR title = ticket id). Do not hand-roll Graphite or forget prepare/OpenAPI.
- Respect the user's plan-before-coding preference: the grill IS the alignment
  step. Don't jump to edits when it ends unless the user says so.
