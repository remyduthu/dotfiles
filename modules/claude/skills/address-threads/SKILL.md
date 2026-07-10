---
name: address-threads
description: >-
  Work a pull request's review feedback end to end: read every unresolved review
  thread, implement the code change it asks for, fold that change into the right
  stack commit, push with mergify, then resolve the threads you addressed. Stops to
  ask on any feedback that isn't a clear mechanical fix — a question, a judgment
  call, or a comment you'd push back on. Run when I invoke /address-threads,
  optionally with a PR number or URL; with no argument it targets the current
  branch's PR.
disable-model-invocation: true
argument-hint: "[pr-number-or-url]"
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, TodoWrite
---

# Address review threads

Turn a PR's review comments into actual changes: read each unresolved thread, make
the change it asks for, push it, and resolve the thread. This skill **acts on the
code** — resolving is only the last step, never a substitute for the fix.

## How to run this

Outward-facing and hard to undo — it pushes to a real PR and resolves real threads.
Three habits keep it safe:

- **Checklist it.** Put the threads on your todo list up front, one item each, and
  tick them off — so a run interrupted mid-review resumes without dropping or
  double-fixing a thread.
- **Code first, resolve last.** A thread is resolved only after its fix is committed
  and pushed. Resolving a thread you haven't addressed hides a real request — that is
  the one thing this skill must never do.
- **Stop at every fork.** Only clear, mechanical fixes are yours to make alone. A
  question, a judgment call, a comment you think is wrong, or anything whose intent
  you're unsure of — stop and ask before touching code or the thread. Silent guesses
  at a reviewer's meaning are the expensive mistake here.

## Ground rules (non-negotiable)

- **mergify only.** Never `git push`; update the PR with `mergify stack push`.
- Never remove or modify a `Change-Id` trailer.
- Never resolve a thread whose feedback you didn't address, and never reply on a
  reviewer's behalf — surface anything that needs words, not code, to me.

## Step 1 — Locate the PR and its branch

The target comes from `$ARGUMENTS` — a PR number or URL, or empty for the current
branch's PR. You need that branch checked out to edit its code, so confirm you're on
it and stop if not:

```bash
gh pr view $ARGUMENTS --json number,headRefName,url
```

Compare `headRefName` to `git branch --show-current`. If they differ, stop and tell
me — I'll check out the branch (or its ship worktree) first. Editing the wrong
checkout is the worst failure this skill can cause.

## Step 2 — List the unresolved threads

```bash
"$HOME/.claude/skills/address-threads/scripts/list-threads.sh" $ARGUMENTS
```

It prints one JSON object per unresolved thread: `id`, `path`, `line`,
`originalLine`, `isOutdated`, and the `comments` (author + body). Put each thread on
your todo list. An empty array means nothing to address — say so and stop.

## Step 3 — Triage each thread

Read each comment against the code at `path:line` and sort it into one of two
buckets:

- **Clear mechanical fix** — the change is unambiguous (rename, guard a nil, fix a
  typo, tighten a type, delete dead code). Make it (Step 4).
- **Everything else** — a question, a design opinion, a trade-off, a comment you'd
  push back on, or feedback whose intent you're not sure of. **Stop and ask me**
  before doing anything: lay out the thread, your read of it, and your recommended
  response, then let me decide. Some of these want a reply rather than a code change
  — that reply is mine to write, not yours to post.

An `isOutdated` thread points at code that has since moved or gone, so its `line` may
be null. Locate the current code by content (Grep); if the feedback no longer
applies, treat it as "everything else" and ask.

## Step 4 — Implement the clear fixes

Make each approved change with the smallest edit that satisfies the comment. Don't
gold-plate — a review nit is not a license to refactor the surrounding code. Keep
each change traceable to its thread so Step 5 can fold it into the right commit.

## Step 5 — Fold each fix into its commit

Every commit in the stack is a PR that must stay independently deployable, so a fix
belongs in the commit that introduced the line it touches — not a trailing "address
review" commit. Find the owning commit and fold in, preserving every `Change-Id`:

- Which commit owns the line: `git blame` it, or `git log -S '<snippet>' origin/main..HEAD`.
- Single-commit stack: `git add -A && git commit --amend --no-edit`.
- Multi-commit: `git commit --fixup=<sha>` per fix, then
  `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash "$(git merge-base HEAD origin/main)"`
  — non-interactive, scoped to this stack, and it preserves Change-Ids. If the rebase
  conflicts, stop and surface it — don't guess a resolution.

## Step 6 — Push (mergify)

If no fixes landed (every thread was deferred to me), skip this step. Otherwise:

```bash
mergify stack push --dry-run
```

If the dry run would touch PRs you didn't mean to, stop and ask. Then
`mergify stack push` to update the PR(s). If the push is rejected, surface the exact
error and stop — never fall back to `git push`, never force-push.

## Step 7 — Resolve the threads you addressed

Only now, and only the threads whose fix you just pushed. Echo each one before
resolving so the mapping is on the record, then resolve it by id:

```bash
"$HOME/.claude/skills/address-threads/scripts/resolve-thread.sh" <thread-id>
```

Leave untouched every thread you didn't address — including the "everything else"
ones still waiting on my decision or a reply.

## Step 8 — Report

Post a compact summary so the state is legible at a glance:

```
## Review addressed — PR #<n>
Fixed & resolved:
- <path:line> — <what the comment asked> → folded into <commit>
Needs you:
- <path:line> — <the question / judgment call / reply to write>
Pushed: <mergify stack push result, or "nothing to push">
```
