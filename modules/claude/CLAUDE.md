## General

- Be extremely concise — sacrifice grammar for concision.

## Comments And Documentation

- Do not leak implementation details.
- End all comments with a dot.
- Explain WHAT and WHY, not HOW.

## Git

- Reduce coupling as much as possible by using independant branches when using stacks (`mergify stack`).
- Try to add references to Linear issues at the end of the message (e.g. `Fixes: MRGFY-6467`).
- Use Conventional Commits starting with an uppercase (e.g. `feat(ci-insights): Add...`).

## Plans

- Confirm semantics of everything — ask, don't assume.
- End with unresolved questions, if any.

When implementing the plan:

- Linters and tests must pass after each step.
- Never skip a failing test.
- Each step should be a commit and be deployable.
