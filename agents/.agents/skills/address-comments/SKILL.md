---
name: address-comments
description: Collects review feedback across every PR in the current GitHub stack, decides each item with the user, applies accepted changes to the branch that owns the feedback, and resolves only implemented review threads. Use when addressing PR comments, review feedback, stack feedback, or when the user says /address-comments.
compatibility: Requires git, gh authenticated to GitHub, github/gh-stack, and Python 3.
---

# Address PR Comments

Work through review feedback for the **current GitHub stack**. A review thread belongs to the PR where it was posted; its implementation commit must land on that PR's branch, never opportunistically on the tip.

## 1. Preflight and inventory

1. Confirm this is a git repository, `gh auth status` succeeds, `gh stack --help` succeeds, and the working tree is clean. Stop on any failure; do not stash, discard, or overwrite user work.
2. Identify the stack with `gh stack view --json`. If it cannot identify a stack (for example the current branch belongs to several stacks), ask the user to check out any branch in the intended stack, then retry. Extract its open PR numbers, ordered base → tip. Report that order and ask only if it is ambiguous.
3. Run the bundled collector, preserving its JSON as the source inventory, then create `/tmp/address-comments-decisions.md` as the decision ledger:

```bash
python3 scripts/review_feedback.py list --pr <base-pr> --pr <next-pr> > /tmp/address-comments.json
```

It collects all review threads plus PR conversation comments and review summaries. Review threads are the only GitHub feedback items that can be resolved. Do not claim conversation comments or review summaries were resolved; offer to reply to them when the user requests it.

4. Show counts per PR: unresolved/resolved/outdated review threads, conversation comments, and review summaries. Treat already-resolved threads as audit context, not new work, unless the user asks to reopen them.

## 2. Decide feedback interactively

Go through every **unresolved** review thread, then each non-empty conversation comment and review summary, one item at a time. Include PR number, author, link, file/line and outdated status where available, the full comment text, and the relevant code/diff context.

For each item, recommend a disposition and wait for the user's decision. Record its type, PR number, stable GitHub node ID, link, disposition, rationale, and implementation/reply plan in the ledger before moving on:

- `address` — specific implementation plan; review thread is eligible for resolution after the change is pushed.
- `reply` — exact response or rationale; no code change and no thread resolution unless the user explicitly directs it.
- `defer` — follow-up destination (issue/link/owner); do not resolve.
- `decline` — rationale; do not resolve.
- `already-addressed` — verify the implementation is on that PR's remote head; eligible for resolution only after user confirms.
- `not-actionable` — duplicates, acknowledgements, or informational feedback; never silently resolve it.

Do not collapse related comments into one decision without showing every item and obtaining a decision for each. If a comment is unclear, investigate the code or ask a focused question rather than guessing. When all decisions are recorded, present a compact per-PR implementation plan and get confirmation before editing.

## 3. Implement on the owning PRs

1. Work base → tip. For each PR with `address` decisions, use `gh stack checkout <pr-number>` and confirm `git branch --show-current` matches that PR's head branch.
2. Implement only that PR's accepted decisions. A comment on an upper PR may change code introduced lower down, but the commit still belongs on the upper PR unless the user explicitly moves the decision.
3. Read the repository's instructions before changing code. Run the relevant format, generation, and test commands. Commit a focused change on the owning branch, then push/update the stack with the repository's prescribed ship flow; otherwise use `gh stack submit` after the relevant checks.
4. After lower-branch changes, restack all upper branches before continuing (`gh stack rebase --upstack --no-trunk` when appropriate). Never force-push, hard-reset, or lose uncommitted work.
5. Verify each addressed thread's change is present in the owning PR's updated remote diff before marking it eligible. If tests fail or the intended change cannot be made, return that item to the user rather than resolving it.

## 4. Return to tip and resolve verified threads

1. Submit/push all changed PR branches and wait until `gh pr view <pr-number> --json headRefOid` shows their updated heads. Run `gh stack top` to return to the stack tip.
2. Re-fetch feedback into a new file and match each `address` or confirmed `already-addressed` decision by review-thread ID. Resolve only IDs that are still unresolved and whose owning PR contains the verified implementation:

```bash
python3 scripts/review_feedback.py resolve <thread-id> [<thread-id> ...]
```

3. Re-run the collector. Report, per PR: resolved thread IDs/links, intentionally left-open threads with their disposition, non-resolvable comments/reviews replied to (if any), changes made, and checks run.

## Hard rules

- Decisions precede edits; no implementation starts while feedback remains undecided.
- Preserve PR ownership: changes and commits go to the branch whose PR received the feedback.
- Resolve only review threads with verified implemented decisions. Never resolve a declined, deferred, reply-only, uncertain, or failed item.
- GitHub does not support resolving PR conversation comments or review summaries. State that plainly rather than treating a reply as resolution.
- Finish on the stack tip. Do not merge PRs.
