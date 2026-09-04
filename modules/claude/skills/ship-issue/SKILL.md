---
name: ship-issue
description: >-
  Ship one Linear issue to reviewed, pushed PRs. Use when shipping a Linear issue
  (user names it or /ship-idea hands it over).
argument-hint: "MRGFY-1234"
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, Skill, TodoWrite, ToolSearch, Artifact, mcp__linear-server__get_issue, mcp__linear-server__save_comment
---

# Ship an issue

One Linear issue → implemented, reviewed, pushed PRs, using **mergify tooling only**.

The mechanical steps live in `scripts/ship-issue.py`, bundled next to this file. Define once
and reuse — the skill's base directory is given when this skill loads:

```bash
SHIP='python3 "<base directory of this skill>/scripts/ship-issue.py"'
```

Put the steps on your todo list up front: a ship often resumes after an interruption,
and the checklist is what a resumed run reads to find its place.

## Ground rules (non-negotiable)

- **A fork is mine.** Where the work offers a real choice — scope past the smallest
  slice, a plan that disagrees with the code, a review finding you'd rather not keep, a
  surprising push, red CI — stop, lay out the options with your recommendation, and wait
  for my answer. Later steps name their forks; treat any other one the same way.
- **Push with `$SHIP push`.** Mergify handles branch cleanup and PR lifecycle; let it run.
  Use `git worktree remove` only for local cleanup.
- **Fold trailers into their commits as you amend.** Each commit carries its own `Change-Id`
  from the commit-msg hook — preserve all of them across step 7's folding.
- **All work after Step 2 runs inside the worktree.** `$SHIP` subcommands take `--worktree`;
  for anything by hand, use `git -C "$WT" …` or `cd "$WT"` before mergify/pnpm. A commit
  from the source checkout lands on the wrong branch — the worst failure this skill can cause.
- **Pass `--root "$ROOT"` wherever a subcommand takes it.** It defaults to the current
  directory, which is the worktree from Step 3 on — wrong default stacks the second tree
  inside the first.
- **Show every error whole.** Display the subcommand's exact stderr, then treat it as a fork.

## Step 1 — Preflight

```bash
ROOT=$(git rev-parse --show-toplevel)
$SHIP preflight --root "$ROOT"
```

A missing commit-msg hook is a fork — later commits would carry no `Change-Id`.

**Done when:** preflight passes.

## Step 2 — Read, grill, and plan

`$ARGUMENTS` names one Linear issue. Fetch it with the Linear MCP `get_issue` tool and
read it for **intent**. Issues are written before work is understood — proposed steps are
often stale. Judge whether intent is clear enough to implement. Where real choices remain,
read the relevant code (questions about this codebase, not the issue's prose), then invoke
`/mattpocock-skills:grilling` and run it to completion.

While grilling, settle the **seams** where tests sit; Step 5 writes them first.

Post the settled plan back to the issue with `save_comment` — a grill that stays in
this session is invisible work.

```bash
$SHIP branch --issue MRGFY-1234 --title "<the issue title>"
```

Carry that branch name through the rest.

**Done when:** grill ran to completion, seams are settled, plan is posted, and you hold
`<branch>`.

## Step 3 — Worktree

```bash
WT=$($SHIP worktree --root "$ROOT" --branch <branch>)
```

One call resumes an existing ship or creates the worktree off fresh `origin/main`, and
migrates any uncommitted work from the source checkout.

**Done when:** `$WT` exists and holds any work that was in the source checkout.

## Step 4 — Dashboard server (only when the change touches `dashboard/`)

Judge that from the issue's labels or the plan from Step 2: on an unimplemented issue the
diff is empty, and reading that emptiness as "no dashboard work" leaves the server down
through exactly the step you want to watch.

```bash
cd "$WT/dashboard" && pnpm start   # background; report the URL
```

**Done when:** the URL is reported, or the change stays clear of `dashboard/`.

## Step 5 — Implement

Build the smallest useful slice and name what you are leaving out (fork, if scope is unclear).
Parallelism, CLI arguments, a new abstraction layer — each is a fork. Same for an issue
that disagrees with the code once you are in it.

Work test-first at the seams from Step 2: invoke `/mattpocock-skills:tdd` and run red → green
per vertical slice. Red before green proves the test fails without the code.

Tests live in the same commit as the code they cover — a commit whose tests sit in another PR
is not independently deployable.

When two concerns are independent (each stands alone, no ordering), split them into separate
stacks at Step 7 rather than chaining them into one branch.

**Done when:** the change is complete and its tests go red without it.

## Step 6 — Format and lint

Settle style before committing, so Step 8 spends its attention on substance. Once per
area you touched:

```bash
$SHIP lint --worktree "$WT" --area dashboard
$SHIP lint --worktree "$WT" --area engine
```

**Done when:** every touched area reports clean.

## Step 7 — Commit by concern

One **concern** is a unit of code change that stands alone: it solves one problem, touches
one subsystem, or moves one abstraction. One concern = one commit = one PR = one independently
deployable unit.

Split commits with `git add -p` or path-scoped `git add`, and commit every concern—each
gets its own `Change-Id` from mergify's commit-msg hook.

Messages follow CLAUDE.md. The Linear footer is `Fixes:` (commit that completes the issue)
or `References:` (commit only relates to it) — state which you used.

When two concerns are independent (Step 5 flagged this), create a separate stack:

```bash
$SHIP split --root "$ROOT" --worktree "$WT" --sha <sha> --branch <branch-2>
```

**Done when:** the worktree is clean and every branch/worktree pair is on your list —
Steps 8 to 10 run per pair.

## Step 8 — Review

The stack's size sets the review depth:

```bash
$SHIP review-level --worktree "$WT"
```

Invoke `/code-review <that level> --fix`. It reviews the committed branch-vs-base diff and
applies every finding to the working tree. A finding you'd rather not keep is reverted
first, then proposed as a fork.

Fold what you kept into the commit it belongs to:

```bash
$SHIP fold --worktree "$WT"                # single-commit stack: amends
$SHIP fold --worktree "$WT" --sha <sha>    # multi-commit stack: fixup + autosquash
```

**Done when:** every kept finding sits in the commit it belongs to and the worktree is
clean.

## Step 9 — Test gate

Each commit is green before it becomes a PR. Choosing which tests prove the change is
your judgment; running them is not:

```bash
$SHIP test --worktree "$WT" --area dashboard --paths <files>
$SHIP test --worktree "$WT" --area engine --paths <path>
```

A run that collects nothing sends you back to Step 5 to write the test. When Step 8
folded code changes, re-run Step 6 first.

**Done when:** every worktree from Step 7 is green.

## Step 10 — Push each stack

Independent stacks are independent pushes — once per worktree:

```bash
$SHIP push --worktree "$WT" --dry-run
```

On a branch with existing PRs, a dry run that would update PRs from unrelated commits is
a fork. Then `$SHIP push --worktree "$WT"`, which prints each PR URL.

**Done when:** every stack is pushed and you hold its PR numbers.

## Step 11 — Report

One CI snapshot per PR:

```bash
$SHIP report --worktree "$WT" --prs <n> [<n> …]
```

Relay its `## Shipped` summary and add `Independent stacks: <count>`.

**Done when:** every PR from Step 10 appears in the summary with its CI state.
