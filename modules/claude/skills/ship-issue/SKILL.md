---
name: ship-issue
description: >-
  Ship one Linear issue to landed PRs. Use when the user asks to ship or implement a
  Linear issue, or /ship-idea hands one over.
argument-hint: "ABC-123"
allowed-tools: Agent, Bash, Read, Edit, Write, Grep, Glob, Skill, TodoWrite, ToolSearch, Artifact, mcp__linear-server__get_issue, mcp__linear-server__save_comment
---

# Ship an issue

One Linear issue → PRs that are implemented, reviewed, pushed, green and **landed**.

The mechanical steps live in `scripts/ship-issue.py`, bundled next to this file. Below,
`$SHIP` stands for `"<base directory of this skill>/scripts/ship-issue.py"` — the skill's
base directory is given when this skill loads. Shell variables don't survive from one Bash
call to the next, so write that path out in every call, and do the same for the values
`$ROOT` and `$WT` stand for. `$GREEN` likewise stands for
`"<base directory of this skill>/../green/scripts/green.py"`, the `/green` skill's script.

The repository's guide (`AGENTS.md`, `CLAUDE.md`, including the touched area's own) and
its skills own the tooling: how to format, lint, test, stack and push. Load them; this
skill only sets the order and the rules below.

Put the steps on your todo list up front: a ship often resumes after an interruption,
and the checklist is what a resumed run reads to find its place.

## Ground rules (non-negotiable)

- **A fork is mine.** Where the work offers a real choice — scope past the smallest
  slice, a plan that disagrees with the code, a review finding you'd rather not keep, a
  surprising push — stop, lay out the options with your recommendation, and wait for my
  answer. Later steps name their forks; treat any other one the same way.
- **A rebase conflict is yours.** Resolve it in the worktree with
  `/mattpocock-skills:resolving-merge-conflicts`. Two intents that can't both survive, and
  that the plan doesn't settle, are a fork.
- **Preserve every commit trailer across folds.**
- **All work after Step 2 runs inside the worktree.** For anything you run by hand, use
  `git -C "$WT" …` or `cd "$WT"` before any tool. A commit from the source checkout lands
  on the wrong branch — the worst failure this skill can cause.
- **Show every error whole.** Display the subcommand's exact stderr. An error a rule above
  makes yours — a rebase conflict, a red check — you clear; any other is a fork.

## Step 1 — Preflight

```bash
ROOT=$(git rev-parse --show-toplevel)
$SHIP preflight --root "$ROOT"
```

**Done when:** preflight passes.

## Step 2 — Read, grill, and plan

`$ARGUMENTS` names one Linear issue. Fetch it with the Linear MCP `get_issue` tool and
read it for **intent**. Issues are written before work is understood — proposed steps are
often stale. Read the relevant code, then list the forks the issue plus the code leave
open. Anything you'd want me to review once built is one of them: every PR opens without
my review, so this is where we agree. None open: go straight to the plan. Any open: invoke
`/mattpocock-skills:grilling` and run it to completion.

Either way, settle the **seams** where tests sit; you write them before the code.

Post the settled plan back to the issue with `save_comment` — a plan that stays in
this session is invisible work.

```bash
$SHIP branch --issue ABC-123 --title "<the issue title>"
```

Carry that branch name through the rest.

**Done when:** no fork is left open, seams are settled, plan is posted, and you hold
`<branch>`.

## Step 3 — Worktree

```bash
WT=$($SHIP worktree --root "$ROOT" --branch <branch>)
```

One call resumes an existing ship or creates the worktree off the fresh default branch,
and migrates any uncommitted work from the source checkout.

**Done when:** `$WT` exists and holds any work that was in the source checkout.

## Step 4 — Implement

Build the smallest useful slice and name what you are leaving out (fork, if scope is unclear).
Parallelism, CLI arguments, a new abstraction layer — each is a fork. Same for an issue
that disagrees with the code once you are in it.

Work test-first at the seams you settled: invoke `/mattpocock-skills:tdd` and run red →
green per vertical slice. Red before green proves the test fails without the code. After
each slice, typecheck and run the test file you are in; the full suite runs once, in CI.

**Done when:** the change is complete and its tests go red without it.

## Step 5 — Format and lint

Settle style before committing, so the review spends its attention on substance: run the
formatter and linters of every area you touched, as its guide documents them.

**Done when:** every touched area reports clean.

## Step 6 — Commit by concern

Cut the change into commits with the repository's stacking skill when one is loaded, else
one concern per commit, its tests in the same commit. Link the issue in a commit footer,
in the repository's convention.

When two concerns are independent (each stands alone, no ordering), give the second its
own stack rather than chaining it onto the first:

```bash
$SHIP split --root "$ROOT" --worktree "$WT" --sha <sha> --branch <branch-2>
```

**Done when:** the worktree is clean and every branch/worktree pair is on your list —
review, test and push run once per pair.

## Step 7 — Review

Invoke `/simplify` first, so the review spends its attention on bugs rather than cleanups.
Then run the pre-push review the repository's guide names, else `/code-review medium
--fix`. Both work on the committed branch-vs-base diff and apply their changes to the
working tree. A change you'd rather not keep is reverted first, then proposed as a fork.

Fold what you kept into the commit it belongs to:

```bash
$GREEN fold --worktree "$WT"                # single-commit stack: amends
$GREEN fold --worktree "$WT" --sha <sha>    # multi-commit stack: fixup + autosquash
```

**Done when:** every kept finding sits in the commit it belongs to and the worktree is
clean.

## Step 8 — Test gate

Each commit is green before it becomes a PR. Choosing which tests prove the change is
your judgment; running them, as the area's guide documents, is not. A run that collects
nothing sends you back to write the test. When the review folded code changes, lint again
first.

**Done when:** every worktree is green.

## Step 9 — Push each stack

Independent stacks are independent pushes — once per worktree, with the push tool the
repository's guide names, else `git push`. When the tool has a dry run, run it first: on a
branch with existing PRs, one that would update PRs from unrelated commits is a fork.

Take every PR out of draft with `gh pr ready <number>`: part of CI only fires on an open
PR.

**Done when:** every stack is pushed, every PR is open, and you hold its numbers.

## Step 10 — Land

Invoke `/land` with every PR number.

**Done when:** `/land` has relayed `/green`'s report, adding `Independent stacks: <count>`,
and closed the session, or stopped on a fork.
