## General

- Be extremely concise — sacrifice grammar for concision.
- Avoid abbreviations in code — prefer full words (e.g. `documentation` over `doc`, `repository` over `repo`).
- Readability is correctness — unclear code is a bug, not a style issue.
- Never over-engineer — no speculative abstractions, no "just in case" code.
- Don't retroactively edit existing comments or code style unless asked.

## Comments And Documentation

- Do not leak implementation details.
- End all comments with a dot.
- Explain WHAT and WHY, not HOW.

## Git

- Use Conventional Commits starting with an uppercase (e.g. `feat(ci-insights): Add...`).
- Commit messages must complete "If applied, this commit will..." — use imperative verbs.
- When using stacks, each commit is a PR. Every commit must be independently deployable.
- Reduce coupling as much as possible by using independent branches when using stacks (`mergify stack`).
- Push stacks with `mergify stack push`.
- Add references to Linear issues at the end of the message (e.g. `Fixes: MRGFY-XXXX` or `References: `MRGFY-XXXX`) when relevant.

## Plans

- Confirm semantics of everything — ask, don't assume.
- End with unresolved questions, if any.

### When implementing

- Linters and tests must pass after each step.
- Never skip a failing test.

## Mergify — Testing Patterns (CI Insights)

- Use shared fixtures from `db_fixtures.py` (e.g. `_insert_span_job`, `_insert_runner_metrics`) via `pytest.mark.parametrize` instead of `db.add`.
- In `pytest.mark.parametrize`, use explicit keyword arguments: `argnames`, `argvalues`, `pytest.param(...)`, `indirect=[...]`.
- Use `indirect=["_insert_span_job", ...]` instead of `indirect=True`.
- Assert metrics as whole dicts (via `model_to_dict`) — use `anys` matchers only for truly non-deterministic fields.
