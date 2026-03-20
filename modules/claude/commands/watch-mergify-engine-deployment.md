# Watch Mergify Engine Deployment

Watch for a merged PR to be deployed to production.

## Workflow

### Step 1: Run the deployment watcher

Run:

```bash
gh watch-mergify-engine-deployment $ARGUMENTS
```

Where `$ARGUMENTS` is the optional PR number provided by the user. If no number is given, omit it entirely — the script defaults to the user's last merged PR.

### Step 2: Report

Relay the script output to the user. If the deployment succeeds, confirm it. If it times out, let the user know.
