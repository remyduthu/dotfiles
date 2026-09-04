---
name: ship-issues
description: Ship a list of Linear issues in parallel, one background session each.
disable-model-invocation: true
argument-hint: "MRGFY-1234 [MRGFY-5678 …]"
allowed-tools: Bash, AskUserQuestion, ToolSearch, mcp__linear-server__get_issue
---

# Ship issues

Fan a list of Linear issues out into one background `/ship-issue` per issue. This skill
**launches** and stops; the shipping, and every judgment call in it, belongs to each
spawned session.

## Ground rules (non-negotiable)

- **Ship only the issues you name; add no others.** With none, say so and stop. Each
  extra one spawns a session that opens a PR nobody asked for.
- **One session per issue**, each owning one branch and one stack.
- **Launch and stop.** The spawned sessions are mine to drive.

## Step 1 — Name each session

Fetch each issue with the Linear MCP `get_issue` tool (load it via ToolSearch if the
Linear tools aren't available yet) and build `<ID> — <TITLE>`, em dash included. It
becomes the session name, so `claude agents` reads at a glance.

If Linear is unreachable, stop and tell me — every session would halt at its own Step 1.

**Done when:** every ID is named and every fetch succeeded.

## Step 2 — Ask which repository

Every batch ships into one checkout, and it is mine to choose — ask, whatever the
current directory happens to be:

```bash
ls -d ~/dev/mergify/*/
```

Offer those as the options and wait for my answer.

**Done when:** I have named the repository root.

## Step 3 — Spawn

Spawn each issue by running the script once:

```bash
$SHIP_ISSUES --repository <the root I chose> "MRGFY-1234 — Fix the thing" "MRGFY-5678 — Fix the other thing"
```

If a spawn fails, retry the failed issues only; stop if any fails twice. A repository
never opened in Claude Code before stops at the workspace-trust prompt on its first turn,
with nothing in the transcript to explain the silence. Say so if the sessions sit idle.

**Done when:** every issue spawned without error and all session IDs are visible.

## Step 4 — Report

Relay what it printed, then how to follow the batch:

```
Spawned <n> sessions in <repository>:
- <id>  <ID> — <TITLE>
Follow with `claude agents`; `claude attach <id>` answers one that shows `blocked`.
```

`/ship-issue` stops at every **fork** it was built to stop at, so `blocked` sessions are
the design working.

**Done when:** every spawned session appears in the summary with its id.
