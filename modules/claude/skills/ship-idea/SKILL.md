---
name: ship-idea
description: File an untracked idea as a Linear issue, then ship it with /ship-issue.
disable-model-invocation: true
argument-hint: "[the idea, if it isn't already in the conversation]"
allowed-tools: Bash, Skill, ToolSearch, AskUserQuestion, mcp__linear-server__list_issues, mcp__linear-server__list_teams, mcp__linear-server__list_projects, mcp__linear-server__list_issue_labels, mcp__linear-server__list_issue_statuses, mcp__linear-server__save_issue, mcp__linear-server__save_comment
---

# Ship an idea

Work that ships without a Linear issue is **invisible work**: nobody can find it, count
it, or pick it up. This skill makes it visible first, then ships it — file the issue,
then hand it to `/ship-issue`.

## Ground rules (non-negotiable)

- **The idea is mine.** It comes from `$ARGUMENTS` or from what this conversation has
  established.

## Step 1 — Draft the issue

State the idea as it stands: the problem, why it is worth doing, and whatever this
conversation already settled about the shape of the fix. Leave the open questions open
and name them — `/ship-issue` grills those, and pre-guessing them is what makes an issue
stale before the work starts.

**Triage** it: labels from `list_issue_labels`, team and project from `list_teams` and
`list_projects`.

Search with `list_issues` first. If it finds an open match, comment the new context on
it with `save_comment` and skip to Step 3 with its identifier.

File without asking. Stop and show me the draft only when context is clearly missing —
the problem, why it matters, or where it lands can't be settled from the conversation.

**Done when:** the search found no open match, and the text, its triage and project each
come from the conversation — or, where context was missing, from my answer to the draft.

## Step 2 — File it

```
save_issue — title, description, team, project, labels, assignee: me,
             status: In Progress
```

File the draft; resolve the status name with `list_issue_statuses`. It
goes straight to In Progress because Step 3 starts the work now.

**Done when:** you hold the issue identifier, e.g. `ABC-123`, and have shown me its URL.

## Step 3 — Ship it

```
/ship-issue ABC-123
```

`/ship-issue` re-reads the issue from Linear, so the handover is the issue itself — the
idea survives even if this session ends here.

**Done when:** `/ship-issue` has landed its PRs.
