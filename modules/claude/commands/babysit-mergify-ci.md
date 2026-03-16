# Babysit CI

Monitor CI status on the current branch's PR and automatically fix failures.

Designed to be used with `/loop` (e.g., `/loop 3m /babysit-ci`).

## Workflow

### Step 1: Get CI status

Run:

```bash
gh pr checks --json name,state,bucket,link --jq '.[] | select(.bucket == "fail")' 2>&1
```

If no failures are found, report that CI is green and stop.
If checks are still pending, report and stop (the next loop iteration will re-check).

### Step 2: For each failed check, fetch logs

For each failed check, extract the run ID and job name from the `link` field, then fetch the failed logs:

```bash
gh run view <run-id> --log-failed 2>&1
```

If the output is too large, focus on the last 200 lines per job, which usually contain the actual errors.

### Step 3: Diagnose and fix

Read the failure logs carefully. Common failure types:

- **Lint failures**: Read the failing file(s), apply the fix (formatting, type errors, import order, etc.).
- **Test failures**: Read both the test file and the production code under test. Determine if the fix belongs in the test or the production code. Fix accordingly.
- **Build/type-check failures**: Read the relevant source files and fix type errors, missing imports, etc.
- **Any other CI failure**: Read the logs, understand the root cause, and fix it.

### Step 4: Amend the commit and push

After fixing, amend the current commit while **preserving the entire commit message including the Change-Id trailer**:

```bash
git add -u
git commit --amend --no-edit
```

CRITICAL: The `Change-Id:` line in the commit message MUST be preserved. Using `--no-edit` ensures this. If you need to verify, run `git log -1` after amending to confirm the Change-Id is still present.

Then push:

```bash
mergify stack push
```

### Step 5: Report

Summarize what was fixed and what was pushed. If you could not fix a failure, explain why.

## Rules

- NEVER remove or modify the `Change-Id` in commit messages.
- ALWAYS use `mergify stack push` to push, never `git push`.
- ALWAYS use `git add -u` before amending (do not stage untracked files unless you created them intentionally).
- If you created new files, stage them explicitly by name.
- If a failure is not actionable (e.g., flaky infra, external service timeout), skip it and report it.
- Do NOT retry the same fix if it already failed once — escalate to the user instead.
