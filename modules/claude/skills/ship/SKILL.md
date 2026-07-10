---
name: ship
description: >-
  End-to-end PR shipping workflow, mergify-only. The input is usually a Linear issue
  ID (e.g. MRGFY-1234) — fetched to drive the branch name, commit footer, and context
  — or a free description of the change. Preflight the tooling, create a gitignored
  worktree on a new branch, format/lint, commit by concern, review with /code-review
  max, run affected tests, push the stack, open or update the PRs, then
  report the shipped PRs with their CI status. Run when I invoke /ship,
  say ship it / ship the changes, or ask to worktree + commit + push the stack.
disable-model-invocation: true
argument-hint: "[MRGFY-1234 | description]"
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, Skill, TodoWrite, mcp__linear-server__get_issue
---

# Ship

Take the current changes from working tree to reviewed, pushed PRs — end to end,
using **mergify tooling only**.

## How to run this

This is a multi-step, partly outward-facing workflow — it opens and updates real
PRs. Two habits keep it safe:

- **Track it as a checklist.** Put the steps below on your todo list up front and
  tick them off. A ship often resumes after an interruption (worktree already
  exists); an explicit checklist is what stops a resumed run from skipping the test
  gate.
- **Fail loudly, never paper over.** If any command fails — push rejected, rebase
  conflict, a lint error you can't cleanly fix — stop, show the exact error, and
  ask. Never force-push, never `--no-verify`. A green-looking ship that skipped a
  broken step is the worst outcome.

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

- **mergify only.** Never `git push`. Push and update PRs with `mergify stack push`.
- **Never delete branches via git** (`git branch -D`, `git push --delete`). Let
  mergify/GitHub delete branches after merge. `git worktree remove` (working dir
  only, leaves the branch) is fine for cleanup.
- Never remove or modify a `Change-Id` trailer.
- **Every step after Step 2 runs inside the worktree.** A fresh shell has no memory
  of an earlier `cd`, so pin it explicitly on each call: use `git -C "$WT" …`, and
  `cd "$WT"` before `mergify`/`pnpm` (which have no `-C`). Running a commit or push
  from the source checkout would land it on the wrong branch — the worst failure
  this skill can cause.

## Step 1 — Preflight

Cheaper to fail here than halfway up a stack. Resolve the source checkout root once
and sanity-check the ground before touching anything (default is the Mergify
monorepo):

```bash
ROOT="${ROOT:-$HOME/dev/mergify/monorepo}"
git -C "$ROOT" rev-parse --git-dir           # is it a real checkout? (errors → stop)
command -v mergify >/dev/null || echo "✗ mergify CLI missing — install it before shipping."
```

Then confirm three things and stop early if any is off:

- **Something to ship.** If the source checkout is clean, the target branch doesn't
  exist, and there's no worktree to resume, there's nothing to ship — say so and
  stop rather than opening an empty stack.
- **Interpret the input (`$ARGUMENTS`)** — usually a Linear issue ID, sometimes a
  description, sometimes empty:
  - **Linear issue** — a `MRGFY-1234` (any `ABC-123`) identifier or a
    `linear.app/…/issue/…` URL, including one embedded in a longer sentence. Fetch it
    with the Linear MCP `get_issue` tool (load it via ToolSearch if the Linear tools
    aren't already available). Use the issue to: name the branch `mrgfy-1234-<short-slug>`
    (a few meaningful kebab-case words from the title, not the whole title); carry
    `MRGFY-1234` as the reference footer for Step 5; and frame the work — the
    title/description guide how to split commits and write messages, and the
    `repo:`/`area:` labels hint which area's tooling applies (Steps 4/7).

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
- **Commit-msg hook.** Warn now if it's absent, so commits get their `Change-Id`
  (Step 5 covers the fix); the hook lives on the shared common `.git`:

  ```bash
  HOOK="$(git -C "$ROOT" rev-parse --git-common-dir)/hooks/commit-msg"
  [ -x "$HOOK" ] || echo "⚠ commit-msg hook missing — Change-Ids won't be generated; install it before committing."
  ```

## Step 2 — Worktree

Everything derives from the source checkout root captured in Step 1. Put the
worktree in Claude Code's managed dir, where all worktrees live:

```bash
WT="$ROOT/.claude/worktrees/<branch>"   # <branch> chosen in Step 1
```

Resume an existing ship instead of failing on a second run; otherwise fetch and
create the worktree off fresh `origin/main` (AGENTS.md), so neither a stale local
`main` nor a leftover source-checkout branch bases the stack on old code:

```bash
if [ -d "$WT" ]; then
  cd "$WT"                                   # resume — worktree already exists
else
  # .claude/worktrees/ is Claude Code's managed, already-ignored dir; ensure it's
  # excluded even in a repo not yet set up for it, without touching tracked .gitignore.
  EXCLUDE="$(git -C "$ROOT" rev-parse --git-common-dir)/info/exclude"
  grep -qxF '**/.claude/worktrees/' "$EXCLUDE" || echo '**/.claude/worktrees/' >> "$EXCLUDE"

  if git -C "$ROOT" show-ref --verify --quiet "refs/heads/<branch>"; then
    git -C "$ROOT" worktree add "$WT" <branch>        # reuse an existing branch
  else
    git -C "$ROOT" fetch origin main
    git -C "$ROOT" worktree add "$WT" -b <branch> origin/main
  fi
  cd "$WT"

  # Move uncommitted work from the source checkout into the worktree, if any.
  # Guarded so a clean tree doesn't pop an unrelated stash.
  if ! git -C "$ROOT" diff --quiet || ! git -C "$ROOT" diff --cached --quiet; then
    git -C "$ROOT" stash push -u -m "ship-<branch>" && git stash pop
  fi
fi
```

## Step 3 — Dashboard server (only if the change touches `dashboard/`)

As soon as the worktree exists — before commit/review — start the dev server so I
can follow changes live. `.env.development.local` is gitignored, so copy it from the
source checkout. `dashboard/` is its own pnpm workspace (`start` runs Vite), so run
from there:

```bash
cp "$ROOT/dashboard/.env.development.local" "$WT/dashboard/.env.development.local"
cd "$WT/dashboard" && pnpm start   # background; report the URL
```

## Step 4 — Format & lint (before committing)

Settle style *now*, not after review. A clean, formatted diff means `/code-review`
(Step 6) spends its attention on substance instead of whitespace, and your commits
read right the first time instead of needing a formatting fold later. Adapt to the
area you touched:

- Dashboard: `cd "$WT/dashboard" && pnpm format && pnpm lint` (Biome writes fixes, then oxlint checks).
- Engine: `cd "$WT/engine" && uv run poe linters` — the full pre-commit validation (ruff
  format check, ruff, mypy, vulture…). It only *checks*; apply fixes with
  `uv run pre-commit run -a` (ruff format + `--fix`), then re-run `uv run poe linters`.

Fix anything the tools can't auto-fix before committing.

## Step 5 — Commit by concern

From the worktree, split the changes into logical, independently-deployable commits
— each is a PR in the stack. Concerns with no dependency between them belong in
**separate independent stacks**, not one linear chain (CLAUDE.md coupling rule).
Separate concerns with `git add -p` / path-scoped `git add`.

Commit messages follow CLAUDE.md (Conventional Commits, uppercase, imperative,
WHY-focused, alphabetical footer). When Step 1 resolved a Linear issue, that's the
Linear ref: add `Fixes: MRGFY-1234` on the commit that completes it (closes on merge)
or `References: MRGFY-1234` when the commit only relates to it — choose per the diff,
say which, and keep footers alphabetical (`Change-Id` before `Fixes:`/`References:`).
New commits get their
`Change-Id` from mergify's commit-msg hook (shared across worktrees via the common
`.git`); if Step 1 flagged it missing or `mergify stack push` later warns about a
missing `Change-Id`, install the hook and re-commit, so re-ships match PRs
deterministically.

## Step 6 — Review with /code-review max

Invoke `/code-review max --fix`. It reviews the branch-vs-base **committed** diff
(hence commit first) and applies fixes to the working tree. Fold each fix into the
commit it belongs to; skip this if there are no findings:

- Single commit: `git add -A && git commit --amend --no-edit` (use `-A`, not `-u`,
  so a new file the review adds — e.g. a test — isn't silently dropped).
- Multiple commits: `git commit --fixup=<sha>`, then
  `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash "$(git merge-base HEAD origin/main)"`
  — non-interactive (the no-op editor accepts the autosquash order), scoped to this
  stack, and it preserves every commit's `Change-Id`. If the rebase conflicts, stop
  and surface it — don't guess a resolution.

Apply only high-confidence cleanups and bug fixes. If a finding would add
abstraction, parallelism, or CLI args — or is otherwise risky — do **not** auto-apply:
propose the smallest diff, list what you're not building, and wait for my approval.

## Step 7 — Test gate: affected tests

Each commit must be green before it becomes a PR — that's what "independently
deployable" means (CLAUDE.md). Run the tests relevant to your change, not the whole
suite:

- Dashboard: `cd "$WT/dashboard" && CI=true pnpm test <files>` — `CI=true` runs Vitest
  once instead of parking in watch mode (which would hang).
- Engine: `cd "$WT/engine" && uv run poe test <path>` — scope to the touched path.

If Step 6 folded code changes, re-run format/lint first (cheap) so the fold didn't
reintroduce style drift, then the tests. Fix any failure and re-fold it into the
right commit (Step 6). Don't push red.

## Step 8 — Push the stack (mergify)

```bash
cd "$WT"
mergify stack push --dry-run
```

If the dry run would update PRs from earlier/unrelated commits, ask before
proceeding (skip this check on a brand-new branch with no existing PRs). Then
`mergify stack push` — it opens the PRs (first ship) or updates them (re-ship).
Capture the PR numbers/URLs it prints; you'll need them in the steps that follow. If
the push is rejected, surface the exact error and stop — never fall back to `git push`.

## Step 9 — CI + final report

Don't leave me to hunt for what happened. From Step 8 you have the PR numbers; take
one CI snapshot per PR rather than watching a loop:

```bash
gh pr checks <number>   # per PR; add --watch only if I ask you to wait for green
```

Then post a compact summary so the state is legible at a glance:

```
## Shipped
- PR #<n> — <title> — <url> — <passing | pending | ✗ failing>
- …
Independent stacks: <count>
```

If CI fails, surface the failing job and stop for my direction — don't auto-loop
fixes.
