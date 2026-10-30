---
name: land
description: >-
  Land pull requests: keep them green until they merge, then close the session. Use when
  the user wants a PR seen through to merge, or /ship-issue hands over its pushed PRs.
argument-hint: "[PR numbers; defaults to the stack checked out here]"
allowed-tools: Bash, Read, Skill, ToolSearch
---

# Land

Pushed PRs → **landed**: merged, with this session's footprint cleaned up and the session
archived. The merge is mine or the merge queue's; you keep the PRs green while they wait,
then close up.

`$GREEN` stands for `"<base directory of this skill>/../green/scripts/green.py"`, the
`/green` skill's script. Shell variables don't survive from one Bash call to the next, so
write that path out in every call.

## Ground rules

- **A fork is mine.** Stop, lay out the options with your recommendation, and wait for my
  answer. Later steps name their forks.

## Step 1 — Green

The PRs are `$ARGUMENTS`, else the stack checked out here. Group them by worktree with
`git worktree list`: independent stacks sit in separate worktrees. Invoke `/green` once per
worktree with that worktree's PR numbers.

**Done when:** `/green` reports green for every worktree, you have relayed each report, and
you hold each worktree's path and the pr-state script `/green` waited with.

## Step 2 — Watch for the merge

Start one watch per worktree, each with `run_in_background`, then end your turn: the
session stays mine to talk in, and a watch costs nothing until it exits and wakes you.

```bash
$GREEN watch --worktree <worktree> --pr-state <pr-state script> --prs <n> [<n> …]
```

It polls every five minutes and returns at the first verdict, or after a day, printing each
PR's `SIGNAL` line and `VERDICT: merged|closed|moved|open`.

- **`merged`** — that worktree is landed.
- **`closed`** — the `CLOSED:` line names PRs closed without merging: a fork. I may have
  abandoned or superseded them.
- **`moved`** — a new commit, action or feedback: Step 1 for that worktree, then watch it
  again.
- **`open`** — a day passed with nothing new: watch it again.

**Done when:** every worktree's watch reported `merged`.

## Step 3 — Close

Invoke `/close-session`.

**Done when:** it has archived this session, or stopped on an item it asks me about.
