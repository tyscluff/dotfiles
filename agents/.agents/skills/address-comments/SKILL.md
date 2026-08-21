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

Linear diff reviews are a separate feedback surface. When a PR has a Linear review link or the user says they reviewed in Linear, use the Linear MCP `get_diff_threads` tool to inventory those threads too. GitHub review-thread resolution does not resolve Linear diff threads, and vice versa.

4. Show counts per PR and source: unresolved/resolved/outdated review threads, conversation comments, and review summaries. Treat already-resolved threads as audit context, not new work, unless the user asks to reopen them. Treat automated Linear linkbacks (`author: linear-code` with `<!-- linear-linkback -->`) as ignored audit metadata: include them in counts but do not present them for a decision, reply to them, or record individual ledger entries.
5. Compare the actionable GitHub and Linear feedback for the same underlying concern. Group duplicate or materially overlapping comments—even when their wording, location, or proposed fix differs—into one concern, while retaining every source item and its ID/link in that concern. Do not group distinct concerns merely because they touch the same code.

## 2. Discuss and decide feedback interactively

Discuss each actionable concern, rather than mechanically processing individual comments. For a grouped concern, show every linked GitHub and Linear item with its PR number, author, link, file/line and outdated status where available, plus the full comment text and relevant code/diff context. Make clear which comments are treated as the same concern and why.

First understand what the reviewer needs. A comment may request a code change, raise a design question, seek an explanation, ask for investigation, or identify a symptom rather than the root cause. Analyze the underlying concern and the proposed fix. When useful, identify assumptions, risks, root causes, or alternatives the comment does not mention. Recommend a thoughtful path forward with its rationale and tradeoffs, then discuss it with the user until they choose an outcome. Do not force the discussion into a fixed menu of dispositions.

Record each concern in the ledger, including its source items (type, PR number, stable GitHub node ID or Linear thread ID, and link), grouping rationale, the discussion and decision, rationale, and implementation/reply/follow-up plan. Use a precise outcome that fits the decision—for example, implement, reply with clarification, investigate, defer, decline, already addressed, not actionable, or resolve without change. These examples are not exhaustive.

A grouped concern has one substantive decision and one coordinated plan, but every source item remains independently tracked for replies and resolution. Do not require duplicate decisions for comments in the same concern. A comment that is unclear should prompt focused investigation or a question, not a guess. When all concerns are decided, present a compact per-PR implementation plan and get confirmation before editing.

## 3. Implement on the owning PRs

1. Work base → tip. For each PR with `address` decisions, use `gh stack checkout <pr-number>` and confirm `git branch --show-current` matches that PR's head branch.
2. Implement only that PR's accepted decisions. A comment on an upper PR may change code introduced lower down, but the commit still belongs on the upper PR unless the user explicitly moves the decision.
3. Read the repository's instructions before changing code. Run the relevant format, generation, and test commands. Commit a focused change on the owning branch, then push/update the stack with the repository's prescribed ship flow; otherwise use `gh stack submit` after the relevant checks.
4. After lower-branch changes, restack all upper branches before continuing (`gh stack rebase --upstack --no-trunk` when appropriate). Never force-push, hard-reset, or lose uncommitted work.
5. Verify each addressed thread's change is present in the owning PR's updated remote diff before marking it eligible. A `resolve-without-change` thread is eligible only when the user's explicit decision and rationale are recorded. If tests fail or the intended change cannot be made, return that item to the user rather than resolving it.

## 4. Return to tip and resolve verified threads

1. Submit/push all changed PR branches and wait until `gh pr view <pr-number> --json headRefOid` shows their updated heads. Run `gh stack top` to return to the stack tip.
2. Re-fetch feedback into a new file and match each `address`, confirmed `already-addressed`, or user-approved `resolve-without-change` decision by review-thread ID. Resolve only IDs that are still unresolved and either whose owning PR contains the verified implementation or whose no-change rationale is recorded:

```bash
python3 scripts/review_feedback.py resolve <thread-id> [<thread-id> ...]
```

3. For a Linear diff thread that is eligible for resolution, use the Linear MCP `resolve_diff_thread` tool with its Linear thread ID. Verify it is resolved with `get_diff_threads`. Apply the same decision rules: resolve only verified implementation decisions or explicit user-approved `resolve-without-change` decisions.
4. Re-run the GitHub collector and re-fetch applicable Linear diff threads. Report, per PR: resolved GitHub and Linear thread IDs/links, intentionally left-open threads with their disposition, non-resolvable comments/reviews replied to (if any), changes made, and checks run.

## Hard rules

- Decisions precede edits; no implementation starts while feedback remains undecided.
- Preserve PR ownership: changes and commits go to the branch whose PR received the feedback.
- Resolve only review threads with a verified implementation or an explicit user-approved `resolve-without-change` decision. Never resolve a declined, deferred, reply-only, uncertain, or failed item.
- GitHub does not support resolving PR conversation comments or review summaries. State that plainly rather than treating a reply as resolution.
- Linear diff-review threads require the Linear MCP `resolve_diff_thread` tool; a GitHub resolution does not close them.
- Finish on the stack tip. Do not merge PRs.
