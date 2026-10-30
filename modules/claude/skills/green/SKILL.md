---
name: green
description: >-
  Take a pull request or stack to green: conflict-free, checks passing, review blockers
  cleared. Use when the user wants a PR or stack green or babysat through CI, or when
  /land hands over its PRs.
argument-hint: "[PR numbers; defaults to the stack checked out here]"
allowed-tools: Agent, Bash, Read, Edit, Write, Grep, Glob, Skill, TodoWrite
---

# Green

A pull request or stack → **green**: no conflict, checks passing, nothing a reviewer —
human or bot — is still waiting on.

The mechanical steps live in `scripts/green.py`, bundled next to this file. Below,
`$GREEN` stands for `"<base directory of this skill>/scripts/green.py"` — the skill's
base directory is given when this skill loads. Shell variables don't survive from one Bash
call to the next, so write that path out in every call, and do the same for `$WT`.

The repository's guide (`AGENTS.md`, `CLAUDE.md`) and its skills own the tooling: how to
check out, list and push a stack, and how to read and answer review feedback. Load them;
this skill only sets the order and the rules below.

## Ground rules

- **A fork is mine.** Stop, lay out the options with your recommendation, and wait for my
  answer. Later rules and steps name their forks.
- **Invoking me is the authorization.** Rebase and push without asking, approved PRs
  included.
- **A rebase conflict is yours.** Resolve it with
  `/mattpocock-skills:resolving-merge-conflicts`. Two intents that can't both survive are
  a fork.
- **Answer a fixed thread with `Fixed in <sha>.`, then resolve it**, once the fix is
  pushed. Every other word is mine: a thread or comment that wants more, a finding you'd
  push back on, a changes-requested verdict, or feedback whose intent you can't pin down
  is a fork.
- **Fold, don't append.** A fix goes into the commit that introduced its line, with
  `$GREEN fold --worktree "$WT" [--sha <that commit>]`. Lint what you touched and run the
  test file covering it before pushing.
- **An error these rules make yours you clear; any other is a fork.** Quote it whole.

## Step 1 — Find the stack

`$WT` is the checkout holding the stack: the current directory, or — when `$ARGUMENTS`
names PRs checked out elsewhere — their worktree from `git worktree list`. None holds them:
check them out in the current checkout, unless it has uncommitted work (fork).

The PR numbers are `$ARGUMENTS`, else the stack's PRs as the repository's stack tool lists
them.

**Done when:** you hold `$WT` and every PR number.

## Step 2 — Babysit until green

Invoke the repository's PR-unblocking skill, one whose `scripts/pr-state.py --signal`
prints a `SIGNAL` line per PR; none loaded is a fork. It reads every place feedback can
land, and its decision table is how you work each blocker — where the ground rules above
differ, they win.

```bash
$GREEN wait --worktree "$WT" --pr-state <its base directory>/scripts/pr-state.py --prs <n> [<n> …]
```

Run it with `run_in_background`, then end your turn: the session stays mine to talk in while
it waits, and its exit wakes you. Keep one wait running per worktree. It waits up to eight minutes for checks to settle, then
prints one `SIGNAL` line per PR and `VERDICT: green|work|waiting`.

- **`waiting`** — call it again, unless a PR reads `ci=none` after a full wait or
  `action=unknown` across two waits: a fork.
- **`work`** — clear the blockers of each PR whose line reads `action=fix`, in the
  unblocking skill's order. Rebase only on a conflict. A failing check whose log doesn't
  explain itself goes to a subagent for **diagnosis only** — it reports the root cause and
  the smallest fix, and the log stays out of this session. A **flake** — a failure the
  diff cannot explain — earns one rerun; the second one is yours to fix. The same check
  failing three rounds running is a fork. Then call `wait` again.
- **`green`** — done, unless a line carries `annotations` above 0 with an `anhash` not yet
  on your todo list. Triage them like threads, record the `anhash`, then call `wait`
  again.

Every fork above says what you tried.

**Done when:** `wait` reports `green` with every annotation triaged. Report per PR: its URL,
what you fixed, which findings you left for me and why, and anything else left open.
