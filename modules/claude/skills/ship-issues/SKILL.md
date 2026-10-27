---
name: ship-issues
description: Ship a list of Linear issues in parallel, one background session each.
disable-model-invocation: true
argument-hint: "ABC-123 [ABC-456 …]"
allowed-tools: Bash, AskUserQuestion, ToolSearch, mcp__linear-server__get_issue
---

# Ship issues

Fan a list of Linear issues out into one background `/ship-issue` per issue. This skill
**launches** and stops; the shipping, and every judgment call in it, belongs to each
spawned session.

Spawning lives in `scripts/ship-issues.py`, bundled next to this file. Below,
`$SHIP_ISSUES` stands for `"<base directory of this skill>/scripts/ship-issues.py"` — the
skill's base directory is given when this skill loads; write that path out in the call.

## Ground rules (non-negotiable)

- **Ship only the issues you name; add no others.** With none, say so and stop. Each
  extra one spawns a session that opens a PR nobody asked for.
- **One session per issue**; it may open several stacks.

## Step 1 — Name each session

Fetch each issue with the Linear MCP `get_issue` tool (load it via ToolSearch if the
Linear tools aren't available yet) and build `<ID> — <TITLE>`, em dash included. It
becomes the session name, so `claude agents` reads at a glance. Keep each issue's `repo:`
label too — the next step settles the checkout from it.

If Linear is unreachable, stop and tell me — every session would halt at its own fetch.

**Done when:** every ID is named and every fetch succeeded.

## Step 2 — Settle the repository

Every batch ships into one checkout, and the issues usually name it: a `repo:` label means
`~/dev/mergify/<its value>`.

```bash
ls -d ~/dev/mergify/*/
```

Propose the checkout the labels agree on and let me confirm it. Labels that disagree, a
missing `repo:`, or a directory that isn't there is a **fork** — offer what `ls` found and
wait for my answer.

**Done when:** I have confirmed the repository root.

## Step 3 — Spawn

Spawn each issue by running the script once:

```bash
$SHIP_ISSUES --repository <the root I chose> "ABC-123 — Fix the thing" "ABC-456 — Fix the other thing"
```

If a spawn fails, re-run with that issue and every one after it; stop if the same issue
fails twice. A repository never opened in Claude Code before stops at the workspace-trust
prompt on its first turn, with nothing in the transcript to explain the silence. Say so
if the sessions sit idle.

**Done when:** the script exits 0 and each issue has a session ID from its output.

## Step 4 — Report

Relay what it printed, then how to follow the batch:

```
Spawned <n> sessions in <repository>:
- <id>  <ID> — <TITLE>
Follow with `claude agents`; `claude attach <id>` answers one that shows `blocked`.
```

A session working quietly for hours is the normal state rather than a hang. `blocked`
means a **fork**; attach and answer it. A session idle from its first turn is stuck at
workspace trust. Each session runs until its PRs are green.

**Done when:** every spawned session appears in the summary with its id.
