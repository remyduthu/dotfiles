---
name: ship
description: >-
  End-to-end feature shipping workflow, mergify-only. The input is usually a Linear issue
  ID (e.g. MRGFY-1234) — fetched to drive the branch name, commit footer, and context
  — or a free description of the change. Preflight the tooling, create a gitignored
  worktree on a new branch, implement the change with its tests if it isn't written yet,
  start the dashboard server, format/lint, commit by concern, review with /code-review
  max, run affected tests, push each stack, open or update the PRs, then report them
  with their CI status. Works from an unimplemented issue as well as from a dirty tree.
  Invoke explicitly with /ship — it never runs on its own, because it pushes real PRs.
disable-model-invocation: true
argument-hint: "[MRGFY-1234 | description]"
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, Skill, TodoWrite, ToolSearch, mcp__linear-server__get_issue
---

# Ship

Take a change from wherever it currently is — an unimplemented Linear issue, a rough
draft, a dirty working tree — to reviewed, pushed PRs, end to end, using **mergify
tooling only**.

The mechanical steps live in `scripts/ship.py` (stdlib-only Python), bundled next to
this file. Define once and reuse throughout — the skill's base directory is given when
this skill loads:

```bash
SHIP='python3 "<base directory of this skill>/scripts/ship.py"'
```

Every subcommand echoes the git commands it runs, exits nonzero on the first failure,
and prints exactly what went wrong and what state it left behind. Your judgment stays
on: what to implement, how to split commits, which tests prove the change, and when to
stop and ask.

## How to run this

This is a multi-step, partly outward-facing workflow — it opens and updates real
PRs. Two habits keep it safe:

- **Track it as a checklist.** Put the steps below on your todo list up front and
  tick them off. A ship often resumes after an interruption (worktree already
  exists); an explicit checklist is what stops a resumed run from skipping the test
  gate.
- **Fail loudly, never paper over.** When a `$SHIP` subcommand (or anything else)
  fails, stop, show its exact error, and ask. Never force-push, never `--no-verify`,
  never re-implement a failing subcommand's job with raw git to get past it. A
  green-looking ship that skipped a broken step is the worst outcome.

## Working principles (apply throughout)

- Stay pragmatic. Don't try to be smart. Keep it simple.
- Propose the smallest possible fix first, as a diff. List what you are
  intentionally **not** building. Wait for my approval before adding any
  parallelism, sharding, CLI args, or new abstraction layer.
- Never assume on decisions that matter. When the approach, a trade-off, or a stale
  or incomplete plan leaves a real choice open, stop and ask — lay out the options
  with your recommendation and let me pick. Silent guesses at a fork are the most
  expensive mistakes.
- One commit = one PR = independently deployable (see CLAUDE.md, Git section).

## Ground rules (non-negotiable)

- **mergify only.** Never `git push`. Push and update PRs with `$SHIP push`.
- **Never delete branches via git** (`git branch -D`, `git push --delete`). Let
  mergify/GitHub delete branches after merge. `git worktree remove` (working dir
  only, leaves the branch) is fine for cleanup.
- Never remove or modify a `Change-Id` trailer.
- **Every step after Step 2 runs inside the worktree.** The `$SHIP` subcommands take
  `--worktree` and pin it for you; for anything you run by hand, use `git -C "$WT" …`
  and `cd "$WT"` before `mergify`/`pnpm`. Running a commit or push from the source
  checkout would land it on the wrong branch — the worst failure this skill can cause.

## Step 1 — Preflight

Cheaper to fail here than halfway up a stack.

```bash
$SHIP preflight                  # default --root is ~/dev/mergify/monorepo
```

It verifies the checkout, the mergify CLI (hard failures), and the commit-msg hook
(warning — Step 6 covers the fix). Then confirm two things yourself and stop early if
either is off:

- **Something to ship.** A clean checkout is *not* "nothing to ship". If the input
  names a Linear issue or describes a change, the code simply isn't written yet — that's
  Step 4's job, so carry on. Shipping an unimplemented issue is a normal run, not an
  error. Stop only when there is genuinely nothing to find: no input, a clean checkout
  (untracked drafts count as work), no target branch, and no worktree to resume. Say so
  then, rather than opening an empty stack.
- **Interpret the input (`$ARGUMENTS`)** — usually a Linear issue ID, sometimes a
  description, sometimes empty:
  - **Linear issue** — a `MRGFY-1234` (any `ABC-123`) identifier or a
    `linear.app/…/issue/…` URL, including one embedded in a longer sentence. Fetch it
    with the Linear MCP `get_issue` tool (load it via ToolSearch if the Linear tools
    aren't already available). Use the issue to: name the branch `mrgfy-1234-<short-slug>`
    (a few meaningful kebab-case words from the title, not the whole title); carry
    `MRGFY-1234` as the reference footer for Step 6; and frame the work — the
    title/description guide how to split commits and write messages, and the
    `repo:`/`area:` labels hint which area's tooling applies (Steps 5/8).

    **Challenge the plan — don't inherit it.** A Linear issue is written before the work
    is understood and drifts as reality lands, so its proposed steps are often stale,
    partial, or wrong by the time you ship. Read it for *intent*, then judge the best
    implementation against the code as it is now — not against the plan's word. Where the
    plan and the code disagree, or the plan leaves a real decision open or half-specified,
    stop and ask: surface the options with your recommendation and let me choose. Assuming
    your way past a fork the issue got wrong is how a ship ships the wrong thing.

    If Linear is unreachable, fall back to branch `mrgfy-1234` and a `References: MRGFY-1234`
    footer, and say so — a fetch hiccup shouldn't block the ship.
  - **Description** — derive a short kebab-case branch from it; no Linear footer unless
    the text itself names an issue.
  - **Empty** — derive a short kebab-case branch from the change itself.

  Carry the result as `<branch>` through the rest.

## Step 2 — Worktree

```bash
$SHIP worktree --branch <branch>     # <branch> chosen in Step 1
WT="$ROOT/.claude/worktrees/<branch>"
```

One call does the whole dance: resumes an existing ship instead of failing on a second
run; otherwise excludes the worktrees dir from the checkout's status, fetches and
creates the worktree off fresh `origin/main` (or reuses an existing local branch),
migrates any uncommitted work from the source checkout via a labeled stash (safe
against concurrent sessions), and copies the gitignored dashboard env file. If it
reports a stash-pop conflict, the work is still in the stash it names — resolve by
hand, never drop it.

## Step 3 — Dashboard server (only if the change touches, or will touch, `dashboard/`)

Judge that from the issue's `repo:`/`area:` labels or your Step 4 plan — not from the
diff. On an unimplemented issue there is no diff to read yet, and skipping on that basis
would leave the server down through Step 4, which is exactly when I want to watch it.

Start it as soon as the worktree exists, before commit/review, so I can follow changes
live (`dashboard/` is its own pnpm workspace; `start` runs Vite):

```bash
cd "$WT/dashboard" && pnpm start   # background; report the URL
```

## Step 4 — Implement (only if the change isn't written yet)

Skip this only when the tree already holds the **complete** change. A rough draft
cleared Step 1's "something to ship" check without being finished — finish it here,
rather than reading its presence as "already implemented" and shipping it half-built.

The worktree is where the code gets *written*, not just where it gets carried. Read the
code first, then judge the implementation against the code as it stands now — Step 1's
"challenge the plan" applies here too: where the issue and the code disagree, or a real
decision is still open, stop and ask with your recommendation instead of assuming past
it.

Build the smallest useful slice first and say what you're intentionally **not**
building (working principles above). Anything past that slice — parallelism, CLI args, a
new abstraction — waits for my approval.

**New behavior ships with its tests.** They're part of the smallest useful slice, not an
addition to it, and they go in the same commit as the code they cover — a commit whose
tests live in a different PR isn't independently deployable (CLAUDE.md). Step 8 can only
run what you write here; it has no way to fail a test that was never written.

## Step 5 — Format & lint (before committing)

Settle style *now*, not after review. A clean, formatted diff means `/code-review`
(Step 7) spends its attention on substance instead of whitespace. Run once per area you
touched:

```bash
$SHIP lint --worktree "$WT" --area dashboard   # Biome writes fixes, then oxlint checks
$SHIP lint --worktree "$WT" --area engine      # pre-commit applies fixes, then poe linters gates
```

Fix anything the tools can't auto-fix before committing.

## Step 6 — Commit by concern

From the worktree, split the changes into logical, independently-deployable commits
— each is a PR in the stack. Separate concerns with `git add -p` / path-scoped `git add`.
Commit every concern here first, whatever shape the stacks end up taking: that's what
earns each one its `Change-Id` and gets it somewhere recoverable.

Commit messages follow CLAUDE.md (Conventional Commits, uppercase, imperative,
WHY-focused, alphabetical footer). When Step 1 resolved a Linear issue, that's the
Linear ref: add `Fixes: MRGFY-1234` on the commit that completes it (closes on merge)
or `References: MRGFY-1234` when the commit only relates to it — choose per the diff,
say which, and keep footers alphabetical (`Change-Id` before `Fixes:`/`References:`).
New commits get their `Change-Id` from mergify's commit-msg hook (shared across
worktrees via the common `.git`); if Step 1 flagged it missing or a push later warns
about a missing `Change-Id`, install the hook and re-commit, so re-ships match PRs
deterministically.

### Independent concerns get their own stack

Chaining unrelated work into one branch couples PRs that needn't be: the second can't
merge until the first does (CLAUDE.md coupling rule). Whether two concerns are
independent is your call; moving one is not:

```bash
$SHIP split --worktree "$WT" --sha <sha> --branch <branch-2>
```

It cherry-picks the commit onto a new stack off `origin/main` (the message, and its
`Change-Id`, come across), then — only after a clean pick — drops it from the original
via `rebase --onto`. A cherry-pick conflict means the concerns weren't independent
after all, and you've learned that with the original stack unchanged: say so and keep
one stack rather than forcing the split.

Track each branch/worktree pair — Step 9 pushes them separately, and Step 10 reports
the count.

## Step 7 — Review with /code-review max

Invoke `/code-review max --fix`. It reviews the branch-vs-base **committed** diff
(hence commit first) and applies fixes to the working tree. It only sees the branch you
are standing on, so run it once per worktree Step 6 left you with.

Keep only high-confidence cleanups and bug fixes. By the time you read the findings
`--fix` has already applied all of them, so "don't apply that one" isn't on the menu —
**revert** the hunk instead, then propose it separately: smallest diff, what you're not
building, and wait for my approval. That covers any finding that adds abstraction,
parallelism, or CLI args, or is otherwise risky.

Then fold what you kept into the commit it belongs to:

```bash
$SHIP fold --worktree "$WT"                # single-commit stack: amends
$SHIP fold --worktree "$WT" --sha <sha>    # multi-commit stack: fixup + autosquash
```

Both preserve every commit's `Change-Id`. If the autosquash rebase conflicts, the
subcommand stops and says so — surface it, don't guess a resolution.

## Step 8 — Test gate: affected tests

Each commit must be green before it becomes a PR — that's what "independently
deployable" means (CLAUDE.md). Choosing which tests prove the change is your judgment;
running them is not:

```bash
$SHIP test --worktree "$WT" --area dashboard --paths <files>   # Vitest, once (no watch mode)
$SHIP test --worktree "$WT" --area engine --paths <path>       # poe test, scoped to the touched path
```

A run that collects nothing fails — that's deliberate. If the change added behavior and
no test exercises it, the gate didn't hold: go back to Step 4 and write the test.

Gate every worktree Step 6 left you with, not just `$WT`. A stack split off precisely
because it stands alone is the last one that should reach a PR untested.

If Step 7 folded code changes, re-run Step 5 first (cheap) so the fold didn't
reintroduce style drift, then the tests. Fix any failure and re-fold it into the
right commit (Step 7). Don't push red.

## Step 9 — Push each stack (mergify)

Independent stacks are independent pushes — there's no combined command. Run this once
per worktree Step 6 left you with:

```bash
$SHIP push --worktree "$WT" --dry-run
```

If a dry run would update PRs from earlier/unrelated commits, ask before proceeding
(skip this check on a brand-new branch with no existing PRs). Then
`$SHIP push --worktree "$WT"` — it opens the PRs (first ship) or updates them
(re-ship), and prints each PR URL it finds; you'll need them in Step 10. If a push is
rejected, surface the exact error and stop — never fall back to `git push`.

## Step 10 — CI + final report

Don't leave me to hunt for what happened. From Step 9 you have the PR numbers; take
one CI snapshot per PR rather than watching a loop:

```bash
$SHIP report --worktree "$WT" --prs <n> [<n> …]
```

It prints the `## Shipped` summary (one line per PR: title, URL, passing/pending/
failing) and the failing check names if any. Relay it, add
`Independent stacks: <count>`, and if CI fails, stop for my direction — don't
auto-loop fixes.
