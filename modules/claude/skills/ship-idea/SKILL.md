---
name: ship-idea
description: >-
  Ship an untracked idea, chore, or fix by filing its Linear issue first. Use when the
  user wants something from this conversation tracked and shipped rather than done
  invisibly.
argument-hint: "[the idea, if it isn't already in the conversation]"
allowed-tools: Bash, Skill, ToolSearch, AskUserQuestion, mcp__linear-server__list_teams, mcp__linear-server__list_projects, mcp__linear-server__list_issue_labels, mcp__linear-server__list_issue_statuses, mcp__linear-server__save_issue
---

# Ship an idea

Work that ships without a Linear issue is **invisible work**: nobody can find it, count
it, or pick it up. This skill makes it visible first, then ships it — file the issue,
then hand it to `/ship-issue`.

## Ground rules (non-negotiable)

- **The idea is mine.** It comes from `$ARGUMENTS` or from what this conversation has
  established.
- **I approve the issue before it is filed.** One round-trip, and the tracker stays
  worth reading.

## Step 1 — Draft the issue

State the idea as it stands: the problem, why it is worth doing, and whatever this
conversation already settled about the shape of the fix. Leave the open questions open
and name them — `/ship-issue` grills those, and pre-guessing them is what makes an issue
stale before the work starts.

**Triage** it as well, so it sorts and plans like everything else in the backlog:

- **Priority** — Urgent and High are for something already hurting production or a
  customer, Low for a chore nobody is waiting on, Medium otherwise.
- **Estimate** — size the smallest useful slice, since that is all `/ship-issue`
  builds. An estimate past the low end of the scale means the idea holds more than one
  issue: say so in the draft.
- **Labels** — one from each group that applies (`kind:`, `type:`, `area:`, `repo:`),
  taken from `list_issue_labels` rather than invented. `/ship-issue` reads them
  to decide whether to start the dashboard server, so the `repo:` one is load-bearing
  rather than decoration.

Show me the draft, plus the team and project you will file it under — where either is
ambiguous, resolve it here (`list_teams`, `list_projects`). Then wait.

**Done when:** I have approved the text, its triage, and the team and project it lands
in.

## Step 2 — File it

```
save_issue — title, description, team, project, priority, estimate, labels,
             status: In Progress
```

File exactly what I approved; resolve the status name with `list_issue_statuses`. It
goes straight to In Progress because Step 3 starts the work now.

**Done when:** you hold the issue identifier, e.g. `MRGFY-1234`.

## Step 3 — Ship it

```
/ship-issue MRGFY-1234
```

Its Step 1 re-reads the issue from Linear, so the handover is the issue itself — the
idea survives even if this session ends here.

**Done when:** `/ship-issue` has reported its PRs.
