---
name: close-session
description: Clean up this session's footprint so the user can close it.
disable-model-invocation: true
---

# Close the session

Clean up this session's **footprint**: what this session created. Everything outside
it, such as other sessions and the user's own work, stays.

Worktree and branch safety lives in `<base directory of this skill>/scripts/close-session.py`;
run it by that full path every time.

`close-session.py check <worktree-path-or-branch>...` prints `✓ safe` or `✗ keep: <reasons>` per
target. Safe means everything in it is already on origin's default branch, squash merges
included. `close-session.py remove` takes the same targets and removes only the safe ones. Branch
names resolve against the current directory; pass `--repository <checkout>` for others.

## Steps

1. **Map the footprint** from the conversation: PRs, worktrees and local branches (any
   repository), background tasks, monitors, crons, dev servers, temp files and clones
   outside the scratchpad, Linear issues. Done when every item is listed with its path,
   repository or ID.
2. **Check worktrees and branches** with `close-session.py check`. Done when each has a verdict.
3. **Ask about every `✗`**: show its reasons and wait for the user's call. When the user
   says it's merged, run `check` again. Done when every `✗` is either `✓` or has the
   user's keep-or-drop call.
4. **Stop background work.** Done when nothing this session started is running.
5. **Remove temp files.** Done when every temp file from step 1 is gone.
6. **Remove worktrees and branches.** The session's own worktree, if entered with
   `EnterWorktree`: `ExitWorktree` first, then `close-session.py remove` its branch.
   Others: `close-session.py remove`. A `✗` the user chose to drop: `git worktree remove
   --force`, then `git branch -D`; its stash entries stay, so report them.
7. **Check PRs and Linear** with `gh pr view` and the issue: an issue whose PRs are all
   merged should be Done. List any that aren't in the report, without moving them.
8. **Report** every footprint item as removed, or kept with its reason, plus follow-ups
   still owed (deploy check, Sentry issue). End with whether the session is safe to
   close.
