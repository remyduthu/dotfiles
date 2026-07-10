## General

- Be extremely concise — sacrifice grammar for concision.
- Avoid abbreviations in code — prefer full words (e.g. `documentation` over `doc`, `repository` over `repo`).
- Readability is correctness — unclear code is a bug, not a style issue.
- Never over-engineer — no speculative abstractions, no "just in case" code.
- Prefer minimal fixes — start with the simplest code/SQL change; don't add parallelism, sharding, CLI args, or extra abstraction layers unless explicitly asked.
- Don't retroactively edit existing comments or code style unless asked.

## Five Non-Negotiables

<!-- https://addyosmani.com/blog/agent-skills/#:~:text=Five%20non%2Dnegotiables%2C%20lifted,you%E2%80%99re%20asked%20to%20touch. -->

1. Surface assumptions before building. Wrong assumptions held silently are the most common failure mode.
2. Stop and ask when requirements conflict. Don’t guess.
3. Push back when warranted. You're not a yes-machine.
4. Prefer the boring, obvious solution. Cleverness is expensive.
5. Touch only what you’re asked to touch.

## Comments And Documentation

- Do not leak implementation details.
- End all comments with a dot.
- Explain WHAT and WHY, not HOW.

## Git

- When using stacks, each commit is a PR. Every commit must be independently deployable.
- Reduce coupling as much as possible by using independent branches when using stacks (`mergify stack`).
- Push stacks with `mergify stack push`.

## Commit messages

- Use Conventional Commits starting with an uppercase (e.g. `feat(ci-insights): Add...`).
- Commit messages must complete "If applied, this commit will..." — use imperative verbs.
- Focus on WHY the change is needed; the WHAT should be self-evident from the diff.
- Back perf and behavior claims with concrete numbers (e.g. before/after).
- Add references to Linear issues at the end of the message (e.g. `Fixes: MRGFY-XXXX` or `References: `MRGFY-XXXX`) when relevant.
- Order footer attributes alphabetically (e.g. `Change-Id`, `Co-Authored-By`, `References`).

## Plans

- Confirm semantics of everything — ask, don't assume.
- End with unresolved questions, if any.

### When implementing

- Linters and tests must pass after each step.
- Never skip a failing test.

## Database / Production Access

- Never open a direct prod DB proxy or connection.
- Always use the internal `prod-sql-query` skill for production database lookups.

## Customer & Security Replies

- Before including facts from a subagent in customer or security replies, independently verify the claim against source code.

## Mergify — Testing Patterns (CI Insights)

- Use shared fixtures from `db_fixtures.py` (e.g. `_insert_span_job`, `_insert_runner_metrics`) via `pytest.mark.parametrize` instead of `db.add`.
- In `pytest.mark.parametrize`, use explicit keyword arguments: `argnames`, `argvalues`, `pytest.param(...)`, `indirect=[...]`.
- Use `indirect=["_insert_span_job", ...]` instead of `indirect=True`.
- Assert metrics as whole dicts (via `model_to_dict`) — use `anys` matchers only for truly non-deterministic fields.
