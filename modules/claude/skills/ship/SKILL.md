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
- **Commit-msg hook.** Warn now if it's absent, so commits get their `Change-Id`
  (Step 6 covers the fix); the hook lives on the shared common `.git`:

  ```bash
  # --path-format=absolute is load-bearing: the bare form is relative to $ROOT, so it
  # would resolve against whatever directory this shell happens to sit in.
  HOOK="$(git -C "$ROOT" rev-parse --path-format=absolute --git-common-dir)/hooks/commit-msg"
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
  # Keep the sibling worktrees out of $ROOT's status without touching tracked
  # .gitignore. Not already ignored anywhere, and it matters: unexcluded, every other
  # session's worktree reads as untracked work and trips the stash guard below.
  EXCLUDE="$(git -C "$ROOT" rev-parse --path-format=absolute --git-common-dir)/info/exclude"
  grep -qxF '**/.claude/worktrees/' "$EXCLUDE" || echo '**/.claude/worktrees/' >> "$EXCLUDE"

  if git -C "$ROOT" show-ref --verify --quiet "refs/heads/<branch>"; then
    git -C "$ROOT" worktree add "$WT" <branch>        # reuse an existing branch
  else
    git -C "$ROOT" fetch origin main || exit 1   # unguarded, a failed fetch bases the stack on stale code.
    git -C "$ROOT" worktree add "$WT" -b <branch> origin/main
  fi
  cd "$WT"

  # Move uncommitted work from the source checkout into the worktree, if any.
  # Guarded so a clean tree doesn't stash at all. --porcelain is what sees untracked
  # drafts; `git diff` alone reports them as clean and strands them.
  if [ -n "$(git -C "$ROOT" status --porcelain)" ]; then
    git -C "$ROOT" stash push -u -m "ship-<branch>" || exit 1
    # The stash stack is shared across every worktree, so concurrent sessions push onto
    # it too. Pop ours by label: a bare `git stash pop` takes whatever is on top, which
    # is how one session's uncommitted work silently lands on another session's branch.
    REF="$(git -C "$ROOT" stash list --format='%gd %gs' | grep -F 'ship-<branch>' | head -1 | cut -d' ' -f1)"
    [ -n "$REF" ] && git stash pop "$REF"
  fi
fi
```

## Step 3 — Dashboard server (only if the change touches, or will touch, `dashboard/`)

Judge that from the issue's `repo:`/`area:` labels or your Step 4 plan — not from the
diff. On an unimplemented issue there is no diff to read yet, and skipping on that basis
would leave the server down through Step 4, which is exactly when I want to watch it.

Start it as soon as the worktree exists, before commit/review, so I can follow changes
live. `.env.development.local` is gitignored, so copy it from the source checkout;
`dashboard/` is its own pnpm workspace (`start` runs Vite), so run from there:

```bash
ENV="$ROOT/dashboard/.env.development.local"
[ -f "$ENV" ] && cp "$ENV" "$WT/dashboard/.env.development.local"   # absent is fine — say so and carry on.
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
(Step 7) spends its attention on substance instead of whitespace, and your commits
read right the first time instead of needing a formatting fold later. Adapt to the
area you touched:

- Dashboard: `cd "$WT/dashboard" && pnpm format && pnpm lint` (Biome writes fixes, then oxlint checks).
- Engine: `cd "$WT/engine" && uv run poe linters` — the full pre-commit validation (ruff
  format check, ruff, mypy, vulture…). It only *checks*; apply fixes with
  `uv run pre-commit run -a` (ruff format + `--fix`), then re-run `uv run poe linters`.

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
New commits get their
`Change-Id` from mergify's commit-msg hook (shared across worktrees via the common
`.git`); if Step 1 flagged it missing or `mergify stack push` later warns about a
missing `Change-Id`, install the hook and re-commit, so re-ships match PRs
deterministically.

### Independent concerns get their own stack

Chaining unrelated work into one branch couples PRs that needn't be: the second can't
merge until the first does (CLAUDE.md coupling rule). So once the commits exist, give
each concern that doesn't depend on the ones before it its own branch off fresh
`origin/main`:

```bash
WT2="$ROOT/.claude/worktrees/<branch-2>"
git -C "$ROOT" worktree add "$WT2" -b <branch-2> origin/main
git -C "$WT2" cherry-pick <sha> || exit 1   # the message, and its Change-Id, come across
git -C "$WT" rebase --onto <sha>~1 <sha>    # only now safe to drop it from the original
```

Cherry-pick before dropping, never the reverse, and keep the `|| exit 1` — a failed
pick followed by a drop leaves the commit on no branch at all. A conflict here means
the concerns weren't independent after all, and you've learned that having changed
nothing in `$WT`. Say so and leave them in one stack rather than forcing the split.

Track each branch/worktree pair — Step 9 pushes them separately, and Step 10 reports
the count.

## Step 7 — Review with /code-review max

Invoke `/code-review max --fix`. It reviews the branch-vs-base **committed** diff
(hence commit first) and applies fixes to the working tree. It only sees the branch you
are standing on, so run it once per worktree Step 6 left you with. Fold each fix into
the commit it belongs to; skip this if there are no findings:

- Single commit: `git add -A && git commit --amend --no-edit` (use `-A`, not `-u`,
  so a new file the review adds — e.g. a test — isn't silently dropped).
- Multiple commits: `git commit --fixup=<sha>`, then
  `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash "$(git merge-base HEAD origin/main)"`
  — non-interactive (the no-op editor accepts the autosquash order), scoped to this
  stack, and it preserves every commit's `Change-Id`. If the rebase conflicts, stop
  and surface it — don't guess a resolution.

Keep only high-confidence cleanups and bug fixes. By the time you read the findings
`--fix` has already applied all of them, so "don't apply that one" isn't on the menu —
**revert** the hunk instead, then propose it separately: smallest diff, what you're not
building, and wait for my approval. That covers any finding that adds abstraction,
parallelism, or CLI args, or is otherwise risky.

## Step 8 — Test gate: affected tests

Each commit must be green before it becomes a PR — that's what "independently
deployable" means (CLAUDE.md). Run the tests relevant to your change, not the whole
suite:

- Dashboard: `cd "$WT/dashboard" && CI=true pnpm test <files>` — `CI=true` runs Vitest
  once instead of parking in watch mode (which would hang).
- Engine: `cd "$WT/engine" && uv run poe test <path>` — scope to the touched path.

A run that collects nothing is a red flag, not a pass. If the change added behavior and
no test exercises it, the gate didn't hold — go back to Step 4 and write the test.

Gate every worktree Step 6 left you with, not just `$WT`. A stack split off precisely
because it stands alone is the last one that should reach a PR untested.

If Step 7 folded code changes, re-run format/lint first (cheap) so the fold didn't
reintroduce style drift, then the tests. Fix any failure and re-fold it into the
right commit (Step 7). Don't push red.

## Step 9 — Push each stack (mergify)

Independent stacks are independent pushes — there's no combined command. Run this once
per worktree Step 6 left you with, from inside that worktree:

```bash
cd "$WT"                 # then again from "$WT2", … — one push per stack
mergify stack push --dry-run
```

If a dry run would update PRs from earlier/unrelated commits, ask before proceeding
(skip this check on a brand-new branch with no existing PRs). Then `mergify stack push`
— it opens the PRs (first ship) or updates them (re-ship). Capture the PR numbers/URLs
each push prints; you'll need them in the steps that follow. If a push is rejected,
surface the exact error and stop — never fall back to `git push`.

## Step 10 — CI + final report

Don't leave me to hunt for what happened. From Step 9 you have the PR numbers; take
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
