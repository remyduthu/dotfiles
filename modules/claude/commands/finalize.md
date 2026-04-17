# Finalize

Prepare the current branch for review: self-review, format, lint, then push as draft PRs.

## Workflow

### Step 1: Self-review with /simplify

Invoke `/simplify` to review the changes for code quality, reuse, and efficiency. Apply any fixes, then amend the relevant commit:

```bash
git add -u
git commit --amend --no-edit
```

### Step 2: Format and lint

Run the project's formatter and linter on the full working tree. Adapt to the project:

- Python: `poe format && poe linters --fix`
- Frontend: `pnpm format && pnpm lint`

If any files changed, amend the last commit:

```bash
git add -u
git commit --amend --no-edit
```

### Step 3: Review commit messages

For each commit, verify the message follows the rules in CLAUDE.md (Git section). Preserve any existing `Change-Id` trailer. If no Linear issue is clearly associated, omit the `Fixes:` trailer.

If a message needs fixing, amend it with `git commit --amend`.

### Step 4: Dry-run the stack push

```bash
mergify stack push --dry-run
```

If the output shows updates to PRs from previous commits (not part of the current work), ask the user for confirmation before proceeding. Skip this check on new branches with no existing PRs.

### Step 5: Push the stack

```bash
mergify stack push
```

### Step 6: Self-review with /code-review

`/code-review` requires a live PR, which is why it runs after pushing.

For each PR created by the stack push, invoke `/code-review`. Collect all valid fixes, amend the relevant commits, then push once:

```bash
git add -u
git commit --amend --no-edit
mergify stack push
```

## Rules

- NEVER remove or modify the `Change-Id` in commit messages.
- ALWAYS use `mergify stack push` to push, never `git push`.
- If `/simplify` or `/code-review` find no issues, skip the amend step.
- If a self-review fix is ambiguous or risky, ask the user before applying.
